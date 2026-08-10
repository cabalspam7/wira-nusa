"""Uji mandiri WIRA NUSA v1.2 (tanpa pustaka luar).

Jalankan: python3 selftest.py
Keluar dengan kode 0 bila semua uji lulus dan mencetak WIRA_TEST_OK.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db as DB
import gamedata as G
import protocol as P
from world import Dunia, Pemain

LULUS = 0
GAGAL = 0
_GAGAL_PESAN = []


def bagian(judul):
    print("")
    print(judul)


def cek(syarat, keterangan):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print("  ok   :", keterangan)
    else:
        GAGAL += 1
        _GAGAL_PESAN.append(keterangan)
        print("  GAGAL:", keterangan)


def _pemain_uji(con, ds, akun, nama, job=0, level=5, gold=5000):
    dasar = G.statistik_dasar(job, level)
    cid = DB.buat_karakter(con, akun, nama, job, 0, 0, dasar["hp_maks"],
                           dasar["mp_maks"], gold, G.MAP_AWAL, G.SPAWN_AWAL_X)
    data = DB.muat_karakter(con, cid)
    data["skill"] = json.loads(data["skill"] or "{}")
    data["quest"] = DB.muat_quest(con, cid)
    data["level"] = level
    p = Pemain(ds.eid_baru(), data, {}, {})
    ds.masuk(p)
    return p


def uji_gamedata():
    bagian("== 1. data permainan")
    masalah = G.validasi()
    cek(not masalah, "tabel data konsisten" + (": " + "; ".join(masalah)
                                               if masalah else ""))
    cek(len(G.JOB) == 4, "empat job tersedia")
    for jid, j in G.JOB.items():
        cek(j["hp"] > 0 and j["atk"] > 0, "job %d punya statistik dasar" % jid)
    cek(len(G.MAP) >= 4, "minimal empat peta")
    cek(G.MAP_AWAL in G.MAP, "peta awal ada di tabel")
    cek(G.MAP[G.MAP_AWAL]["aman"] == 1, "peta awal adalah zona aman")

    for job in G.JOB:
        a = G.statistik_dasar(job, 1)
        b = G.statistik_dasar(job, 10)
        cek(b["hp_maks"] > a["hp_maks"] and b["atk"] >= a["atk"],
            "statistik job %d naik ikut level" % job)
    naik = [G.exp_untuk(l) for l in range(1, 20)]
    cek(all(naik[i] < naik[i + 1] for i in range(len(naik) - 1)),
        "kebutuhan exp selalu naik")
    cek(G.exp_untuk(G.LEVEL_MAKS - 1) > G.exp_untuk(1) * 10,
        "kurva exp cukup panjang sampai level maks")
    cek(G.exp_untuk(G.LEVEL_MAKS) == 0, "level maks tidak butuh exp lagi")

    cek(len(G.UPGRADE_PELUANG) == G.UPGRADE_MAKS, "tabel peluang tempa lengkap")
    cek(len(G.UPGRADE_BATU) == G.UPGRADE_MAKS, "tabel biaya batu tempa lengkap")
    cek(all(G.UPGRADE_PELUANG[i] >= G.UPGRADE_PELUANG[i + 1]
            for i in range(G.UPGRADE_MAKS - 1)),
        "peluang tempa makin kecil di plus tinggi")
    cek(G.stat_upgrade(100, 0) == 100, "tanpa tempa statistik tetap")
    cek(G.stat_upgrade(100, 5) > G.stat_upgrade(100, 1), "tempa menambah statistik")

    for it_id, it in G.ITEM.items():
        cek(it.get("nama") and it.get("tumpuk", 1) >= 1,
            "item %d punya nama dan aturan tumpuk" % it_id)
    for mid, m in G.MOB.items():
        cek(m["hp"] > 0 and m["exp"] > 0, "mob %d punya hp dan exp" % mid)
    for sid, s in G.SKILL.items():
        cek(s["mp"] >= 0 and s["cd"] > 0 and s["job"] in G.JOB,
            "skill %d wajar" % sid)
    for tid in G.TOKO:
        cek(tid in G.ITEM, "barang toko %d ada di tabel item" % tid)


def uji_quest_data():
    bagian("== 2. rantai quest")
    cek(len(G.QUEST) >= 5, "minimal lima quest")
    for qid, q in G.QUEST.items():
        cek(q["npc"][0] in G.MAP, "quest %d menempel di peta yang ada" % qid)
        cek(q["lv"] >= 1 and q["exp"] > 0, "quest %d punya syarat dan hadiah" % qid)
        if q["jenis"] == 0:
            cek(q["sasaran"] in G.MOB, "quest buru %d menyasar mob nyata" % qid)
        elif q["jenis"] == 1:
            cek(q["sasaran"] in G.ITEM, "quest kumpul %d menyasar item nyata" % qid)
        for item_id, jml in q.get("item", []):
            cek(item_id in G.ITEM and jml > 0,
                "hadiah item quest %d valid" % qid)
        if q.get("berikut"):
            cek(q["berikut"] in G.QUEST, "lanjutan quest %d ada" % qid)

    map_id, npc_idx = G.QUEST[1]["npc"]
    cek(1 in G.quest_npc(map_id, npc_idx), "quest pertama muncul di npc-nya")
    hadiah = G.hadiah_item(1, 0)
    cek(isinstance(hadiah, list), "hadiah item quest bisa dihitung per job")
    cek(G.Q_AKTIF != G.Q_SIAP != G.Q_SELESAI, "kode status quest berbeda")


def uji_protokol():
    bagian("== 3. protokol biner")
    paket = (P.Tulis(P.S_STATUS).b(200).sb(-5).s(-1234).us(60000)
             .i(1234567).teks("Pendekar").paket())
    potong = P.Pemotong()
    hasil = potong.masuk(paket)
    cek(len(hasil) == 1, "satu paket utuh terpotong benar")
    op, r = hasil[0]
    cek(op == P.S_STATUS, "opcode terbaca")
    cek(r.b() == 200, "byte tanpa tanda terbaca")
    cek(r.sb() == -5, "byte bertanda terbaca")
    cek(r.s() == -1234, "short bertanda terbaca")
    cek(r.us() == 60000, "short tanpa tanda terbaca")
    cek(r.i() == 1234567, "int terbaca")
    cek(r.teks() == "Pendekar", "teks terbaca")
    cek(r.sisa() == 0, "payload habis pas")

    potong = P.Pemotong()
    a = P.Tulis(P.C_PING).i(1).paket()
    b = P.Tulis(P.C_CHAT).b(0).teks("halo").paket()
    gabung = a + b
    cek(potong.masuk(gabung[:3]) == [], "paket terpotong ditahan dulu")
    lanjut = potong.masuk(gabung[3:])
    cek(len(lanjut) == 2, "sisa aliran menghasilkan dua paket")
    cek(lanjut[1][1].b() == 0 and lanjut[1][1].teks() == "halo",
        "paket kedua utuh")

    kosong = P.Baca(b"")
    try:
        kosong.i()
        cek(False, "baca melewati batas dilempar sebagai error")
    except P.ProtokolError:
        cek(True, "baca melewati batas dilempar sebagai error")
    try:
        P.Tulis(P.S_PESAN).teks("x" * 70000).paket()
        cek(False, "teks kelewat panjang ditolak")
    except P.ProtokolError:
        cek(True, "teks kelewat panjang ditolak")
    r2 = P.Pemotong().masuk(P.Tulis(P.S_PESAN).teks("abcdef").paket())[0][1]
    try:
        r2.teks(3)
        cek(False, "batas panjang teks saat membaca dihormati")
    except P.ProtokolError:
        cek(True, "batas panjang teks saat membaca dihormati")

    nol = P.Pemotong()
    try:
        nol.masuk(b"\x00\x00")
        cek(False, "panjang paket nol ditolak")
    except P.ProtokolError:
        cek(True, "panjang paket nol ditolak")

    ops = [v for k, v in vars(P).items()
           if k.startswith(("C_", "S_")) and isinstance(v, int)]
    cek(len(ops) == len(set(ops)), "tidak ada opcode kembar")
    cek(all(0 < o < 256 for o in ops), "semua opcode muat satu byte")


def uji_db():
    bagian("== 4. basis data dan inventori")
    d = tempfile.mkdtemp(prefix="wira-inti-")
    con, baru = DB.buka(os.path.join(d, "inti.db"))
    cek(baru, "database baru dibuat")
    akun = DB.buat_akun(con, "budi", "sandi123")
    cek(akun, "akun dibuat")
    cek(DB.buat_akun(con, "budi", "lain") is None, "nama akun kembar ditolak")
    aid, err = DB.cek_akun(con, "budi", "sandi123")
    cek(aid == akun and err is None, "login benar diterima")
    aid, err = DB.cek_akun(con, "budi", "salah")
    cek(aid is None and err, "sandi salah ditolak")
    aid, err = DB.cek_akun(con, "hantu", "sandi123")
    cek(aid is None and err, "akun asing ditolak")

    ds = Dunia(seed=7)
    p = _pemain_uji(con, ds, akun, "Pendekar", job=0, level=5, gold=5000)
    cek(p.hp == p.hp_maks and p.hp_maks > 0, "hp penuh saat masuk")
    cek(DB.buat_karakter(con, akun, "Pendekar", 0, 0, 0, 10, 10, 0,
                         G.MAP_AWAL, 200) is None,
        "nama karakter kembar ditolak")
    cek(len(DB.daftar_karakter(con, akun)) == 1, "daftar karakter terisi")

    cek(p.slot_kosong() == 0, "tas kosong di awal")
    cek(p.tambah_item(602, 5), "item tumpuk masuk tas")
    cek(p.punya_item(602, 5) and not p.punya_item(602, 6), "stok terhitung")
    cek(len(p.inv) == 1, "item tumpuk memakai satu slot")
    cek(p.tambah_item(200, 1, 3), "senjata bertempa masuk tas")
    cek(len(p.inv) == 2, "barang bertempa tidak ditumpuk")
    cek(p.pakai_bahan(602, 3) and p.punya_item(602, 2), "bahan terpakai sebagian")
    cek(not p.pakai_bahan(602, 99), "bahan kurang tidak bisa dipakai")
    slot602 = [s for s in p.inv if p.inv[s]["id"] == 602][0]
    cek(p.buang_item(slot602, 2) and not p.punya_item(602, 1),
        "slot bersih setelah habis dibuang")
    cek(not p.buang_item(slot602, 1), "slot kosong tidak bisa dibuang lagi")
    for i in range(G.INVENTORI_MAKS):
        p.tambah_item(200, 1, i % 4)
    cek(p.slot_kosong() == -1, "tas bisa penuh")
    cek(not p.tambah_item(200, 1, 1), "tas penuh menolak barang baru")

    level_awal = p.level
    naik = p.beri_exp(G.exp_untuk(level_awal) * 3)
    cek(naik >= 1 and p.level > level_awal, "pemain naik level dari exp")
    cek(p.poin > 0, "poin statistik bertambah saat naik level")
    cek(p.hp_maks > G.statistik_dasar(p.job, level_awal)["hp_maks"],
        "hp maks ikut naik")

    DB.simpan_karakter(con, p.sebagai_baris())
    DB.simpan_item(con, p.char_id, p.inv, p.eq)
    ulang = DB.muat_karakter(con, p.char_id)
    cek(ulang["level"] == p.level and ulang["gold"] == p.gold,
        "karakter tersimpan ke database")
    inv2, eq2 = DB.muat_item(con, p.char_id)
    cek(len(inv2) == len(p.inv), "isi tas tersimpan")
    DB.catat(con, "uji", p.char_id, "catatan uji")
    cek(True, "log server bisa ditulis")


def main():
    print("WIRA NUSA - uji mandiri v1.2")
    uji_gamedata()
    uji_quest_data()
    uji_protokol()
    uji_db()

    import selftest_sosial
    selftest_sosial.jalankan(cek, bagian)

    print("")
    print("lulus : %d" % LULUS)
    print("gagal : %d" % GAGAL)
    if GAGAL:
        for m in _GAGAL_PESAN:
            print("  -", m)
        print("WIRA_TEST_FAIL")
        return 1
    print("WIRA_TEST_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
