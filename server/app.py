#!/usr/bin/env python3
"""Server WIRA NUSA: TCP + protokol biner + loop tick.

    python3 server/app.py --host 0.0.0.0 --port 7777 --db data/wira.db

Satu thread untuk accept, satu thread per koneksi (MIDlet jumlahnya
sedikit dan paketnya kecil, jadi ini jauh lebih sederhana daripada
asyncio dan cukup untuk ratusan pemain). Loop tick jalan di thread
sendiri 10 Hz dan yang memegang semua mutasi dunia, dilindungi satu
kunci global supaya tidak ada balapan data.
"""

import argparse
import os
import re
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db as DB
import gamedata as G
import pasar as PASAR
import protocol as P
from world import Dunia, Pemain, sekarang

NAMA_RE = re.compile(r"^[A-Za-z0-9_]{3,14}$")
VERSI = "WiraNusa/1.0"


class Sesi(object):
    """Satu koneksi klien. Menyimpan status login dan buffer paket."""

    def __init__(self, srv, sock, alamat):
        self.srv = srv
        self.sock = sock
        self.alamat = alamat
        self.potong = P.Pemotong()
        self.akun_id = None
        self.pemain = None
        self.hidup = True
        self.terakhir = sekarang()

    def kirim(self, paket):
        if not self.hidup:
            return
        try:
            self.sock.sendall(paket)
        except OSError:
            self.tutup()

    def pesan(self, teks):
        self.kirim(P.Tulis(P.S_PESAN).teks(teks).paket())

    def tolak(self, teks):
        self.kirim(P.Tulis(P.S_TOLAK).teks(teks).paket())

    def tutup(self):
        if not self.hidup:
            return
        self.hidup = False
        try:
            self.sock.close()
        except OSError:
            pass


class Server(object):
    def __init__(self, path_db, seed=None):
        self.con, baru = DB.buka(path_db)
        self.kunci = threading.RLock()
        self.dunia = Dunia(seed=seed)
        self.sesi = {}          # eid -> Sesi
        self.jalan = True
        masalah = G.validasi()
        if masalah:
            raise SystemExit("data tidak konsisten:\n  " + "\n  ".join(masalah))
        self.dunia.guild_muat(DB.muat_guild_semua(self.con))
        PASAR.proses_kadaluarsa(self.con)
        PASAR.bersihkan_surat(self.con)
        if baru:
            print("database baru dibuat di", path_db)

    # ------------------------------------------------------- broadcast
    def sesi_pemain(self, pemain):
        return self.sesi.get(pemain.eid)

    def ke_peta(self, map_id, paket, kecuali=None):
        peta = self.dunia.peta.get(map_id)
        if not peta:
            return
        for p in list(peta.pemain.values()):
            if kecuali is not None and p.eid == kecuali:
                continue
            s = self.sesi.get(p.eid)
            if s:
                s.kirim(paket)

    def ke_pemain(self, pemain, paket):
        s = self.sesi.get(pemain.eid)
        if s:
            s.kirim(paket)

    # -------------------------------------------------- paket bantuan
    def paket_entitas_pemain(self, p):
        t = P.Tulis(P.S_ENTITAS_TAMBAH)
        t.b(0).i(p.eid).teks(p.nama).b(p.job).b(p.rambut).b(p.kulit)
        t.s(p.level).s(int(p.x)).s(int(p.y)).sb(p.arah)
        t.i(p.hp).i(p.hp_maks)
        senjata = p.eq.get(0)
        baju = p.eq.get(1)
        topi = p.eq.get(2)
        sayap = p.eq.get(3)
        t.us(senjata["id"] if senjata else 0).b(senjata.get("plus", 0) if senjata else 0)
        t.us(baju["id"] if baju else 0)
        t.us(topi["id"] if topi else 0)
        t.us(sayap["id"] if sayap else 0)
        return t.paket()

    def paket_entitas_mob(self, m):
        t = P.Tulis(P.S_ENTITAS_TAMBAH)
        t.b(1).i(m.eid).teks(m.info["nama"]).b(m.mob_id).b(0).b(0)
        t.s(m.info["lv"]).s(int(m.x)).s(int(m.y)).sb(m.arah)
        t.i(m.hp).i(m.hp_maks)
        t.us(0).b(0).us(0).us(0).us(0)
        return t.paket()

    def paket_drop(self, d):
        return (P.Tulis(P.S_DROP_TAMBAH).i(d.did).us(d.item_id)
                .us(d.jumlah).b(d.plus).s(int(d.x)).paket())

    def paket_status(self, p):
        t = P.Tulis(P.S_STATUS)
        t.i(p.hp).i(p.hp_maks).i(p.mp).i(p.mp_maks)
        t.s(p.level).i(p.exp).i(G.exp_untuk(p.level)).i(p.gold)
        t.s(p.atk).s(p.dfn).b(p.poin)
        t.b(len(p.skill))
        for sid, lv in p.skill.items():
            t.us(int(sid)).b(lv)
        return t.paket()

    def paket_inventori(self, p):
        t = P.Tulis(P.S_INVENTORI)
        t.b(len(p.inv))
        for slot, it in sorted(p.inv.items()):
            t.b(slot).us(it["id"]).us(it["jumlah"]).b(it.get("plus", 0))
        t.b(len(p.eq))
        for slot, it in sorted(p.eq.items()):
            t.b(slot).us(it["id"]).us(it["jumlah"]).b(it.get("plus", 0))
        return t.paket()

    def paket_quest(self, pemain, mode, daftar):
        """mode 0 = dialog NPC, 1 = jurnal quest yang sedang jalan."""
        t = P.Tulis(P.S_QUEST).b(mode).b(len(daftar))
        for qid, kode, progres, butuh in daftar:
            q = G.QUEST[qid]
            if kode == 0:
                teks = q["mulai"]
            elif kode == 1:
                teks = q["jalan"]
            elif kode == 2:
                teks = "Sudah lengkap. Lapor ke %s." % self.nama_npc(qid)
            elif kode == 3:
                teks = "Sudah selesai."
            else:
                teks = "Butuh level %d." % q["lv"] if pemain.level < q["lv"] \
                    else "Selesaikan dulu quest sebelumnya."
            t.us(qid).b(kode).us(progres).us(butuh)
            t.b(q["jenis"]).us(q["sasaran"])
            t.teks(q["nama"]).teks(teks)
        return t.paket()

    def nama_npc(self, qid):
        map_id, idx = G.QUEST[qid]["npc"]
        npc = G.MAP[map_id]["npc"]
        return npc[idx][1] if idx < len(npc) else "NPC"

    def kirim_quest_npc(self, sesi, pemain, npc_idx):
        daftar = self.dunia.quest_daftar_npc(pemain, pemain.map_id, npc_idx)
        sesi.kirim(self.paket_quest(pemain, 0, daftar))

    def kirim_quest_jurnal(self, sesi, pemain):
        daftar = []
        for qid in sorted(self.dunia.quest_aktif(pemain)):
            progres, butuh = self.dunia.quest_progres(pemain, qid)
            kode = 2 if progres >= butuh else 1
            daftar.append((qid, kode, progres, butuh))
        sesi.kirim(self.paket_quest(pemain, 1, daftar))

    # ------------------------------------------------------ paket trade
    def _isi_tawar(self, pemilik, t):
        keluar = []
        for slot, jumlah in t.tawar[pemilik.char_id]["item"]:
            it = pemilik.inv.get(slot)
            if it:
                keluar.append((it["id"], jumlah, it.get("plus", 0)))
        return keluar

    def paket_trade_update(self, kamu, t):
        lawan = t.lawan(kamu)
        w = P.Tulis(P.S_TRADE).b(2)
        for sisi in (kamu, lawan):
            isi = self._isi_tawar(sisi, t)
            w.i(t.tawar[sisi.char_id]["gold"]).b(len(isi))
            for item_id, jumlah, plus in isi:
                w.us(item_id).us(jumlah).b(plus)
        w.b(1 if t.kunci[kamu.char_id] else 0)
        w.b(1 if t.kunci[lawan.char_id] else 0)
        return w.paket()

    def kirim_trade_update(self, t):
        for sisi in (t.a, t.b):
            self.ke_pemain(sisi, self.paket_trade_update(sisi, t))

    def kirim_trade_mulai(self, t):
        for sisi in (t.a, t.b):
            lawan = t.lawan(sisi)
            self.ke_pemain(sisi, P.Tulis(P.S_TRADE).b(1).i(lawan.eid)
                           .teks(lawan.nama).paket())
        self.kirim_trade_update(t)

    # ------------------------------------------------------ paket guild
    def paket_guild(self, pemain):
        """mode 0 = info guild lengkap, mode 1 = kamu belum punya guild."""
        g = self.dunia.guild_dari(pemain)
        if not g:
            return P.Tulis(P.S_GUILD).b(1).paket()
        t = P.Tulis(P.S_GUILD).b(0)
        t.i(g["id"]).teks(g["nama"]).b(g["level"]).i(g["exp"])
        t.i(G.guild_exp_naik(g["level"])).i(g["kas"])
        t.b(self.dunia.guild_pangkat(pemain))
        t.us(g.get("menang", 0)).us(g.get("kalah", 0))
        t.b(G.guild_bonus(g["level"], "exp")).b(G.guild_bonus(g["level"], "gold"))
        anggota = sorted(g["anggota"].items(),
                         key=lambda kv: (-kv[1]["pangkat"], -kv[1]["sumbang"]))
        anggota = anggota[:40]
        t.b(len(anggota))
        for cid, a in anggota:
            online = self.dunia.pemain_by_char.get(cid)
            nama = online.nama if online else self.nama_char(cid)
            t.i(cid).teks(nama).b(a["pangkat"]).i(a["sumbang"])
            t.b(1 if online else 0).s(online.level if online else 0)
        return t.paket()

    def nama_char(self, char_id):
        r = self.con.execute("SELECT nama FROM karakter WHERE id = ?",
                             (char_id,)).fetchone()
        return r["nama"] if r else "?"

    def kirim_guild(self, pemain):
        self.ke_pemain(pemain, self.paket_guild(pemain))

    def siar_guild(self, g, paket=None):
        for anggota in self.dunia.guild_anggota_online(g):
            self.ke_pemain(anggota, paket or self.paket_guild(anggota))

    def pesan_guild(self, g, teks):
        paket = P.Tulis(P.S_PESAN).teks(teks).paket()
        for anggota in self.dunia.guild_anggota_online(g):
            self.ke_pemain(anggota, paket)

    def paket_war(self, w):
        sisa = max(0, (w["akhir"] - sekarang()) // 1000)
        return (P.Tulis(P.S_GUILD).b(3).i(w["id"])
                .teks(w["nama_a"]).teks(w["nama_b"])
                .i(w["skor"].get(w["a"], 0)).i(w["skor"].get(w["b"], 0))
                .i(int(sisa)).i(w["taruhan"]).paket())

    # ------------------------------------------------------- paket mail
    def paket_mail_daftar(self, char_id):
        surat = PASAR.daftar_surat(self.con, char_id)
        t = P.Tulis(P.S_MAIL).b(0).b(len(surat))
        for m in surat:
            t.i(m["id"]).teks(m["dari_nama"]).teks(m["judul"])
            t.b(1 if m["dibaca"] else 0).i(m["gold"]).b(len(m["lampiran"]))
            t.i(m["waktu"])
        return t.paket()

    def paket_mail_isi(self, m):
        t = P.Tulis(P.S_MAIL).b(1)
        t.i(m["id"]).teks(m["dari_nama"]).teks(m["judul"]).teks(m["isi"])
        t.i(m["gold"]).b(len(m["lampiran"]))
        for baris in m["lampiran"]:
            t.us(int(baris[0])).us(int(baris[1])).b(int(baris[2]))
        return t.paket()

    # ----------------------------------------------------- paket lelang
    def paket_lelang(self, mode, rows, halaman=0):
        skr = int(time.time())
        t = P.Tulis(P.S_LELANG).b(mode).b(halaman).b(len(rows))
        for row in rows:
            t.i(row["id"]).teks(row["penjual_nama"]).us(row["item_id"])
            t.us(row["jumlah"]).b(row["plus"]).i(row["harga"])
            t.i(max(0, row["kadaluarsa"] - skr))
        return t.paket()

    def kirim_masuk_map(self, sesi, pemain):
        peta = self.dunia.peta[pemain.map_id]
        info = peta.info
        t = P.Tulis(P.S_MASUK_MAP)
        t.b(pemain.map_id).teks(info["nama"]).teks(info["tema"]).teks(info["tile"])
        t.us(info["lebar"]).s(info["tanah"]).b(info["aman"])
        t.i(pemain.eid).s(int(pemain.x))
        t.b(len(info["portal"]))
        for x, tujuan, tx in info["portal"]:
            t.us(x).b(tujuan).us(tx)
        t.b(len(info["npc"]))
        for x, nama, jenis in info["npc"]:
            t.us(x).teks(nama).b(jenis)
        sesi.kirim(t.paket())
        sesi.kirim(self.paket_status(pemain))
        sesi.kirim(self.paket_inventori(pemain))
        for lain in peta.pemain.values():
            if lain.eid != pemain.eid:
                sesi.kirim(self.paket_entitas_pemain(lain))
        for mob in peta.mob.values():
            if mob.hidup:
                sesi.kirim(self.paket_entitas_mob(mob))
        for d in peta.drop.values():
            sesi.kirim(self.paket_drop(d))
        self.ke_peta(pemain.map_id, self.paket_entitas_pemain(pemain),
                     kecuali=pemain.eid)

    # ------------------------------------------------------- penanganan
    def tangani(self, sesi, opcode, r):
        if opcode == P.C_PING:
            sesi.kirim(P.Tulis(P.S_PONG).i(r.i() if r.sisa() >= 4 else 0).paket())
            return
        if opcode == P.C_DAFTAR:
            nama, sandi = r.teks(14), r.teks(32)
            if not NAMA_RE.match(nama):
                return sesi.tolak("nama akun 3-14 huruf/angka")
            if len(sandi) < 4:
                return sesi.tolak("sandi minimal 4 karakter")
            with self.kunci:
                aid = DB.buat_akun(self.con, nama, sandi)
            if aid is None:
                return sesi.tolak("nama akun sudah dipakai")
            return sesi.pesan("akun dibuat, silakan login")
        if opcode == P.C_LOGIN:
            nama, sandi = r.teks(14), r.teks(32)
            with self.kunci:
                aid, err = DB.cek_akun(self.con, nama, sandi)
            if err:
                return sesi.tolak(err)
            sesi.akun_id = aid
            sesi.kirim(P.Tulis(P.S_LOGIN_OK).teks(VERSI).paket())
            return self.kirim_daftar_char(sesi)
        if sesi.akun_id is None:
            return sesi.tolak("belum login")
        if opcode == P.C_BUAT_CHAR:
            return self.buat_char(sesi, r)
        if opcode == P.C_PILIH_CHAR:
            return self.pilih_char(sesi, r.i())
        if sesi.pemain is None:
            return sesi.tolak("belum pilih karakter")
        self.tangani_game(sesi, sesi.pemain, opcode, r)

    def kirim_daftar_char(self, sesi):
        with self.kunci:
            daftar = DB.daftar_karakter(self.con, sesi.akun_id)
        t = P.Tulis(P.S_DAFTAR_CHAR).b(len(daftar))
        for c in daftar:
            t.i(c["id"]).teks(c["nama"]).b(c["job"]).s(c["level"]) \
             .b(c["rambut"]).b(c["kulit"]).b(c["map_id"])
        sesi.kirim(t.paket())

    def buat_char(self, sesi, r):
        nama, job, rambut, kulit = r.teks(14), r.b(), r.b(), r.b()
        if not NAMA_RE.match(nama):
            return sesi.tolak("nama karakter 3-14 huruf/angka")
        if job not in G.JOB or rambut > 15 or kulit > 3:
            return sesi.tolak("pilihan karakter tidak valid")
        with self.kunci:
            if len(DB.daftar_karakter(self.con, sesi.akun_id)) >= 3:
                return sesi.tolak("maksimal 3 karakter per akun")
            st = G.statistik_dasar(job, 1)
            cid = DB.buat_karakter(self.con, sesi.akun_id, nama, job, rambut,
                                   kulit, st["hp_maks"], st["mp_maks"],
                                   G.GOLD_AWAL, G.MAP_AWAL, G.SPAWN_AWAL_X)
            if cid is None:
                return sesi.tolak("nama karakter sudah dipakai")
            # perlengkapan awal sesuai job
            senjata = {0: 200, 1: 210, 2: 220, 3: 230}[job]
            inv = {0: dict(id=senjata, jumlah=1, plus=0),
                   1: dict(id=300, jumlah=1, plus=0),
                   2: dict(id=100, jumlah=5, plus=0),
                   3: dict(id=101, jumlah=3, plus=0)}
            DB.simpan_item(self.con, cid, inv, {})
            DB.catat(self.con, "char_baru", cid, nama)
        self.kirim_daftar_char(sesi)

    def pilih_char(self, sesi, char_id):
        with self.kunci:
            data = DB.muat_karakter(self.con, char_id)
            if not data or data["akun_id"] != sesi.akun_id:
                return sesi.tolak("karakter bukan milik akun ini")
            if data["id"] in self.dunia.pemain_by_char:
                return sesi.tolak("karakter sedang online")
            import json
            data["skill"] = json.loads(data["skill"] or "{}")
            data["quest"] = DB.muat_quest(self.con, char_id)
            inv, eq = DB.muat_item(self.con, char_id)
            pemain = Pemain(self.dunia.eid_baru(), data, inv, eq)
            for gid, g in self.dunia.guild.items():
                if pemain.char_id in g["anggota"]:
                    pemain.guild = gid
                    break
            self.dunia.masuk(pemain)
            sesi.pemain = pemain
            self.sesi[pemain.eid] = sesi
        self.kirim_masuk_map(sesi, pemain)
        self.kirim_guild(pemain)
        n = DB.mail_hitung(self.con, pemain.char_id)
        if n:
            sesi.pesan("ada %d surat di kotak masuk (tombol 0 lalu Surat)" % n)

    # -------------------------------------------------- paket dalam game
    def tangani_game(self, sesi, pemain, opcode, r):
        with self.kunci:
            if opcode == P.C_GERAK:
                x, arah, state = r.s(), r.sb(), r.b()
                ok = self.dunia.gerak(pemain, x, arah, state)
                paket = (P.Tulis(P.S_ENTITAS_GERAK).i(pemain.eid)
                         .s(int(pemain.x)).sb(pemain.arah).b(state).paket())
                self.ke_peta(pemain.map_id, paket, kecuali=pemain.eid)
                if not ok:
                    sesi.kirim(paket)   # koreksi posisi ke client
                return
            if opcode == P.C_SERANG:
                skill_id, target = r.us(), r.i()
                self.dunia.terakhir_damage = []
                err = self.dunia.serang(pemain, skill_id, target)
                if err:
                    return sesi.pesan(err)
                self.ke_peta(pemain.map_id,
                             P.Tulis(P.S_ENTITAS_SERANG).i(pemain.eid)
                             .us(skill_id).i(target).paket())
                for eid, dmg, sisa in getattr(self.dunia, "terakhir_damage", []):
                    self.ke_peta(pemain.map_id,
                                 P.Tulis(P.S_DAMAGE).i(eid).i(dmg).i(sisa)
                                 .i(pemain.eid).paket())
                    if sisa <= 0:
                        self.ke_peta(pemain.map_id,
                                     P.Tulis(P.S_MATI).i(eid).paket())
                peta = self.dunia.peta[pemain.map_id]
                for d in peta.drop.values():
                    if sekarang() - d.waktu < 200:
                        self.ke_peta(pemain.map_id, self.paket_drop(d))
                sesi.kirim(self.paket_status(pemain))
                return
            if opcode == P.C_AMBIL:
                did = r.i()
                err = self.dunia.ambil_drop(pemain, did)
                if err:
                    return sesi.pesan(err)
                self.ke_peta(pemain.map_id,
                             P.Tulis(P.S_DROP_HAPUS).i(did).paket())
                return sesi.kirim(self.paket_inventori(pemain))
            if opcode == P.C_CHAT:
                kanal, teks = r.b(), r.teks(120)
                teks = teks.strip()
                if not teks:
                    return
                if teks[0] == "/":
                    return self.perintah_chat(sesi, pemain, teks[1:])
                paket = (P.Tulis(P.S_CHAT).b(kanal).teks(pemain.nama)
                         .teks(teks).paket())
                if kanal == 0:
                    self.ke_peta(pemain.map_id, paket)
                elif kanal == 1 and pemain.party:
                    for cid in self.dunia.party[pemain.party]["anggota"]:
                        rekan = self.dunia.pemain_by_char.get(cid)
                        if rekan:
                            self.ke_pemain(rekan, paket)
                else:
                    for p in list(self.dunia.pemain_by_char.values()):
                        self.ke_pemain(p, paket)
                return
            if opcode == P.C_QUEST:
                aksi = r.b()
                if aksi == 0:
                    npc_idx = r.b()
                    info = self.dunia.peta[pemain.map_id].info
                    if npc_idx >= len(info["npc"]):
                        return sesi.pesan("tidak ada NPC di situ")
                    if abs(pemain.x - info["npc"][npc_idx][0]) > 90:
                        return sesi.pesan("dekati NPC-nya dulu")
                    return self.kirim_quest_npc(sesi, pemain, npc_idx)
                if aksi == 4:
                    return self.kirim_quest_jurnal(sesi, pemain)
                qid = r.us()
                if qid not in G.QUEST:
                    return sesi.pesan("quest tidak dikenal")
                npc_idx = G.QUEST[qid]["npc"][1]
                if aksi == 1:
                    err = self.dunia.quest_ambil(pemain, qid)
                    if err:
                        return sesi.pesan(err)
                    sesi.pesan("quest diambil: %s" % G.QUEST[qid]["nama"])
                elif aksi == 2:
                    err, hasil = self.dunia.quest_serah(pemain, qid)
                    if err:
                        return sesi.pesan(err)
                    sesi.pesan(hasil["teks"])
                    upah = []
                    if hasil["exp"]:
                        upah.append("%d exp" % hasil["exp"])
                    if hasil["gold"]:
                        upah.append("%d gold" % hasil["gold"])
                    for item_id, jumlah in hasil["item"]:
                        upah.append("%s x%d" % (G.ITEM[item_id]["nama"], jumlah))
                    if upah:
                        sesi.pesan("hadiah: " + ", ".join(upah))
                    if hasil["naik"]:
                        self.ke_peta(pemain.map_id, P.Tulis(P.S_NAIK_LEVEL)
                                     .i(pemain.eid).s(pemain.level).paket())
                    DB.catat(self.con, "quest", pemain.char_id, str(qid))
                    sesi.kirim(self.paket_inventori(pemain))
                elif aksi == 3:
                    err = self.dunia.quest_batal(pemain, qid)
                    if err:
                        return sesi.pesan(err)
                    sesi.pesan("quest dibatalkan")
                else:
                    return sesi.pesan("aksi quest tidak dikenal")
                sesi.kirim(self.paket_status(pemain))
                if self.dunia._dekat_npc(pemain, qid):
                    self.kirim_quest_npc(sesi, pemain, npc_idx)
                return
            if opcode == P.C_TRADE:
                return self.tangani_trade(sesi, pemain, r)
            if opcode == P.C_GUILD:
                return self.tangani_guild(sesi, pemain, r)
            if opcode == P.C_MAIL:
                return self.tangani_mail(sesi, pemain, r)
            if opcode == P.C_LELANG:
                return self.tangani_lelang(sesi, pemain, r)
            if opcode == P.C_PAKAI_ITEM:
                err = self.dunia.pakai_item(pemain, r.b())
            elif opcode == P.C_PAKAI_EQUIP:
                err = self.dunia.pakai_equip(pemain, r.b())
            elif opcode == P.C_LEPAS_EQUIP:
                err = self.dunia.lepas_equip(pemain, r.b())
            elif opcode == P.C_NAIK_SKILL:
                err = self.dunia.naik_skill(pemain, r.us())
            elif opcode == P.C_UPGRADE:
                err, plus = self.dunia.upgrade(pemain, r.b())
            elif opcode == P.C_TOKO:
                aksi = r.b()
                if aksi == 0:
                    t = P.Tulis(P.S_TOKO_ISI).b(len(G.TOKO))
                    for iid in G.TOKO:
                        t.us(iid).i(G.ITEM[iid]["harga"])
                    sesi.kirim(t.paket())
                    return
                if not self.dunia.peta[pemain.map_id].info["aman"]:
                    return sesi.pesan("toko hanya ada di desa")
                if aksi == 1:
                    err = self.dunia.beli(pemain, r.us(), r.us())
                else:
                    err = self.dunia.jual(pemain, r.b(), r.us())
            elif opcode == P.C_PINDAH_MAP:
                idx = r.b()
                info = self.dunia.peta[pemain.map_id].info
                if idx >= len(info["portal"]):
                    return sesi.pesan("portal tidak ada")
                px, tujuan, tx = info["portal"][idx]
                if abs(pemain.x - px) > 60:
                    return sesi.pesan("kamu jauh dari portal")
                lama = pemain.map_id
                self.dunia.pindah_map(pemain, tujuan, tx)
                self.ke_peta(lama, P.Tulis(P.S_ENTITAS_HAPUS)
                             .i(pemain.eid).paket())
                self.kirim_masuk_map(sesi, pemain)
                return
            elif opcode == P.C_PARTY:
                aksi = r.b()
                if aksi == 0:
                    err = self.dunia.party_buat(pemain)
                elif aksi == 1:
                    err = self.dunia.party_masuk(pemain, r.i())
                else:
                    err = self.dunia.party_keluar(pemain)
                if not err:
                    self.siar_party(pemain)
            else:
                err = "opcode %d tidak dikenal" % opcode
            if err:
                return sesi.pesan(err)
            sesi.kirim(self.paket_status(pemain))
            sesi.kirim(self.paket_inventori(pemain))
            self.ke_peta(pemain.map_id, self.paket_entitas_pemain(pemain))

    def tangani_trade(self, sesi, pemain, r):
        aksi = r.b()
        if aksi == 0:
            err, t = self.dunia.trade_ajak(pemain, r.i())
            if err:
                return sesi.pesan(err)
            self.ke_pemain(t.b, P.Tulis(P.S_TRADE).b(0).i(pemain.eid)
                           .teks(pemain.nama).paket())
            return sesi.pesan("ajakan dagang dikirim ke %s" % t.b.nama)
        if aksi == 1:
            err, t = self.dunia.trade_terima(pemain)
            if err:
                return sesi.pesan(err)
            return self.kirim_trade_mulai(t)
        if aksi == 2:
            a, b, alasan = self.dunia.trade_batal(pemain, "dibatalkan %s" % pemain.nama)
            if a is None:
                return sesi.pesan("tidak sedang berdagang")
            paket = P.Tulis(P.S_TRADE).b(4).teks(alasan).paket()
            self.ke_pemain(a, paket)
            self.ke_pemain(b, paket)
            return
        if aksi == 3:
            gold = r.i()
            n = r.b()
            if n > G.TRADE_SLOT_MAKS:
                return sesi.pesan("terlalu banyak barang")
            daftar = []
            for _ in range(n):
                daftar.append((r.b(), r.us()))
            err, t = self.dunia.trade_tawar(pemain, gold, daftar)
            if err:
                return sesi.pesan(err)
            return self.kirim_trade_update(t)
        if aksi == 4:
            err, t, selesai = self.dunia.trade_kunci(pemain)
            if err:
                if t:
                    self.kirim_trade_update(t)
                return sesi.pesan(err)
            if not selesai:
                return self.kirim_trade_update(t)
            paket = P.Tulis(P.S_TRADE).b(3).paket()
            for sisi in (t.a, t.b):
                self.ke_pemain(sisi, paket)
                self.ke_pemain(sisi, self.paket_inventori(sisi))
                self.ke_pemain(sisi, self.paket_status(sisi))
                self.ke_peta(sisi.map_id, self.paket_entitas_pemain(sisi))
                DB.simpan_karakter(self.con, sisi.sebagai_baris())
                DB.simpan_item(self.con, sisi.char_id, sisi.inv, sisi.eq)
            DB.catat(self.con, "trade", t.a.char_id,
                     "%s <-> %s" % (t.a.nama, t.b.nama))
            return
        return sesi.pesan("aksi dagang tidak dikenal")

    # ------------------------------------------------------------ guild
    def tangani_guild(self, sesi, pemain, r):
        D = self.dunia
        aksi = r.b()
        if aksi == 7:
            return self.kirim_guild(pemain)
        if aksi == 0:
            err, g = D.guild_buat(pemain, r.teks(G.GUILD_NAMA_MAKS))
            if err:
                return sesi.pesan(err)
            DB.simpan_guild(self.con, g)
            DB.catat(self.con, "guild_buat", pemain.char_id, g["nama"])
            sesi.pesan("guild %s berdiri" % g["nama"])
            sesi.kirim(self.paket_status(pemain))
            return self.kirim_guild(pemain)
        if aksi == 1:
            eid = r.i()
            target = None
            for p in self.dunia.peta[pemain.map_id].pemain.values():
                if p.eid == eid:
                    target = p
                    break
            if target is None:
                return sesi.pesan("pemainnya tidak ada di peta ini")
            err = D.guild_undang(pemain, target)
            if err:
                return sesi.pesan(err)
            g = D.guild_dari(pemain)
            self.ke_pemain(target, P.Tulis(P.S_GUILD).b(2).i(g["id"])
                           .teks(g["nama"]).teks(pemain.nama).paket())
            return sesi.pesan("undangan dikirim ke %s" % target.nama)
        if aksi == 2:
            err, g = D.guild_terima(pemain, r.i())
            if err:
                return sesi.pesan(err)
            DB.simpan_guild(self.con, g)
            self.pesan_guild(g, "%s bergabung ke guild" % pemain.nama)
            return self.siar_guild(g)
        if aksi == 3:
            g = D.guild_dari(pemain)
            err = D.guild_keluar(pemain)
            if err:
                return sesi.pesan(err)
            self.simpan_guild_kotor()
            sesi.pesan("kamu keluar dari guild")
            self.kirim_guild(pemain)
            if g and g["anggota"]:
                self.pesan_guild(g, "%s keluar dari guild" % pemain.nama)
                self.siar_guild(g)
            return
        if aksi == 4:
            cid = r.i()
            korban = D.pemain_by_char.get(cid)
            g = D.guild_dari(pemain)
            err = D.guild_pecat(pemain, cid)
            if err:
                return sesi.pesan(err)
            self.simpan_guild_kotor()
            if korban:
                self.ke_pemain(korban, P.Tulis(P.S_PESAN)
                               .teks("kamu dikeluarkan dari guild").paket())
                self.kirim_guild(korban)
            self.siar_guild(g)
            return sesi.pesan("anggota dikeluarkan")
        if aksi == 5:
            cid, pangkat = r.i(), r.b()
            g = D.guild_dari(pemain)
            err = D.guild_set_pangkat(pemain, cid, pangkat)
            if err:
                return sesi.pesan(err)
            self.simpan_guild_kotor()
            self.pesan_guild(g, "pangkat %s diubah jadi %s"
                             % (self.nama_char(cid), G.NAMA_PANGKAT[pangkat]))
            return self.siar_guild(g)
        if aksi == 6:
            err, naik = D.guild_sumbang(pemain, r.i())
            if err:
                return sesi.pesan(err)
            g = D.guild_dari(pemain)
            self.simpan_guild_kotor()
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            if naik:
                self.pesan_guild(g, "guild naik ke level %d!" % g["level"])
            sesi.kirim(self.paket_status(pemain))
            return self.siar_guild(g)
        if aksi == 8:
            g = D.guild_dari(pemain)
            anggota = D.guild_anggota_online(g) if g else []
            gid = g["id"] if g else 0
            nama = g["nama"] if g else ""
            err = D.guild_bubar(pemain)
            if err:
                return sesi.pesan(err)
            self.simpan_guild_kotor()
            for a in anggota:
                self.ke_pemain(a, P.Tulis(P.S_PESAN)
                               .teks("guild %s dibubarkan" % nama).paket())
                self.kirim_guild(a)
            DB.catat(self.con, "guild_bubar", pemain.char_id, str(gid))
            return
        if aksi == 9:
            nama_lawan, taruhan = r.teks(G.GUILD_NAMA_MAKS), r.i()
            err, ajakan = D.war_deklarasi(pemain, nama_lawan, taruhan)
            if err:
                return sesi.pesan(err)
            lawan = D.guild.get(D.guild_by_nama.get(nama_lawan.strip().lower()))
            g = D.guild_dari(pemain)
            if lawan:
                paket = (P.Tulis(P.S_GUILD).b(4).teks(g["nama"])
                         .i(taruhan).paket())
                for a in D.guild_anggota_online(lawan):
                    self.ke_pemain(a, paket)
            return sesi.pesan("tantangan perang dikirim")
        if aksi == 10:
            err, w = D.war_terima(pemain)
            if err:
                return sesi.pesan(err)
            self.simpan_guild_kotor()
            paket = self.paket_war(w)
            for gid in (w["a"], w["b"]):
                g = D.guild.get(gid)
                if g:
                    self.pesan_guild(g, "perang dimulai: %s vs %s"
                                     % (w["nama_a"], w["nama_b"]))
                    for a in D.guild_anggota_online(g):
                        self.ke_pemain(a, paket)
            DB.catat(self.con, "war_mulai", pemain.char_id,
                     "%s vs %s taruhan=%d" % (w["nama_a"], w["nama_b"],
                                              w["taruhan"]))
            return
        if aksi == 11:
            err = D.war_tolak(pemain)
            return sesi.pesan(err or "tantangan ditolak")
        if aksi == 12:
            g = D.guild_dari(pemain)
            w = D.war_aktif(g["id"]) if g else None
            if not w:
                return sesi.pesan("guild kamu tidak sedang perang")
            return sesi.kirim(self.paket_war(w))
        return sesi.pesan("aksi guild tidak dikenal")

    def perintah_chat(self, sesi, pemain, baris):
        """Perintah teks: /guild, /war, /lapak, /surat.

        Dipakai klien MIDlet karena keypad tidak cukup untuk semua aksi.
        """
        D = self.dunia
        bagian = baris.split()
        if not bagian:
            return sesi.pesan("perintah kosong")
        cmd = bagian[0].lower()
        arg = bagian[1:]
        if cmd == "guild":
            if not arg:
                return sesi.pesan("pakai: /guild NamaGuild")
            err, g = D.guild_buat(pemain, " ".join(arg))
            if err:
                return sesi.pesan(err)
            DB.simpan_guild(self.con, g)
            DB.catat(self.con, "guild_buat", pemain.char_id, g["nama"])
            sesi.pesan("guild %s berdiri" % g["nama"])
            sesi.kirim(self.paket_status(pemain))
            return self.kirim_guild(pemain)
        if cmd == "war":
            if len(arg) < 2:
                return sesi.pesan("pakai: /war NamaGuild taruhan")
            try:
                taruhan = int(arg[-1])
            except ValueError:
                return sesi.pesan("taruhan harus angka")
            nama_lawan = " ".join(arg[:-1])
            err, ajakan = D.war_deklarasi(pemain, nama_lawan, taruhan)
            if err:
                return sesi.pesan(err)
            lawan = D.guild.get(D.guild_by_nama.get(nama_lawan.strip().lower()))
            g = D.guild_dari(pemain)
            if lawan:
                paket = (P.Tulis(P.S_GUILD).b(4).teks(g["nama"])
                         .i(taruhan).paket())
                for a in D.guild_anggota_online(lawan):
                    self.ke_pemain(a, paket)
            return sesi.pesan("tantangan perang dikirim")
        if cmd == "lapak":
            if len(arg) < 2:
                return sesi.pesan("pakai: /lapak slot harga [jumlah]")
            try:
                slot = int(arg[0])
                harga = int(arg[1])
                jumlah = int(arg[2]) if len(arg) > 2 else 1
            except ValueError:
                return sesi.pesan("slot, harga, jumlah harus angka")
            err, _lid = PASAR.pasang_lelang(self.con, pemain, slot, jumlah,
                                            harga)
            if err:
                return sesi.pesan(err)
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            sesi.kirim(self.paket_inventori(pemain))
            sesi.pesan("lapak dipasang seharga %d gold" % harga)
            return sesi.kirim(self.paket_lelang(
                1, PASAR.lelang_saya(self.con, pemain.char_id)))
        if cmd == "surat":
            if len(arg) < 3:
                return sesi.pesan("pakai: /surat NamaTujuan judul isi...")
            err, _mid = PASAR.kirim_surat(self.con, pemain, arg[0], arg[1],
                                          " ".join(arg[2:]))
            if err:
                return sesi.pesan(err)
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            sesi.kirim(self.paket_status(pemain))
            return sesi.pesan("surat terkirim ke %s" % arg[0])
        return sesi.pesan("perintah tidak dikenal: /%s" % cmd)

    def simpan_guild_kotor(self):
        for gid in list(self.dunia.guild_kotor):
            g = self.dunia.guild.get(gid)
            if g:
                DB.simpan_guild(self.con, g)
        self.dunia.guild_kotor.clear()
        for gid in list(self.dunia.guild_dihapus):
            DB.hapus_guild(self.con, gid)
        self.dunia.guild_dihapus.clear()

    # ------------------------------------------------------------- mail
    def tangani_mail(self, sesi, pemain, r):
        aksi = r.b()
        if aksi == 0:
            return sesi.kirim(self.paket_mail_daftar(pemain.char_id))
        if aksi == 1:
            err, m = PASAR.baca_surat(self.con, pemain.char_id, r.i())
            if err:
                return sesi.pesan(err)
            return sesi.kirim(self.paket_mail_isi(m))
        if aksi == 2:
            err, hasil = PASAR.ambil_lampiran(self.con, pemain, r.i())
            if err and hasil is None:
                return sesi.pesan(err)
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            sesi.kirim(self.paket_inventori(pemain))
            sesi.kirim(self.paket_status(pemain))
            sesi.kirim(self.paket_mail_daftar(pemain.char_id))
            return sesi.pesan(err or "lampiran diambil")
        if aksi == 3:
            err = PASAR.hapus_surat(self.con, pemain.char_id, r.i())
            if err:
                return sesi.pesan(err)
            return sesi.kirim(self.paket_mail_daftar(pemain.char_id))
        if aksi == 4:
            ke = r.teks(14)
            judul = r.teks(G.MAIL_JUDUL_MAKS)
            isi = r.teks(G.MAIL_ISI_MAKS)
            gold = r.i()
            n = r.b()
            if n > G.MAIL_LAMPIRAN_MAKS:
                return sesi.pesan("lampiran terlalu banyak")
            lampiran = []
            for _ in range(n):
                lampiran.append((r.b(), r.us()))
            err, mid = PASAR.kirim_surat(self.con, pemain, ke, judul, isi,
                                         gold, lampiran)
            if err:
                return sesi.pesan(err)
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            sesi.kirim(self.paket_inventori(pemain))
            sesi.kirim(self.paket_status(pemain))
            ke_id, _ = PASAR.cari_char(self.con, ke)
            penerima = self.dunia.pemain_by_char.get(ke_id)
            if penerima:
                self.ke_pemain(penerima, P.Tulis(P.S_PESAN)
                               .teks("surat baru dari %s" % pemain.nama).paket())
            return sesi.pesan("surat terkirim")
        return sesi.pesan("aksi surat tidak dikenal")

    # ----------------------------------------------------------- lelang
    def tangani_lelang(self, sesi, pemain, r):
        aksi = r.b()
        if aksi == 0:
            item_id, halaman = r.us(), r.b()
            rows = PASAR.daftar_lelang(self.con, item_id or None, halaman)
            return sesi.kirim(self.paket_lelang(0, rows, halaman))
        if aksi == 1:
            return sesi.kirim(self.paket_lelang(1,
                              PASAR.lelang_saya(self.con, pemain.char_id)))
        if aksi == 2:
            slot, jumlah, harga = r.b(), r.us(), r.i()
            err, lid = PASAR.pasang_lelang(self.con, pemain, slot, jumlah, harga)
            if err:
                return sesi.pesan(err)
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            sesi.kirim(self.paket_inventori(pemain))
            sesi.pesan("lapak dipasang (id %d)" % lid)
            return sesi.kirim(self.paket_lelang(1,
                              PASAR.lelang_saya(self.con, pemain.char_id)))
        if aksi == 3:
            err, hasil = PASAR.beli_lelang(self.con, pemain, r.i())
            if err:
                return sesi.pesan(err)
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            sesi.kirim(self.paket_inventori(pemain))
            sesi.kirim(self.paket_status(pemain))
            penjual_id, _ = None, None
            sesi.pesan("%s x%d dibeli seharga %d gold"
                       % (G.ITEM[hasil["item_id"]]["nama"], hasil["jumlah"],
                          hasil["harga"]))
            return sesi.kirim(self.paket_lelang(0,
                              PASAR.daftar_lelang(self.con, None, 0), 0))
        if aksi == 4:
            err = PASAR.tarik_lelang(self.con, pemain, r.i())
            if err:
                return sesi.pesan(err)
            sesi.pesan("lapak ditarik, barang dikirim lewat surat")
            return sesi.kirim(self.paket_lelang(1,
                              PASAR.lelang_saya(self.con, pemain.char_id)))
        return sesi.pesan("aksi lelang tidak dikenal")

    def siar_party(self, pemain):
        p = self.dunia.party.get(pemain.party)
        anggota = p["anggota"] if p else []
        t = P.Tulis(P.S_PARTY).i(pemain.party or 0).b(len(anggota))
        for cid in anggota:
            rekan = self.dunia.pemain_by_char.get(cid)
            t.i(cid).teks(rekan.nama if rekan else "?")
            t.i(rekan.hp if rekan else 0).i(rekan.hp_maks if rekan else 1)
        paket = t.paket()
        for cid in anggota or [pemain.char_id]:
            rekan = self.dunia.pemain_by_char.get(cid)
            if rekan:
                self.ke_pemain(rekan, paket)

    # ------------------------------------------------------------ loop
    def loop_tick(self):
        berikut = time.time()
        simpan_pada = time.time() + 30
        while self.jalan:
            berikut += G.TICK_MS / 1000.0
            with self.kunci:
                for ev in self.dunia.tick():
                    self.siarkan_peristiwa(ev)
                if time.time() >= simpan_pada:
                    simpan_pada = time.time() + 30
                    self.simpan_semua()
            tidur = berikut - time.time()
            if tidur > 0:
                time.sleep(tidur)
            else:
                berikut = time.time()

    def siarkan_peristiwa(self, ev):
        jenis = ev[0]
        if jenis == "mob_spawn":
            self.ke_peta(ev[1], self.paket_entitas_mob(ev[2]))
        elif jenis == "mob_gerak":
            m = ev[2]
            self.ke_peta(ev[1], P.Tulis(P.S_ENTITAS_GERAK).i(m.eid)
                         .s(int(m.x)).sb(m.arah).b(1).paket())
        elif jenis == "mob_serang":
            _, map_id, mob, target, dmg = ev
            self.ke_peta(map_id, P.Tulis(P.S_ENTITAS_SERANG).i(mob.eid)
                         .us(0).i(target.eid).paket())
            self.ke_peta(map_id, P.Tulis(P.S_DAMAGE).i(target.eid).i(dmg)
                         .i(max(0, target.hp)).i(mob.eid).paket())
            self.ke_pemain(target, self.paket_status(target))
        elif jenis == "pemain_mati":
            _, map_id, target, hilang = ev
            self.ke_peta(map_id, P.Tulis(P.S_MATI).i(target.eid).paket())
            self.ke_pemain(target, P.Tulis(P.S_PESAN)
                           .teks("kamu tumbang, gold hilang %d" % hilang).paket())
        elif jenis == "hidup_lagi":
            _, map_id, pemain = ev
            s = self.sesi.get(pemain.eid)
            if s:
                self.kirim_masuk_map(s, pemain)
        elif jenis == "drop_hapus":
            self.ke_peta(ev[1], P.Tulis(P.S_DROP_HAPUS).i(ev[2]).paket())
        elif jenis == "war_selesai":
            hasil = ev[2]
            paket = (P.Tulis(P.S_GUILD).b(5)
                     .teks(hasil["menang"] or "seri")
                     .i(hasil["skor_a"]).i(hasil["skor_b"])
                     .i(hasil["hadiah_kas"]).b(1 if hasil["seri"] else 0)
                     .paket())
            for gid in (hasil["menang_id"], hasil["kalah_id"]):
                g = self.dunia.guild.get(gid)
                if not g:
                    continue
                for a in self.dunia.guild_anggota_online(g):
                    self.ke_pemain(a, paket)
                    self.ke_pemain(a, self.paket_guild(a))
            self.simpan_guild_kotor()
            DB.catat(self.con, "war_selesai", None,
                     "%s %d-%d" % (hasil["menang"] or "seri",
                                   hasil["skor_a"], hasil["skor_b"]))

    def simpan_semua(self):
        for pemain in list(self.dunia.pemain_by_char.values()):
            DB.simpan_karakter(self.con, pemain.sebagai_baris())
            DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
            DB.simpan_quest(self.con, pemain.char_id, pemain.quest)
        self.simpan_guild_kotor()
        PASAR.proses_kadaluarsa(self.con)

    def layani(self, sesi):
        sesi.sock.settimeout(120)
        try:
            while sesi.hidup and self.jalan:
                data = sesi.sock.recv(4096)
                if not data:
                    break
                for opcode, r in sesi.potong.masuk(data):
                    try:
                        self.tangani(sesi, opcode, r)
                    except P.ProtokolError as e:
                        sesi.tolak("paket rusak: %s" % e)
                        raise
        except (OSError, P.ProtokolError):
            pass
        finally:
            self.putus(sesi)

    def putus(self, sesi):
        with self.kunci:
            pemain = sesi.pemain
            if pemain:
                DB.simpan_karakter(self.con, pemain.sebagai_baris())
                DB.simpan_item(self.con, pemain.char_id, pemain.inv, pemain.eq)
                DB.simpan_quest(self.con, pemain.char_id, pemain.quest)
                if pemain.trade:
                    a, b, alasan = self.dunia.trade_batal(pemain, "lawan keluar")
                    lain = b if a is pemain else a
                    if lain is not None and lain is not pemain:
                        self.ke_pemain(lain, P.Tulis(P.S_TRADE).b(4)
                                       .teks(alasan).paket())
                map_id = pemain.map_id
                self.dunia.keluar(pemain)
                self.sesi.pop(pemain.eid, None)
                self.ke_peta(map_id, P.Tulis(P.S_ENTITAS_HAPUS)
                             .i(pemain.eid).paket())
            sesi.tutup()

    def jalankan(self, host, port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(64)
        threading.Thread(target=self.loop_tick, daemon=True).start()
        print("%s siap di %s:%d" % (VERSI, host, port))
        print("map: %s" % ", ".join(m["nama"] for m in G.MAP.values()))
        try:
            while self.jalan:
                sock, alamat = srv.accept()
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sesi = Sesi(self, sock, alamat)
                threading.Thread(target=self.layani, args=(sesi,),
                                 daemon=True).start()
        except KeyboardInterrupt:
            print("\nmenutup, menyimpan karakter...")
        finally:
            self.jalan = False
            with self.kunci:
                self.simpan_semua()
            srv.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("WIRA_HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("WIRA_PORT", "7777")))
    ap.add_argument("--db", default=os.environ.get("WIRA_DB", "data/wira.db"))
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    Server(args.db, seed=args.seed).jalankan(args.host, args.port)


if __name__ == "__main__":
    main()
