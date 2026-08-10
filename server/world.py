#!/usr/bin/env python3
"""Logika dunia WIRA NUSA: entitas, tempur, AI mob, drop, party, ekonomi.

Semua di sini murni logika -- tidak ada socket. Itu bikin selftest bisa
menjalankan seluruh game tanpa jaringan, dan bikin server bisa diganti
transportnya (TCP sekarang, WebSocket nanti) tanpa menyentuh file ini.

Prinsip yang dipegang: CLIENT TIDAK PERNAH MENGIRIM ANGKA DAMAGE.
Client cuma mengirim niat. Semua hasil dihitung dan divalidasi di sini.
"""

import random
import time

import gamedata as G


def sekarang():
    return int(time.time() * 1000)


class Entitas(object):
    def __init__(self, eid, x, y=0):
        self.eid = eid
        self.x = x
        self.y = y
        self.arah = 1
        self.hp = 1
        self.hp_maks = 1
        self.mati_pada = 0
        self.hidup = True

    def jarak_ke(self, lain):
        dx = self.x - lain.x
        dy = self.y - lain.y
        return (dx * dx + dy * dy) ** 0.5


class Pemain(Entitas):
    def __init__(self, eid, data, inv, eq):
        Entitas.__init__(self, eid, data["x"])
        self.char_id = data["id"]
        self.akun_id = data["akun_id"]
        self.nama = data["nama"]
        self.job = data["job"]
        self.rambut = data["rambut"]
        self.kulit = data["kulit"]
        self.level = data["level"]
        self.exp = data["exp"]
        self.gold = data["gold"]
        self.map_id = data["map_id"]
        self.poin = data["poin"]
        self.skill = dict(data["skill"])
        self.quest = dict(data.get("quest") or {})
        self.inv = inv
        self.eq = eq
        self.buff = {}          # nama -> (kadaluarsa_ms, persen)
        self.cd = {}            # skill_id -> siap_pada_ms
        self.party = None
        self.trade = None
        self.guild = None        # guild_id, diisi saat login
        self.gerak_terakhir = sekarang()
        self.pelanggaran = 0
        self.mp = 0
        self.mp_maks = 1
        self.hitung_stat()
        self.hp = data["hp"] or self.hp_maks
        self.mp = data["mp"] or self.mp_maks
        self.hp = min(self.hp, self.hp_maks)
        self.mp = min(self.mp, self.mp_maks)

    # ---------------------------------------------------------- statistik
    def hitung_stat(self):
        dasar = G.statistik_dasar(self.job, self.level)
        atk = dasar["atk"]
        dfn = dasar["dfn"]
        hp_maks = dasar["hp_maks"]
        mp_maks = dasar["mp_maks"]
        for it in self.eq.values():
            info = G.ITEM.get(it["id"])
            if not info:
                continue
            plus = it.get("plus", 0)
            atk += G.stat_upgrade(info.get("atk", 0), plus)
            dfn += G.stat_upgrade(info.get("dfn", 0), plus)
            hp_maks += info.get("hp", 0)
            mp_maks += info.get("mp", 0)
        skr = sekarang()
        for nama, (habis, persen) in list(self.buff.items()):
            if habis <= skr:
                del self.buff[nama]
                continue
            if nama == "atk":
                atk += atk * persen // 100
            elif nama == "dfn":
                dfn += dfn * persen // 100
        self.atk = atk
        self.dfn = dfn
        self.jarak = dasar["jarak"]
        self.hp_maks = hp_maks
        self.mp_maks = mp_maks
        if self.hp > self.hp_maks:
            self.hp = self.hp_maks
        if self.mp > self.mp_maks:
            self.mp = self.mp_maks

    def sebagai_baris(self):
        """Data yang disimpan balik ke DB."""
        return dict(id=self.char_id, level=self.level, exp=self.exp,
                    gold=self.gold, hp=self.hp, mp=self.mp, map_id=self.map_id,
                    x=int(self.x), poin=self.poin, skill=self.skill)

    # --------------------------------------------------------- inventori
    def slot_kosong(self):
        for s in range(G.INVENTORI_MAKS):
            if s not in self.inv:
                return s
        return -1

    def tambah_item(self, item_id, jumlah=1, plus=0):
        info = G.ITEM.get(item_id)
        if not info:
            return False
        tumpuk = info.get("tumpuk", 1)
        if tumpuk > 1 and plus == 0:
            for it in self.inv.values():
                if it["id"] == item_id and it["jumlah"] < tumpuk:
                    ruang = tumpuk - it["jumlah"]
                    ambil = min(ruang, jumlah)
                    it["jumlah"] += ambil
                    jumlah -= ambil
                    if jumlah <= 0:
                        return True
        while jumlah > 0:
            slot = self.slot_kosong()
            if slot < 0:
                return False
            ambil = min(jumlah, tumpuk)
            self.inv[slot] = dict(id=item_id, jumlah=ambil, plus=plus)
            jumlah -= ambil
        return True

    def buang_item(self, slot, jumlah=1):
        it = self.inv.get(slot)
        if not it or it["jumlah"] < jumlah:
            return False
        it["jumlah"] -= jumlah
        if it["jumlah"] <= 0:
            del self.inv[slot]
        return True

    def punya_item(self, item_id, jumlah=1):
        total = sum(it["jumlah"] for it in self.inv.values() if it["id"] == item_id)
        return total >= jumlah

    def pakai_bahan(self, item_id, jumlah):
        if not self.punya_item(item_id, jumlah):
            return False
        for slot in sorted(self.inv.keys()):
            if jumlah <= 0:
                break
            it = self.inv[slot]
            if it["id"] != item_id:
                continue
            ambil = min(it["jumlah"], jumlah)
            it["jumlah"] -= ambil
            jumlah -= ambil
            if it["jumlah"] <= 0:
                del self.inv[slot]
        return True

    # ------------------------------------------------------------- level
    def beri_exp(self, jumlah):
        naik = 0
        self.exp += jumlah
        while self.level < G.LEVEL_MAKS:
            butuh = G.exp_untuk(self.level)
            if self.exp < butuh:
                break
            self.exp -= butuh
            self.level += 1
            self.poin += 1
            naik += 1
        if self.level >= G.LEVEL_MAKS:
            self.exp = 0
        if naik:
            self.hitung_stat()
            self.hp = self.hp_maks
            self.mp = self.mp_maks
        return naik


class MobHidup(Entitas):
    def __init__(self, eid, mob_id, x, tanah):
        Entitas.__init__(self, eid, x, tanah)
        self.mob_id = mob_id
        info = G.MOB[mob_id]
        self.info = info
        self.hp_maks = info["hp"]
        self.hp = info["hp"]
        self.rumah_x = x
        self.target = None
        self.serang_pada = 0
        self.kontribusi = {}   # char_id -> damage, untuk pembagian exp

    def reset(self):
        self.hp = self.hp_maks
        self.hidup = True
        self.target = None
        self.kontribusi = {}
        self.x = self.rumah_x


class Trade(object):
    """Satu sesi dagang dua arah.

    Aturan yang bikin ini aman: penawaran disimpan sebagai (slot, jumlah)
    milik server, bukan daftar item yang dikirim client; setiap perubahan
    penawaran otomatis membuka kunci kedua pihak; dan isi tas dicek ulang
    tepat sebelum barang berpindah.
    """

    def __init__(self, tid, a, b):
        self.id = tid
        self.a = a
        self.b = b
        self.aktif = False
        self.waktu = sekarang()
        self.tawar = {a.char_id: dict(gold=0, item=[]),
                      b.char_id: dict(gold=0, item=[])}
        self.kunci = {a.char_id: False, b.char_id: False}

    def lawan(self, pemain):
        return self.b if pemain.char_id == self.a.char_id else self.a


class Drop(object):
    def __init__(self, did, item_id, jumlah, plus, x, pemilik, waktu):
        self.did = did
        self.item_id = item_id
        self.jumlah = jumlah
        self.plus = plus
        self.x = x
        self.pemilik = pemilik   # char_id yang berhak duluan
        self.waktu = waktu


class Peta(object):
    def __init__(self, map_id, info, dunia):
        self.map_id = map_id
        self.info = info
        self.dunia = dunia
        self.pemain = {}    # eid -> Pemain
        self.mob = {}       # eid -> MobHidup
        self.drop = {}      # did -> Drop
        self._spawn_mob()

    def _spawn_mob(self):
        rng = self.dunia.rng
        for mob_id, jumlah in self.info["spawn"]:
            for _ in range(jumlah):
                x = rng.randint(120, self.info["lebar"] - 120)
                eid = self.dunia.eid_baru()
                self.mob[eid] = MobHidup(eid, mob_id, x, self.info["tanah"])

    def sekitar(self, x, jarak=G.VIEW_RANGE):
        return [p for p in self.pemain.values() if abs(p.x - x) <= jarak]


class Dunia(object):
    """Kumpulan peta + aturan main. Tidak tahu apa-apa soal socket."""

    def __init__(self, seed=None, kirim=None):
        self.rng = random.Random(seed)
        self._eid = 1000
        self._did = 1
        self.peta = {}
        self.pemain_by_char = {}
        self.party = {}
        self._party_id = 1
        self._tid = 1
        self.guild = {}          # gid -> dict guild
        self.guild_by_nama = {}  # nama huruf kecil -> gid
        self._gid = 0
        self.guild_kotor = set()  # gid yang perlu ditulis ulang ke DB
        self.guild_dihapus = set()  # gid yang harus dihapus dari DB
        self.war = {}            # war_id -> dict perang
        self.war_ajakan = {}     # gid tertantang -> dict(dari, taruhan, batas)
        self._war_id = 0
        self.kirim = kirim or (lambda pemain, opcode, isi: None)
        self.kejadian = []      # log ringkas untuk selftest/debug
        for map_id, info in G.MAP.items():
            self.peta[map_id] = Peta(map_id, info, self)

    # -------------------------------------------------------------- util
    def eid_baru(self):
        self._eid += 1
        return self._eid

    def did_baru(self):
        self._did += 1
        return self._did

    def catat(self, *bagian):
        self.kejadian.append(" ".join(str(b) for b in bagian))
        if len(self.kejadian) > 500:
            del self.kejadian[:250]

    # ------------------------------------------------------------ masuk
    def masuk(self, pemain):
        peta = self.peta[pemain.map_id]
        peta.pemain[pemain.eid] = pemain
        self.pemain_by_char[pemain.char_id] = pemain
        pemain.y = peta.info["tanah"]
        self.catat("masuk", pemain.nama, "map", pemain.map_id)
        return peta

    def keluar(self, pemain):
        peta = self.peta.get(pemain.map_id)
        if peta and pemain.eid in peta.pemain:
            del peta.pemain[pemain.eid]
        self.pemain_by_char.pop(pemain.char_id, None)
        if pemain.party:
            self.party_keluar(pemain)
        if pemain.trade:
            self.trade_batal(pemain, "lawan keluar")
        self.catat("keluar", pemain.nama)

    def pindah_map(self, pemain, tujuan, x):
        if tujuan not in self.peta:
            return False
        if pemain.trade:
            self.trade_batal(pemain, "lawan pindah map")
        lama = self.peta[pemain.map_id]
        lama.pemain.pop(pemain.eid, None)
        pemain.map_id = tujuan
        pemain.x = x
        baru = self.peta[tujuan]
        baru.pemain[pemain.eid] = pemain
        pemain.y = baru.info["tanah"]
        self.catat("pindah", pemain.nama, "ke", tujuan)
        return True

    # ------------------------------------------------------------ gerak
    def gerak(self, pemain, x, arah, state):
        """Validasi anti-speedhack: jarak per paket dibatasi kecepatan resmi."""
        peta = self.peta[pemain.map_id]
        x = max(0, min(int(x), peta.info["lebar"]))
        skr = sekarang()
        selisih_ms = max(1, skr - pemain.gerak_terakhir)
        batas = (G.WALK_SPEED * G.RUN_TOLERANCE * selisih_ms) // G.TICK_MS + 24
        if abs(x - pemain.x) > batas:
            pemain.pelanggaran += 1
            self.catat("koreksi", pemain.nama, "lompat", abs(x - pemain.x))
            return False
        pemain.x = x
        pemain.arah = 1 if arah >= 0 else -1
        pemain.gerak_terakhir = skr
        return True

    # ----------------------------------------------------------- tempur
    def _damage(self, atk, dfn, rng):
        """Rumus damage: pengurangan proporsional + variasi 10 persen."""
        mentah = atk * 100 // (100 + max(0, dfn) * 3)
        mentah = max(1, mentah)
        variasi = rng.randint(-10, 10)
        return max(1, mentah + mentah * variasi // 100)

    def serang(self, pemain, skill_id, target_eid):
        if not pemain.hidup:
            return "kamu sedang mati"
        peta = self.peta[pemain.map_id]
        skr = sekarang()
        skill = None
        if skill_id:
            skill = G.SKILL.get(skill_id)
            if skill is None or skill["job"] != pemain.job:
                return "skill tidak dikenal"
            lv = pemain.skill.get(str(skill_id), 0)
            if lv <= 0:
                return "skill belum dipelajari"
            if pemain.cd.get(skill_id, 0) > skr:
                return "skill masih cooldown"
            if pemain.mp < skill["mp"]:
                return "mp tidak cukup"

        korban = []
        if skill and skill["tipe"] == 2:      # penyembuhan
            pemain.mp -= skill["mp"]
            pemain.cd[skill_id] = skr + skill["cd"]
            lv = pemain.skill.get(str(skill_id), 1)
            heal = skill["heal"] + skill["heal"] * G.SKILL_KENAIKAN * (lv - 1) // 100
            pemain.hp = min(pemain.hp_maks, pemain.hp + heal)
            self.catat("heal", pemain.nama, heal)
            return None
        if skill and skill["tipe"] == 3:      # buff
            pemain.mp -= skill["mp"]
            pemain.cd[skill_id] = skr + skill["cd"]
            if "atk_persen" in skill:
                pemain.buff["atk"] = (skr + skill["durasi"], skill["atk_persen"])
            if "dfn_persen" in skill:
                pemain.buff["dfn"] = (skr + skill["durasi"], skill["dfn_persen"])
            pemain.hitung_stat()
            self.catat("buff", pemain.nama, skill["nama"])
            return None

        if skill and skill["tipe"] == 1:      # area
            radius = skill["radius"]
            korban = [m for m in peta.mob.values()
                      if m.hidup and abs(m.x - pemain.x) <= radius]
        else:
            mob = peta.mob.get(target_eid)
            if mob is None or not mob.hidup:
                return "target tidak ada"
            if abs(mob.x - pemain.x) > pemain.jarak + 12:
                return "target terlalu jauh"
            korban = [mob]

        if skill:
            pemain.mp -= skill["mp"]
            pemain.cd[skill_id] = skr + skill["cd"]

        hasil = []
        for mob in korban:
            atk = pemain.atk
            if skill:
                lv = pemain.skill.get(str(skill_id), 1)
                persen = skill["dmg"] + G.SKILL_KENAIKAN * (lv - 1)
                atk = atk * persen // 100
            dmg = self._damage(atk, mob.info["dfn"], self.rng)
            mob.hp -= dmg
            mob.kontribusi[pemain.char_id] = mob.kontribusi.get(pemain.char_id, 0) + dmg
            if mob.target is None:
                mob.target = pemain.eid
            hasil.append((mob.eid, dmg, max(0, mob.hp)))
            if mob.hp <= 0:
                self.mob_mati(peta, mob)
        self.terakhir_damage = hasil
        return None

    def mob_mati(self, peta, mob):
        mob.hidup = False
        mob.mati_pada = sekarang()
        info = mob.info
        # exp dibagi ke penyumbang damage; party dapat bonus
        total = sum(mob.kontribusi.values()) or 1
        for char_id, dmg in mob.kontribusi.items():
            pemain = self.pemain_by_char.get(char_id)
            if pemain is None or pemain.map_id != peta.map_id:
                continue
            bagian = info["exp"] * dmg // total
            bonus_exp = self.guild_bonus_persen(pemain, "exp")
            bagian += bagian * bonus_exp // 100
            anggota = self.party.get(pemain.party, {}).get("anggota", [])
            dekat = [c for c in anggota
                     if c in self.pemain_by_char
                     and self.pemain_by_char[c].map_id == peta.map_id]
            if len(dekat) > 1:
                bagian = bagian * G.PARTY_BAGI_EXP // 100 // len(dekat)
                for c in dekat:
                    rekan = self.pemain_by_char[c]
                    naik = rekan.beri_exp(bagian)
                    if naik:
                        self.catat("levelup", rekan.nama, rekan.level)
            else:
                naik = pemain.beri_exp(bagian)
                if naik:
                    self.catat("levelup", pemain.nama, pemain.level)
            emas = info["gold"] * dmg // total
            bonus = self.guild_bonus_persen(pemain, "gold")
            pemain.gold += emas + emas * bonus // 100
            self.quest_bunuh(pemain, mob.mob_id)
            self.war_bunuh(pemain, info.get("lv", 1))
            for c in dekat:
                if c != char_id and c in self.pemain_by_char:
                    self.quest_bunuh(self.pemain_by_char[c], mob.mob_id)
        # drop
        pemilik = max(mob.kontribusi, key=mob.kontribusi.get) if mob.kontribusi else 0
        for item_id, peluang, jmin, jmaks in G.DROP.get(mob.mob_id, []):
            if self.rng.randint(1, 10000) <= peluang:
                jumlah = self.rng.randint(jmin, jmaks)
                did = self.did_baru()
                peta.drop[did] = Drop(did, item_id, jumlah, 0,
                                      mob.x + self.rng.randint(-12, 12),
                                      pemilik, sekarang())
        self.catat("mob_mati", info["nama"], "oleh", pemilik)

    def ambil_drop(self, pemain, did):
        peta = self.peta[pemain.map_id]
        d = peta.drop.get(did)
        if d is None:
            return "barang sudah diambil"
        if abs(d.x - pemain.x) > 48:
            return "terlalu jauh"
        umur = sekarang() - d.waktu
        if d.pemilik and d.pemilik != pemain.char_id and umur < 10000:
            return "barang masih milik penjatuh"
        if not pemain.tambah_item(d.item_id, d.jumlah, d.plus):
            return "inventori penuh"
        del peta.drop[did]
        return None

    # -------------------------------------------------------- equipment
    def pakai_equip(self, pemain, slot):
        it = pemain.inv.get(slot)
        if not it:
            return "slot kosong"
        info = G.ITEM.get(it["id"])
        if not info or info["jenis"] not in G.SLOT_EQUIP:
            return "item ini tidak bisa dipakai"
        if info.get("lv", 1) > pemain.level:
            return "level belum cukup"
        if info["jenis"] == 1 and info.get("job") != pemain.job:
            return "senjata ini bukan untuk job kamu"
        tujuan = G.SLOT_EQUIP[info["jenis"]]
        lama = pemain.eq.get(tujuan)
        del pemain.inv[slot]
        pemain.eq[tujuan] = it
        if lama:
            pemain.inv[slot] = lama
        pemain.hitung_stat()
        return None

    def lepas_equip(self, pemain, slot_equip):
        it = pemain.eq.get(slot_equip)
        if not it:
            return "tidak ada yang dipakai"
        kosong = pemain.slot_kosong()
        if kosong < 0:
            return "inventori penuh"
        del pemain.eq[slot_equip]
        pemain.inv[kosong] = it
        pemain.hitung_stat()
        return None

    def upgrade(self, pemain, slot_equip):
        it = pemain.eq.get(slot_equip)
        if not it:
            return "tidak ada yang dipakai di slot itu", 0
        plus = it.get("plus", 0)
        if plus >= G.UPGRADE_MAKS:
            return "sudah maksimal", 0
        butuh = G.UPGRADE_BATU[plus]
        if not pemain.punya_item(600, butuh):
            return "butuh %d Batu Tempa" % butuh, 0
        pemain.pakai_bahan(600, butuh)
        peluang = G.UPGRADE_PELUANG[plus]
        if self.rng.randint(1, 100) <= peluang:
            it["plus"] = plus + 1
            pemain.hitung_stat()
            self.catat("upgrade_sukses", pemain.nama, it["id"], it["plus"])
            return None, it["plus"]
        self.catat("upgrade_gagal", pemain.nama, it["id"], plus)
        return "gagal, batu hangus", plus

    # -------------------------------------------------------- consumable
    def pakai_item(self, pemain, slot):
        it = pemain.inv.get(slot)
        if not it:
            return "slot kosong"
        info = G.ITEM.get(it["id"])
        if not info or info["jenis"] != 0:
            return "item ini tidak bisa diminum"
        if info.get("teleport"):
            self.pindah_map(pemain, G.MAP_AWAL, G.SPAWN_AWAL_X)
        if info.get("hp"):
            pemain.hp = min(pemain.hp_maks, pemain.hp + info["hp"])
        if info.get("mp"):
            pemain.mp = min(pemain.mp_maks, pemain.mp + info["mp"])
        pemain.buang_item(slot, 1)
        return None

    # ------------------------------------------------------------- toko
    def beli(self, pemain, item_id, jumlah):
        if item_id not in G.TOKO:
            return "barang tidak dijual"
        jumlah = max(1, min(int(jumlah), 99))
        harga = G.ITEM[item_id]["harga"] * jumlah
        if pemain.gold < harga:
            return "gold tidak cukup"
        if not pemain.tambah_item(item_id, jumlah):
            return "inventori penuh"
        pemain.gold -= harga
        return None

    def jual(self, pemain, slot, jumlah):
        it = pemain.inv.get(slot)
        if not it:
            return "slot kosong"
        jumlah = max(1, min(int(jumlah), it["jumlah"]))
        info = G.ITEM[it["id"]]
        harga = info["harga"] * jumlah // 4    # jual = 25 persen harga beli
        pemain.buang_item(slot, jumlah)
        pemain.gold += harga
        return None

    # ------------------------------------------------------------ skill
    def naik_skill(self, pemain, skill_id):
        skill = G.SKILL.get(skill_id)
        if not skill or skill["job"] != pemain.job:
            return "skill tidak dikenal"
        if pemain.level < skill["lv_min"]:
            return "level belum cukup"
        if pemain.poin <= 0:
            return "tidak ada poin skill"
        kunci = str(skill_id)
        lv = pemain.skill.get(kunci, 0)
        if lv >= G.SKILL_LEVEL_MAKS:
            return "skill sudah maksimal"
        pemain.skill[kunci] = lv + 1
        pemain.poin -= 1
        return None

    # ------------------------------------------------------------ party
    def party_buat(self, pemain):
        if pemain.party:
            return "kamu sudah punya party"
        pid = self._party_id
        self._party_id += 1
        self.party[pid] = dict(id=pid, ketua=pemain.char_id,
                               anggota=[pemain.char_id])
        pemain.party = pid
        return None

    def party_masuk(self, pemain, pid):
        p = self.party.get(pid)
        if not p:
            return "party tidak ada"
        if pemain.party:
            return "kamu sudah punya party"
        if len(p["anggota"]) >= G.PARTY_MAKS:
            return "party penuh"
        p["anggota"].append(pemain.char_id)
        pemain.party = pid
        return None

    def party_keluar(self, pemain):
        pid = pemain.party
        p = self.party.get(pid)
        pemain.party = None
        if not p:
            return None
        if pemain.char_id in p["anggota"]:
            p["anggota"].remove(pemain.char_id)
        if not p["anggota"]:
            del self.party[pid]
        elif p["ketua"] == pemain.char_id:
            p["ketua"] = p["anggota"][0]
        return None

    # ------------------------------------------------------------ quest
    def quest_progres(self, pemain, qid):
        """(progres sekarang, jumlah yang dibutuhkan).

        Quest kumpul dihitung langsung dari isi tas supaya tidak bisa
        dicurangi: yang dihitung isi tas saat ini, bukan angka yang
        pernah dikirim client.
        """
        q = G.QUEST[qid]
        butuh = q["jumlah"]
        if q["jenis"] == 1:
            punya = sum(it["jumlah"] for it in pemain.inv.values()
                        if it["id"] == q["sasaran"])
            return min(punya, butuh), butuh
        st = pemain.quest.get(qid)
        return (min(st["progres"], butuh) if st else 0), butuh

    def quest_kode(self, pemain, qid):
        """Kode status untuk client: 0 bisa ambil, 1 jalan, 2 siap serah,
        3 sudah selesai, 4 syarat belum terpenuhi."""
        q = G.QUEST[qid]
        st = pemain.quest.get(qid)
        if st and st["status"] != G.Q_SELESAI:
            progres, butuh = self.quest_progres(pemain, qid)
            return 2 if progres >= butuh else 1
        if st and st["status"] == G.Q_SELESAI and not q.get("ulang"):
            return 3
        if pemain.level < q["lv"]:
            return 4
        butuh_q = q["butuh"]
        if butuh_q:
            sebelum = pemain.quest.get(butuh_q)
            if not sebelum or sebelum["status"] != G.Q_SELESAI:
                return 4
        return 0

    def quest_aktif(self, pemain):
        return [qid for qid, st in pemain.quest.items()
                if st["status"] != G.Q_SELESAI]

    def quest_daftar_npc(self, pemain, map_id, npc_idx):
        keluar = []
        for qid in G.quest_npc(map_id, npc_idx):
            kode = self.quest_kode(pemain, qid)
            progres, butuh = self.quest_progres(pemain, qid)
            keluar.append((qid, kode, progres, butuh))
        return keluar

    def _dekat_npc(self, pemain, qid):
        map_id, idx = G.QUEST[qid]["npc"]
        if pemain.map_id != map_id:
            return False
        npc = self.peta[map_id].info["npc"]
        if idx >= len(npc):
            return False
        return abs(pemain.x - npc[idx][0]) <= 90

    def quest_ambil(self, pemain, qid):
        q = G.QUEST.get(qid)
        if not q:
            return "quest tidak ada"
        if not self._dekat_npc(pemain, qid):
            return "kamu jauh dari NPC-nya"
        kode = self.quest_kode(pemain, qid)
        if kode == 3:
            return "quest ini sudah selesai"
        if kode == 4:
            return "syarat belum terpenuhi"
        if kode in (1, 2):
            return "quest ini sedang berjalan"
        if len(self.quest_aktif(pemain)) >= G.QUEST_AKTIF_MAKS:
            return "quest aktif sudah %d" % G.QUEST_AKTIF_MAKS
        lama = pemain.quest.get(qid) or {}
        pemain.quest[qid] = dict(status=G.Q_AKTIF, progres=0,
                                 kali=lama.get("kali", 0))
        self.catat("quest_ambil", pemain.nama, qid)
        return None

    def quest_batal(self, pemain, qid):
        st = pemain.quest.get(qid)
        if not st or st["status"] == G.Q_SELESAI:
            return "quest itu tidak sedang berjalan"
        if st.get("kali", 0) > 0:
            st["status"] = G.Q_SELESAI
            st["progres"] = 0
        else:
            del pemain.quest[qid]
        self.catat("quest_batal", pemain.nama, qid)
        return None

    def quest_bunuh(self, pemain, mob_id):
        """Dipanggil setiap mob mati untuk tiap pemain yang berhak."""
        for qid, st in pemain.quest.items():
            if st["status"] != G.Q_AKTIF:
                continue
            q = G.QUEST.get(qid)
            if not q or q["jenis"] != 0 or q["sasaran"] != mob_id:
                continue
            if st["progres"] < q["jumlah"]:
                st["progres"] += 1

    def quest_serah(self, pemain, qid):
        q = G.QUEST.get(qid)
        if not q:
            return "quest tidak ada", None
        st = pemain.quest.get(qid)
        if not st or st["status"] == G.Q_SELESAI:
            return "quest itu tidak sedang berjalan", None
        if not self._dekat_npc(pemain, qid):
            return "lapor langsung ke NPC-nya", None
        progres, butuh = self.quest_progres(pemain, qid)
        if progres < butuh:
            return "syarat belum lengkap (%d/%d)" % (progres, butuh), None
        hadiah = G.hadiah_item(qid, pemain.job)
        kosong = sum(1 for s in range(G.INVENTORI_MAKS) if s not in pemain.inv)
        if q["jenis"] == 1:
            kosong += 1          # slot bahan yang bakal ikut kosong
        if len(hadiah) > kosong:
            return "kosongkan dulu tasmu", None
        if q["jenis"] == 1:
            pemain.pakai_bahan(q["sasaran"], butuh)
        naik = pemain.beri_exp(q["exp"])
        pemain.gold += q["gold"]
        for item_id, jumlah in hadiah:
            pemain.tambah_item(item_id, jumlah)
        st["status"] = G.Q_SELESAI
        st["progres"] = 0
        st["kali"] = st.get("kali", 0) + 1
        self.catat("quest_selesai", pemain.nama, qid)
        return None, dict(nama=q["nama"], teks=q["selesai"], exp=q["exp"],
                          gold=q["gold"], item=hadiah, naik=naik,
                          berikut=q.get("berikut", 0))

    # ------------------------------------------------------------ trade
    def _trade_id(self):
        self._tid += 1
        return self._tid

    def trade_ajak(self, pemain, target_eid):
        if pemain.trade:
            return "kamu sedang berdagang", None
        peta = self.peta[pemain.map_id]
        lawan = peta.pemain.get(target_eid)
        if lawan is None or lawan.eid == pemain.eid:
            return "pemain itu tidak ada di sini", None
        if lawan.trade:
            return "dia sedang berdagang", None
        if not pemain.hidup or not lawan.hidup:
            return "tidak bisa berdagang sambil tumbang", None
        if abs(pemain.x - lawan.x) > G.TRADE_JARAK:
            return "terlalu jauh, dekati dulu", None
        t = Trade(self._trade_id(), pemain, lawan)
        pemain.trade = t
        lawan.trade = t
        self.catat("trade_ajak", pemain.nama, lawan.nama)
        return None, t

    def trade_terima(self, pemain):
        t = pemain.trade
        if not t:
            return "tidak ada ajakan dagang", None
        if t.b.char_id != pemain.char_id:
            return "kamu yang mengajak, tunggu jawabannya", None
        if t.aktif:
            return "dagang sudah dimulai", None
        t.aktif = True
        self.catat("trade_mulai", t.a.nama, t.b.nama)
        return None, t

    def trade_batal(self, pemain, alasan="dibatalkan"):
        t = pemain.trade
        if not t:
            return None, None, alasan
        t.a.trade = None
        t.b.trade = None
        self.catat("trade_batal", t.a.nama, t.b.nama, alasan)
        return t.a, t.b, alasan

    def trade_tawar(self, pemain, gold, daftar):
        """daftar = [(slot, jumlah)]. Setiap perubahan membuka kunci kedua
        pihak, jadi isi tidak bisa diganti diam-diam setelah lawan setuju."""
        t = pemain.trade
        if not t or not t.aktif:
            return "tidak sedang berdagang", None
        gold = int(gold)
        if gold < 0 or gold > G.TRADE_GOLD_MAKS:
            return "jumlah gold tidak masuk akal", None
        if gold > pemain.gold:
            return "gold kamu tidak cukup", None
        if len(daftar) > G.TRADE_SLOT_MAKS:
            return "maksimal %d barang" % G.TRADE_SLOT_MAKS, None
        dipakai = set()
        bersih = []
        for slot, jumlah in daftar:
            it = pemain.inv.get(slot)
            if not it:
                return "slot %d kosong" % slot, None
            if slot in dipakai:
                return "slot dobel", None
            jumlah = int(jumlah)
            if jumlah < 1 or jumlah > it["jumlah"]:
                return "jumlah barang tidak valid", None
            dipakai.add(slot)
            bersih.append((slot, jumlah))
        t.tawar[pemain.char_id] = dict(gold=gold, item=bersih)
        t.kunci[t.a.char_id] = False
        t.kunci[t.b.char_id] = False
        return None, t

    def trade_kunci(self, pemain):
        t = pemain.trade
        if not t or not t.aktif:
            return "tidak sedang berdagang", None, False
        t.kunci[pemain.char_id] = True
        if not (t.kunci[t.a.char_id] and t.kunci[t.b.char_id]):
            return None, t, False
        err = self._trade_eksekusi(t)
        if err:
            t.kunci[t.a.char_id] = False
            t.kunci[t.b.char_id] = False
            return err, t, False
        t.a.trade = None
        t.b.trade = None
        return None, t, True

    def _trade_eksekusi(self, t):
        """Pindahkan barang dan gold. Semua dicek ulang di detik terakhir."""
        a, b = t.a, t.b
        if a.map_id != b.map_id or abs(a.x - b.x) > G.TRADE_JARAK:
            return "kalian terpisah terlalu jauh"
        if not a.hidup or not b.hidup:
            return "ada yang tumbang"
        paket = {}
        for pemain in (a, b):
            tawar = t.tawar[pemain.char_id]
            if tawar["gold"] > pemain.gold:
                return "%s kekurangan gold" % pemain.nama
            isi = []
            for slot, jumlah in tawar["item"]:
                it = pemain.inv.get(slot)
                if not it or it["jumlah"] < jumlah:
                    return "barang %s sudah berubah" % pemain.nama
                isi.append((it["id"], jumlah, it.get("plus", 0)))
            paket[pemain.char_id] = isi
        for pengirim, penerima in ((a, b), (b, a)):
            masuk = paket[pengirim.char_id]
            keluar = len(t.tawar[penerima.char_id]["item"])
            kosong = sum(1 for s in range(G.INVENTORI_MAKS)
                         if s not in penerima.inv) + keluar
            if len(masuk) > kosong:
                return "tas %s penuh" % penerima.nama
        for pemain in (a, b):
            for slot, jumlah in sorted(t.tawar[pemain.char_id]["item"],
                                       reverse=True):
                pemain.buang_item(slot, jumlah)
            pemain.gold -= t.tawar[pemain.char_id]["gold"]
        for pengirim, penerima in ((a, b), (b, a)):
            for item_id, jumlah, plus in paket[pengirim.char_id]:
                penerima.tambah_item(item_id, jumlah, plus)
            penerima.gold += t.tawar[pengirim.char_id]["gold"]
        self.catat("trade_sukses", a.nama, b.nama,
                   "%dg" % t.tawar[a.char_id]["gold"],
                   "%dg" % t.tawar[b.char_id]["gold"])
        return None

    # ------------------------------------------------------------- tick
    def tick(self):
        """Satu langkah simulasi. Mengembalikan daftar peristiwa broadcast."""
        skr = sekarang()
        peristiwa = []
        for peta in self.peta.values():
            aman = peta.info["aman"]
            for mob in list(peta.mob.values()):
                if not mob.hidup:
                    if skr - mob.mati_pada >= G.RESPAWN_MOB_MS:
                        mob.reset()
                        peristiwa.append(("mob_spawn", peta.map_id, mob))
                    continue
                if aman:
                    continue
                self._ai_mob(peta, mob, skr, peristiwa)
            # drop kedaluwarsa
            for did, d in list(peta.drop.items()):
                if skr - d.waktu > G.DROP_UMUR_MS:
                    del peta.drop[did]
                    peristiwa.append(("drop_hapus", peta.map_id, did))
            # regen + respawn pemain
            for pemain in list(peta.pemain.values()):
                if not pemain.hidup:
                    if skr - pemain.mati_pada >= G.RESPAWN_PLAYER_MS:
                        pemain.hidup = True
                        pemain.hp = pemain.hp_maks // 2
                        pemain.mp = pemain.mp_maks // 2
                        self.pindah_map(pemain, G.MAP_AWAL, G.SPAWN_AWAL_X)
                        peristiwa.append(("hidup_lagi", peta.map_id, pemain))
                    continue
                if pemain.hp < pemain.hp_maks:
                    pemain.hp = min(pemain.hp_maks, pemain.hp + 1 + pemain.level // 8)
                if pemain.mp < pemain.mp_maks:
                    pemain.mp = min(pemain.mp_maks, pemain.mp + 1 + pemain.level // 12)
                if pemain.buff:
                    pemain.hitung_stat()
        for hasil in self.war_tick():
            peristiwa.append(("war_selesai", 0, hasil))
        return peristiwa

    def _ai_mob(self, peta, mob, skr, peristiwa):
        target = None
        if mob.target:
            target = peta.pemain.get(mob.target)
            if target is None or not target.hidup or abs(target.x - mob.x) > G.AGGRO_RANGE * 2:
                mob.target = None
                target = None
        if target is None:
            dekat = [p for p in peta.pemain.values()
                     if p.hidup and abs(p.x - mob.x) <= G.AGGRO_RANGE]
            if dekat:
                target = min(dekat, key=lambda p: abs(p.x - mob.x))
                mob.target = target.eid
        if target is None:
            # patroli pelan balik ke rumah
            if abs(mob.x - mob.rumah_x) > 4:
                mob.x += 1 if mob.rumah_x > mob.x else -1
            return
        jarak = abs(target.x - mob.x)
        mob.arah = 1 if target.x > mob.x else -1
        if jarak > mob.info["jarak"]:
            mob.x += mob.info["speed"] * mob.arah
            peristiwa.append(("mob_gerak", peta.map_id, mob))
            return
        if skr < mob.serang_pada:
            return
        mob.serang_pada = skr + 1200
        dmg = self._damage(mob.info["atk"], target.dfn, self.rng)
        target.hp -= dmg
        peristiwa.append(("mob_serang", peta.map_id, mob, target, dmg))
        if target.hp <= 0:
            target.hp = 0
            target.hidup = False
            target.mati_pada = skr
            hilang = target.gold // 20
            target.gold -= hilang
            mob.target = None
            peristiwa.append(("pemain_mati", peta.map_id, target, hilang))
            self.catat("pemain_mati", target.nama, "oleh", mob.info["nama"])

    # ------------------------------------------------------------ guild
    # Guild disimpan di memori (dict) dan dicerminkan ke DB oleh app.py
    # lewat set `guild_kotor`: setiap perubahan menandai gid yang harus
    # ditulis ulang. Selftest bisa memakai semua ini tanpa DB sama sekali.

    def _gid_baru(self):
        self._gid += 1
        return self._gid

    def guild_tandai(self, gid):
        self.guild_kotor.add(gid)

    def guild_muat(self, baris):
        """Isi ulang dari DB saat boot. baris = list dict ala db.muat_guild_semua."""
        for g in baris:
            g = dict(g)
            g.setdefault("anggota", {})
            g["anggota"] = dict((int(k), dict(v)) for k, v in g["anggota"].items())
            g.setdefault("menang", 0)
            g.setdefault("kalah", 0)
            g.setdefault("war_akhir", 0)
            self.guild[g["id"]] = g
            self.guild_by_nama[g["nama"].lower()] = g["id"]
            self._gid = max(self._gid, g["id"])

    def guild_dari(self, pemain):
        return self.guild.get(pemain.guild) if pemain.guild else None

    def guild_pangkat(self, pemain):
        g = self.guild_dari(pemain)
        if not g:
            return -1
        a = g["anggota"].get(pemain.char_id)
        return a["pangkat"] if a else -1

    def guild_bonus_persen(self, pemain, jenis):
        g = self.guild_dari(pemain)
        if not g:
            return 0
        return G.guild_bonus(g["level"], jenis)

    def guild_buat(self, pemain, nama):
        nama = (nama or "").strip()
        if pemain.guild:
            return "kamu sudah punya guild", None
        if not G.GUILD_NAMA_MIN <= len(nama) <= G.GUILD_NAMA_MAKS:
            return "nama guild %d-%d huruf" % (G.GUILD_NAMA_MIN,
                                               G.GUILD_NAMA_MAKS), None
        for ch in nama:
            if not (ch.isalnum() or ch in " _"):
                return "nama guild hanya huruf, angka, spasi, garis bawah", None
        if nama.lower() in self.guild_by_nama:
            return "nama guild sudah dipakai", None
        if pemain.gold < G.GUILD_BIAYA_BUAT:
            return "butuh %d gold untuk mendirikan guild" % G.GUILD_BIAYA_BUAT, None
        pemain.gold -= G.GUILD_BIAYA_BUAT
        gid = self._gid_baru()
        g = dict(id=gid, nama=nama, ketua_id=pemain.char_id, level=1, exp=0,
                 kas=0, menang=0, kalah=0, war_akhir=0,
                 anggota={pemain.char_id: dict(pangkat=G.P_KETUA, sumbang=0,
                                               masuk=int(sekarang() // 1000))},
                 undangan={})
        self.guild[gid] = g
        self.guild_by_nama[nama.lower()] = gid
        pemain.guild = gid
        self.guild_tandai(gid)
        self.catat("guild_buat", nama, "oleh", pemain.nama)
        return None, g

    def guild_undang(self, pemain, target):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if self.guild_pangkat(pemain) < G.P_PERWIRA:
            return "hanya perwira atau ketua yang boleh mengundang"
        if target.guild:
            return "%s sudah punya guild" % target.nama
        if len(g["anggota"]) >= G.guild_anggota_maks(g["level"]):
            return "guild penuh (maks %d di level %d)" % (
                G.guild_anggota_maks(g["level"]), g["level"])
        g.setdefault("undangan", {})[target.char_id] = sekarang() + 60000
        return None

    def guild_terima(self, pemain, gid):
        g = self.guild.get(gid)
        if not g:
            return "guild tidak ada", None
        if pemain.guild:
            return "kamu sudah punya guild", None
        batas = g.get("undangan", {}).get(pemain.char_id, 0)
        if batas < sekarang():
            return "undangan sudah kedaluwarsa", None
        if len(g["anggota"]) >= G.guild_anggota_maks(g["level"]):
            return "guild penuh", None
        del g["undangan"][pemain.char_id]
        g["anggota"][pemain.char_id] = dict(pangkat=G.P_ANGGOTA, sumbang=0,
                                            masuk=int(sekarang() // 1000))
        pemain.guild = gid
        self.guild_tandai(gid)
        self.catat("guild_masuk", pemain.nama, g["nama"])
        return None, g

    def guild_keluar(self, pemain):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if g["ketua_id"] == pemain.char_id and len(g["anggota"]) > 1:
            return "wariskan dulu jabatan ketua sebelum keluar"
        g["anggota"].pop(pemain.char_id, None)
        pemain.guild = None
        if not g["anggota"]:
            self._guild_hapus(g)
        else:
            self.guild_tandai(g["id"])
        return None

    def _guild_hapus(self, g):
        self.guild.pop(g["id"], None)
        self.guild_by_nama.pop(g["nama"].lower(), None)
        self.guild_dihapus.add(g["id"])
        self.guild_kotor.discard(g["id"])
        w = self.war_aktif(g["id"])
        if w:
            self.war_selesai(w, "guild bubar")

    def guild_bubar(self, pemain):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if g["ketua_id"] != pemain.char_id:
            return "hanya ketua yang boleh membubarkan guild"
        for cid in list(g["anggota"].keys()):
            anggota = self.pemain_by_char.get(cid)
            if anggota:
                anggota.guild = None
        g["anggota"] = {}
        self._guild_hapus(g)
        self.catat("guild_bubar", g["nama"])
        return None

    def guild_pecat(self, pemain, char_id):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if char_id == pemain.char_id:
            return "pakai keluar guild, bukan pecat"
        korban = g["anggota"].get(char_id)
        if not korban:
            return "dia bukan anggota guild kamu"
        aku = self.guild_pangkat(pemain)
        if aku <= korban["pangkat"] or aku < G.P_PERWIRA:
            return "pangkat kamu tidak cukup"
        del g["anggota"][char_id]
        lain = self.pemain_by_char.get(char_id)
        if lain:
            lain.guild = None
        self.guild_tandai(g["id"])
        return None

    def guild_set_pangkat(self, pemain, char_id, pangkat):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if g["ketua_id"] != pemain.char_id:
            return "hanya ketua yang boleh mengatur pangkat"
        a = g["anggota"].get(char_id)
        if not a:
            return "dia bukan anggota guild kamu"
        pangkat = int(pangkat)
        if pangkat not in (G.P_ANGGOTA, G.P_PERWIRA, G.P_KETUA):
            return "pangkat tidak dikenal"
        if pangkat == G.P_KETUA:
            # warisan jabatan: ketua lama turun jadi perwira
            g["anggota"][pemain.char_id]["pangkat"] = G.P_PERWIRA
            g["ketua_id"] = char_id
        a["pangkat"] = pangkat
        self.guild_tandai(g["id"])
        return None

    def guild_tambah_exp(self, g, jumlah):
        """-> jumlah level yang naik."""
        naik = 0
        g["exp"] += max(0, int(jumlah))
        while g["level"] < G.GUILD_LEVEL_MAKS:
            butuh = G.guild_exp_naik(g["level"])
            if butuh <= 0 or g["exp"] < butuh:
                break
            g["exp"] -= butuh
            g["level"] += 1
            naik += 1
        if g["level"] >= G.GUILD_LEVEL_MAKS:
            g["exp"] = min(g["exp"], G.GUILD_EXP_NAIK[-1])
        self.guild_tandai(g["id"])
        return naik

    def guild_sumbang(self, pemain, gold):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild", 0
        gold = int(gold)
        if gold < G.GUILD_SUMBANG_MIN:
            return "sumbangan minimal %d gold" % G.GUILD_SUMBANG_MIN, 0
        if pemain.gold < gold:
            return "gold kamu kurang", 0
        pemain.gold -= gold
        g["kas"] += gold
        g["anggota"][pemain.char_id]["sumbang"] += gold
        naik = self.guild_tambah_exp(g, gold * G.GUILD_EXP_PER_GOLD)
        self.catat("guild_sumbang", pemain.nama, gold)
        return None, naik

    def guild_anggota_online(self, g):
        return [self.pemain_by_char[c] for c in g["anggota"]
                if c in self.pemain_by_char]

    # -------------------------------------------------------------- war
    def war_aktif(self, gid):
        for w in self.war.values():
            if gid in (w["a"], w["b"]) and not w["selesai"]:
                return w
        return None

    def war_deklarasi(self, pemain, nama_lawan, taruhan):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild", None
        if g["ketua_id"] != pemain.char_id:
            return "hanya ketua yang boleh menyatakan perang", None
        gid_lawan = self.guild_by_nama.get((nama_lawan or "").strip().lower())
        lawan = self.guild.get(gid_lawan)
        if not lawan:
            return "guild lawan tidak ada", None
        if lawan["id"] == g["id"]:
            return "tidak bisa perang melawan guild sendiri", None
        taruhan = int(taruhan)
        if not G.WAR_TARUHAN_MIN <= taruhan <= G.WAR_TARUHAN_MAKS:
            return "taruhan %d - %d gold" % (G.WAR_TARUHAN_MIN,
                                             G.WAR_TARUHAN_MAKS), None
        for sisi in (g, lawan):
            if sisi["level"] < G.WAR_LEVEL_MIN:
                return "kedua guild minimal level %d" % G.WAR_LEVEL_MIN, None
            if sisi["kas"] < taruhan:
                return "kas %s tidak cukup untuk taruhan itu" % sisi["nama"], None
            if self.war_aktif(sisi["id"]):
                return "%s sedang perang" % sisi["nama"], None
            if sekarang() - sisi["war_akhir"] < G.WAR_COOLDOWN_MS:
                return "%s masih masa istirahat perang" % sisi["nama"], None
        self.war_ajakan[lawan["id"]] = dict(dari=g["id"], taruhan=taruhan,
                                            batas=sekarang() + 120000)
        self.catat("war_ajak", g["nama"], "vs", lawan["nama"], taruhan)
        return None, self.war_ajakan[lawan["id"]]

    def war_tolak(self, pemain):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild"
        if g["ketua_id"] != pemain.char_id:
            return "hanya ketua yang boleh menjawab tantangan"
        if self.war_ajakan.pop(g["id"], None) is None:
            return "tidak ada tantangan masuk"
        return None

    def war_terima(self, pemain):
        g = self.guild_dari(pemain)
        if not g:
            return "kamu belum punya guild", None
        if g["ketua_id"] != pemain.char_id:
            return "hanya ketua yang boleh menerima tantangan", None
        ajakan = self.war_ajakan.get(g["id"])
        if not ajakan or ajakan["batas"] < sekarang():
            self.war_ajakan.pop(g["id"], None)
            return "tidak ada tantangan yang masih berlaku", None
        penantang = self.guild.get(ajakan["dari"])
        if not penantang:
            self.war_ajakan.pop(g["id"], None)
            return "guild penantang sudah bubar", None
        taruhan = ajakan["taruhan"]
        for sisi in (g, penantang):
            if sisi["kas"] < taruhan:
                self.war_ajakan.pop(g["id"], None)
                return "kas %s tidak cukup lagi" % sisi["nama"], None
            if self.war_aktif(sisi["id"]):
                return "%s sedang perang" % sisi["nama"], None
        del self.war_ajakan[g["id"]]
        for sisi in (g, penantang):
            sisi["kas"] -= taruhan
            self.guild_tandai(sisi["id"])
        self._war_id += 1
        w = dict(id=self._war_id, a=penantang["id"], b=g["id"],
                 nama_a=penantang["nama"], nama_b=g["nama"],
                 mulai=sekarang(), akhir=sekarang() + G.WAR_DURASI_MS,
                 taruhan=taruhan, skor={penantang["id"]: 0, g["id"]: 0},
                 selesai=False, hasil=None)
        self.war[w["id"]] = w
        self.catat("war_mulai", penantang["nama"], "vs", g["nama"])
        return None, w

    def war_bunuh(self, pemain, mob_level):
        """Dipanggil dari mob_mati. -> war yang bertambah skornya atau None."""
        if not pemain.guild:
            return None
        w = self.war_aktif(pemain.guild)
        if w is None:
            return None
        w["skor"][pemain.guild] = w["skor"].get(pemain.guild, 0) + \
            G.war_skor_mob(mob_level)
        return w

    def war_selesai(self, w, alasan="waktu habis"):
        """-> dict(menang, kalah, seri, hadiah_kas, skor)."""
        if w["selesai"]:
            return w["hasil"]
        w["selesai"] = True
        skr = sekarang()
        ga = self.guild.get(w["a"])
        gb = self.guild.get(w["b"])
        sa = w["skor"].get(w["a"], 0)
        sb = w["skor"].get(w["b"], 0)
        pot = w["taruhan"] * 2
        menang = kalah = None
        if sa == sb or ga is None or gb is None:
            # seri atau salah satu bubar: taruhan dikembalikan
            for sisi in (ga, gb):
                if sisi:
                    sisi["kas"] += w["taruhan"]
                    sisi["war_akhir"] = skr
                    self.guild_tandai(sisi["id"])
        else:
            menang, kalah = (ga, gb) if sa > sb else (gb, ga)
            menang["kas"] += pot
            menang["menang"] += 1
            kalah["kalah"] += 1
            self.guild_tambah_exp(menang, G.WAR_EXP_MENANG)
            self.guild_tambah_exp(kalah, G.WAR_EXP_KALAH)
            for sisi in (menang, kalah):
                sisi["war_akhir"] = skr
                self.guild_tandai(sisi["id"])
        hasil = dict(war=w["id"], alasan=alasan, seri=menang is None,
                     menang=menang["nama"] if menang else "",
                     kalah=kalah["nama"] if kalah else "",
                     menang_id=menang["id"] if menang else 0,
                     kalah_id=kalah["id"] if kalah else 0,
                     hadiah_kas=pot if menang else w["taruhan"],
                     skor_a=sa, skor_b=sb)
        w["hasil"] = hasil
        self.catat("war_selesai", hasil["menang"] or "seri", sa, sb)
        return hasil

    def war_tick(self):
        """Tutup perang yang waktunya habis. -> daftar hasil."""
        keluar = []
        skr = sekarang()
        for w in list(self.war.values()):
            if w["selesai"]:
                if skr - w["akhir"] > 300000:
                    del self.war[w["id"]]
                continue
            if skr >= w["akhir"]:
                keluar.append(self.war_selesai(w, "waktu habis"))
        for gid, ajakan in list(self.war_ajakan.items()):
            if ajakan["batas"] < skr:
                del self.war_ajakan[gid]
        return keluar
