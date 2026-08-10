#!/usr/bin/env python3
"""Model dunia WIRA NUSA: pemain, mob, drop, portal, tempur, guild, war.

Semua mutasi state game HARUS lewat fungsi di modul ini saja, dilindungi
oleh kunci global di app.py. Tidak ada I/O, tidak ada threading di sini.
"""

import random
import time

import gamedata as G


def sekarang():
    return int(time.time() * 1000)


_eid_counter = [0]


def _next_eid():
    _eid_counter[0] += 1
    return _eid_counter[0]


class Drop(object):
    def __init__(self, did, item_id, jumlah, plus, x, pemilik_id=None):
        self.did = did
        self.item_id = item_id
        self.jumlah = jumlah
        self.plus = plus
        self.x = x
        self.pemilik_id = pemilik_id
        self.waktu = sekarang()


class Pemain(object):
    def __init__(self, char_id, nama, job, rambut, kulit, level, exp, gold,
                 hp, hp_maks, mp, mp_maks, atk, dfn, poin, skill,
                 map_id, x):
        self.eid = _next_eid()
        self.char_id = char_id
        self.nama = nama
        self.job = job
        self.rambut = rambut
        self.kulit = kulit
        self.level = level
        self.exp = exp
        self.gold = gold
        self.hp = hp
        self.hp_maks = hp_maks
        self.mp = mp
        self.mp_maks = mp_maks
        self.atk = atk
        self.dfn = dfn
        self.poin = poin
        self.skill = skill
        self.map_id = map_id
        self.x = x
        self.y = G.TANAH_Y
        self.arah = 1
        self.hidup = True
        self.mati_pada = 0
        self.inv = {}   # slot -> {id, jumlah, plus}
        self.eq = {}    # slot -> {id, jumlah, plus}
        self.quest = {} # qid -> {kode, progres, ulang}
        self.guild_id = None
        self.guild_pangkat = G.P_ANGGOTA
        self.trade = None
        self.pelanggaran = 0
        self.terakhir_damage = []

    # -------------------------------------------------------- inventori
    def tambah_item(self, item_id, jumlah, plus=0):
        """True bila berhasil, False bila tas penuh."""
        for slot in range(G.INVENTORI_MAKS):
            if slot not in self.inv:
                self.inv[slot] = {"id": item_id, "jumlah": jumlah,
                                  "plus": plus}
                return True
        return False

    def buang_item(self, slot, jumlah):
        it = self.inv.get(slot)
        if it is None:
            return
        it["jumlah"] -= jumlah
        if it["jumlah"] <= 0:
            del self.inv[slot]

    def sebagai_baris(self):
        return {
            "char_id": self.char_id,
            "map_id": self.map_id,
            "x": int(self.x),
            "hp": self.hp,
            "mp": self.mp,
            "level": self.level,
            "exp": self.exp,
            "gold": self.gold,
            "atk": self.atk,
            "dfn": self.dfn,
            "poin": self.poin,
            "skill": self.skill,
        }


class Mob(object):
    def __init__(self, mob_id, x, map_id):
        self.eid = _next_eid()
        self.mob_id = mob_id
        self.info = G.MOB[mob_id]
        self.hp = self.info["hp"]
        self.hp_maks = self.info["hp"]
        self.x = x
        self.spawn_x = x
        self.map_id = map_id
        self.arah = 1
        self.hidup = True
        self.mati_pada = 0
        self.target_eid = None
        self.terakhir_serang = 0
        self.kontribusi = {}   # eid -> total_damage untuk bagi exp

    def reset(self):
        self.hp = self.hp_maks
        self.x = self.spawn_x
        self.arah = 1
        self.hidup = True
        self.mati_pada = 0
        self.target_eid = None
        self.kontribusi = {}


class Peta(object):
    def __init__(self, map_id, info):
        self.map_id = map_id
        self.info = info
        self.pemain = {}  # eid -> Pemain
        self.mob = {}     # eid -> Mob
        self.drop = {}    # did -> Drop
        self._did = 0

        for mob_id, jumlah in info["mob"]:
            for _ in range(jumlah):
                x = random.randint(200, G.LEBAR_MAP - 200)
                m = Mob(mob_id, x, map_id)
                self.mob[m.eid] = m

    def next_did(self):
        self._did += 1
        return self._did


class Trade(object):
    """Satu sesi dagang dua arah.

    Protokol: ajak (0) -> terima (1) -> tawar (3) masing-masing sisi
    -> kunci (4) keduanya -> eksekusi. Setiap perubahan
    penawaran otomatis membuka kunci kedua pihak; dan isi tas dicek ulang
    di saat terakhir supaya tidak ada manipulasi.
    """

    def __init__(self, trade_id, a, b):
        self.id = trade_id
        self.a = a
        self.b = b
        self.aktif = False    # True setelah kedua pihak setuju mulai
        self.tawar = {
            a.char_id: {"gold": 0, "item": []},
            b.char_id: {"gold": 0, "item": []},
        }
        self.kunci = {a.char_id: False, b.char_id: False}


class GuildData(object):
    def __init__(self, baris):
        self.gid = baris["id"]
        self.nama = baris["nama"]
        self.level = baris["level"]
        self.exp = baris["exp"]
        self.kas = baris["kas"]
        self.anggota = {}  # char_id -> {nama, pangkat, online}
        self.menang = baris.get("menang", 0)
        self.kalah = baris.get("kalah", 0)
        self.kotor = False
        self.war_id = None


class WarData(object):
    def __init__(self, wid, guild_a, guild_b, taruhan, mulai_ms):
        self.id = wid
        self.guild_a = guild_a
        self.guild_b = guild_b
        self.taruhan = taruhan
        self.mulai = mulai_ms
        self.selesai = mulai_ms + G.WAR_DURASI_MS
        self.skor = {guild_a.gid: 0, guild_b.gid: 0}


class Dunia(object):
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.peta = {mid: Peta(mid, info) for mid, info in G.MAP.items()}
        self.pemain_by_char = {}  # char_id -> Pemain
        self.guild = {}           # gid -> GuildData
        self._war = {}            # wid -> WarData
        self._trade_counter = 0
        self._war_counter = 0

    # --------------------------------------------------------- guild
    def guild_muat(self, baris_list):
        for b in baris_list:
            g = GuildData(b)
            for a in b.get("anggota", []):
                g.anggota[a["char_id"]] = {
                    "nama": a["nama"], "pangkat": a["pangkat"], "online": False
                }
            self.guild[g.gid] = g

    def guild_anggota_online(self, g):
        return [p for p in self.pemain_by_char.values()
                if p.guild_id == g.gid]

    def guild_pemain(self, pemain):
        if pemain.guild_id is None:
            return None
        return self.guild.get(pemain.guild_id)

    # --------------------------------------------------------- pemain
    def masuk(self, pemain):
        peta = self.peta[pemain.map_id]
        peta.pemain[pemain.eid] = pemain
        self.pemain_by_char[pemain.char_id] = pemain
        g = self.guild_pemain(pemain)
        if g and pemain.char_id in g.anggota:
            g.anggota[pemain.char_id]["online"] = True

    def keluar(self, pemain):
        peta = self.peta.get(pemain.map_id)
        if peta:
            peta.pemain.pop(pemain.eid, None)
        self.pemain_by_char.pop(pemain.char_id, None)
        g = self.guild_pemain(pemain)
        if g and pemain.char_id in g.anggota:
            g.anggota[pemain.char_id]["online"] = False
        if pemain.trade:
            self.trade_batal(pemain, "lawan keluar")

    def pindah_map(self, pemain, map_id, x):
        peta_lama = self.peta[pemain.map_id]
        peta_lama.pemain.pop(pemain.eid, None)
        if pemain.trade:
            self.trade_batal(pemain, "lawan pindah map")
        pemain.map_id = map_id
        pemain.x = x
        pemain.y = G.TANAH_Y
        peta_baru = self.peta[map_id]
        peta_baru.pemain[pemain.eid] = pemain

    def cari_pemain(self, peta, eid):
        return peta.pemain.get(eid)

    # -------------------------------------------------------- aksi
    def gerak(self, pemain, x, selisih_ms):
        """Validasi gerak anti-speedhack. Mengembalikan x yang sah."""
        batas = (G.WALK_SPEED * G.RUN_TOLERANCE * selisih_ms) // G.TICK_MS + 24
        x = max(0, min(int(x), G.LEBAR_MAP))
        if abs(x - pemain.x) > batas:
            pemain.pelanggaran += 1
            self.catat("koreksi", pemain.nama,
                       "dari=%d ke=%d batas=%d" % (pemain.x, x, batas))
            return pemain.x
        pemain.x = x
        return x

    def _damage(self, atk, dfn, rng):
        mentah = atk * 100 // (100 + max(0, dfn) * 3)
        variasi = mentah * rng.randint(-10, 10) // 100
        return max(1, mentah + variasi)

    def serang(self, pemain, skill_id, target_eid):
        """(err, [(eid, dmg, hp_sisa)]). skill_id 0 = serangan biasa."""
        peta = self.peta[pemain.map_id]
        target = peta.mob.get(target_eid) or peta.pemain.get(target_eid)
        if target is None or not target.hidup:
            return "sasaran tidak ada", []
        if not pemain.hidup:
            return "kamu tumbang", []

        if skill_id == 0:
            jarak_maks = (G.ATTACK_RANGE_RANGED
                          if pemain.job == 3 else G.ATTACK_RANGE_MELEE)
            if abs(int(pemain.x) - int(target.x)) > jarak_maks:
                return "terlalu jauh", []
            dmg = self._damage(pemain.atk, target.info["dfn"]
                               if hasattr(target, "info")
                               else target.dfn, self.rng)
            target.hp = max(0, target.hp - dmg)
            hasil = [(target.eid, dmg, target.hp)]
        else:
            lv = int(pemain.skill.get(str(skill_id), 0))
            if lv < 1:
                return "skill belum dipelajari", []
            s = G.SKILL.get(skill_id)
            if not s or s["job"] != pemain.job:
                return "skill tidak sesuai job", []
            if pemain.mp < s["mp"]:
                return "mp kurang", []
            pemain.mp = max(0, pemain.mp - s["mp"])
            daya = G.skill_daya_total(skill_id, lv, pemain.atk)
            tipe = s["tipe"]
            if tipe == 2:  # heal
                heal = daya
                pemain.hp = min(pemain.hp_maks, pemain.hp + heal)
                hasil = [(pemain.eid, -heal, pemain.hp)]
            elif tipe == 1:  # damage tunggal atau area
                area = s.get("area", 0)
                if area:
                    sasaran = [e for e in list(peta.mob.values())
                               + list(peta.pemain.values())
                               if e.hidup and e.eid != pemain.eid
                               and abs(int(e.x) - int(pemain.x)) <= area]
                else:
                    if abs(int(pemain.x) - int(target.x)) > s["jarak"]:
                        return "terlalu jauh", []
                    sasaran = [target]
                hasil = []
                for t in sasaran:
                    dfn = t.info["dfn"] if hasattr(t, "info") else t.dfn
                    dmg = self._damage(daya, dfn, self.rng)
                    t.hp = max(0, t.hp - dmg)
                    hasil.append((t.eid, dmg, t.hp))
            else:  # buff (tipe 3)
                hasil = [(pemain.eid, 0, pemain.hp)]

        pemain.terakhir_damage = hasil
        for eid, dmg, hp_sisa in hasil:
            obj = peta.mob.get(eid) or peta.pemain.get(eid)
            if obj is None:
                continue
            if hasattr(obj, "kontribusi"):  # mob
                obj.kontribusi[pemain.eid] = (
                    obj.kontribusi.get(pemain.eid, 0) + max(0, dmg))
                if hp_sisa == 0:
                    ev = self.mob_mati(peta, obj)
                    pemain.terakhir_damage = ev
        return None, hasil

    def mob_mati(self, peta, mob):
        mob.hidup = False
        mob.mati_pada = sekarang()
        hasil_drop = []
        # bagi exp ke kontributor
        total_kontrib = sum(mob.kontribusi.values()) or 1
        dekat = [p for p in peta.pemain.values()
                 if p.hidup and abs(int(p.x) - int(mob.x)) <= G.VIEW_RANGE]
        penerima_exp = set(mob.kontribusi.keys()) | {p.eid for p in dekat}
        for p_eid in penerima_exp:
            p = peta.pemain.get(p_eid)
            if p is None or not p.hidup:
                continue
            porsi = mob.kontribusi.get(p_eid, 0)
            exp_base = mob.info["exp"] * porsi // total_kontrib
            # bonus party
            if p.eid in {pm.eid for pm in dekat}:
                party_bonus = G.PARTY_BAGI_EXP
            else:
                party_bonus = 100
            exp_base = exp_base * party_bonus // 100
            # bonus guild
            g = self.guild_pemain(p)
            if g:
                exp_base = exp_base * (100 + G.guild_bonus(g.level, "exp")) // 100
                g.exp += exp_base * G.GUILD_EXP_PER_GOLD // 10  # kontribusi kecil
                g.kotor = True
                self.war_bunuh(p, mob.info["lv"])
            self._beri_exp(p, exp_base)
        # drop
        gold_drop = mob.info["gold"] + self.rng.randint(
            -mob.info["gold"] // 4, mob.info["gold"] // 4)
        if gold_drop > 0:
            d = Drop(peta.next_did(), 0, gold_drop, 0,
                     mob.x + self.rng.randint(-20, 20))
            peta.drop[d.did] = d
            hasil_drop.append(d)
        for item_id, pct in mob.info["drop"]:
            if self.rng.randint(1, 100) <= pct:
                d = Drop(peta.next_did(), item_id, 1, 0,
                         mob.x + self.rng.randint(-20, 20))
                peta.drop[d.did] = d
                hasil_drop.append(d)
        mob.kontribusi = {}
        return [(mob.eid, 0, 0)] + [(d.did, d.item_id, d.jumlah)
                                    for d in hasil_drop]

    def _beri_exp(self, pemain, exp):
        if not pemain.hidup or pemain.level >= G.LEVEL_MAKS:
            return
        pemain.exp += exp
        while pemain.level < G.LEVEL_MAKS:
            butuh = G.exp_untuk(pemain.level)
            if butuh == 0 or pemain.exp < butuh:
                break
            pemain.exp -= butuh
            pemain.level += 1
            hp_maks, mp_maks, atk, dfn = G.stat_dasar(pemain.level, pemain.job)
            pemain.hp_maks = hp_maks
            pemain.mp_maks = mp_maks
            pemain.atk = atk
            pemain.dfn = dfn
            pemain.poin += G.SKILL_KENAIKAN
            pemain.hp = pemain.hp_maks
            pemain.mp = pemain.mp_maks

    def ambil_drop(self, pemain, did):
        peta = self.peta[pemain.map_id]
        d = peta.drop.get(did)
        if d is None:
            return "barang tidak ada"
        if abs(int(pemain.x) - int(d.x)) > 48:
            return "terlalu jauh"
        skr = sekarang()
        if d.pemilik_id and d.pemilik_id != pemain.eid:
            if skr - d.waktu < 10000:
                return "barang ini milik orang lain dulu"
        if d.item_id == 0:  # gold
            g = self.guild_pemain(pemain)
            bonus = G.guild_bonus(g.level, "gold") if g else 0
            pemain.gold += d.jumlah * (100 + bonus) // 100
        else:
            if not pemain.tambah_item(d.item_id, d.jumlah, d.plus):
                return "tas penuh"
        del peta.drop[did]
        return None

    def pakai_item(self, pemain, slot):
        it = pemain.inv.get(slot)
        if it is None:
            return "slot kosong"
        info = G.ITEM.get(it["id"])
        if info is None or info["jenis"] != "potion":
            return "bukan potion"
        if not pemain.hidup:
            return "kamu tumbang"
        pemain.hp = min(pemain.hp_maks,
                        pemain.hp + info.get("hp", 0))
        pemain.mp = min(pemain.mp_maks,
                        pemain.mp + info.get("mp", 0))
        pemain.buang_item(slot, 1)
        return None

    def pakai_equip(self, pemain, slot_tas):
        it = pemain.inv.get(slot_tas)
        if it is None:
            return "slot kosong"
        info = G.ITEM.get(it["id"])
        if info is None or "slot" not in info:
            return "barang ini tidak bisa diequip"
        if info.get("job") is not None and info["job"] != pemain.job:
            return "tidak sesuai job"
        slot_eq = info["slot"]
        # tanggalkan dulu kalau ada
        if slot_eq in pemain.eq:
            lama = pemain.eq.pop(slot_eq)
            pemain.tambah_item(lama["id"], lama["jumlah"], lama.get("plus", 0))
        eq_item = pemain.inv.pop(slot_tas)
        pemain.eq[slot_eq] = eq_item
        self._hitung_stat(pemain)
        return None

    def lepas_equip(self, pemain, slot_eq):
        it = pemain.eq.get(slot_eq)
        if it is None:
            return "slot equip kosong"
        if not pemain.tambah_item(it["id"], it["jumlah"], it.get("plus", 0)):
            return "tas penuh"
        del pemain.eq[slot_eq]
        self._hitung_stat(pemain)
        return None

    def _hitung_stat(self, pemain):
        hp_maks, mp_maks, atk, dfn = G.stat_dasar(pemain.level, pemain.job)
        for it in pemain.eq.values():
            atk += G.item_atk(it["id"], it.get("plus", 0))
            dfn += G.item_dfn(it["id"], it.get("plus", 0))
        pemain.hp_maks = hp_maks
        pemain.mp_maks = mp_maks
        pemain.atk = atk
        pemain.dfn = dfn
        pemain.hp = min(pemain.hp, pemain.hp_maks)
        pemain.mp = min(pemain.mp, pemain.mp_maks)

    def upgrade(self, pemain, slot):
        it = pemain.inv.get(slot)
        if it is None:
            return "slot kosong", False
        if G.ITEM.get(it["id"], {}).get("jenis") not in (
                "senjata", "baju", "topi", "sayap"):
            return "barang ini tidak bisa di-upgrade", False
        plus = it.get("plus", 0)
        # cari batu tempa di inventori
        batu_slot = next(
            (s for s, b in pemain.inv.items()
             if b["id"] == 600), None)
        if batu_slot is None:
            return "perlu Batu Tempa", False
        pemain.buang_item(batu_slot, 1)
        if self.rng.random() < G.upgrade_peluang(plus):
            it["plus"] = plus + 1
            self._hitung_stat(pemain)
            return None, True
        return "gagal, batu hangus", False

    def toko_beli(self, pemain, item_id, jumlah, map_id):
        toko = G.MAP.get(map_id, {}).get("toko", [])
        if item_id not in toko:
            return "barang tidak dijual di sini"
        info = G.ITEM.get(item_id)
        if info is None:
            return "barang tidak dikenal"
        total = info["harga"] * jumlah
        if pemain.gold < total:
            return "gold kurang"
        if not pemain.tambah_item(item_id, jumlah, 0):
            return "tas penuh"
        pemain.gold -= total
        return None

    def toko_jual(self, pemain, slot, jumlah):
        it = pemain.inv.get(slot)
        if it is None or jumlah < 1 or it["jumlah"] < jumlah:
            return "slot tidak valid", 0
        info = G.ITEM.get(it["id"])
        if info is None:
            return "barang tidak dikenal", 0
        bayar = info["harga"] * jumlah // 4
        pemain.buang_item(slot, jumlah)
        pemain.gold += bayar
        return None, bayar

    def quest_bicara_npc(self, pemain, npc_idx):
        peta_info = G.MAP.get(pemain.map_id, {})
        npc = peta_info.get("npc", [])
        if npc_idx >= len(npc):
            return "npc tidak ada", []
        nx, _, jenis = npc[npc_idx]
        if abs(int(pemain.x) - nx) > 90:
            return "terlalu jauh dari NPC", []
        daftar = []
        for qid, q in G.QUEST.items():
            npc_map, npc_i = q["npc"]
            if npc_map != pemain.map_id or npc_i != npc_idx:
                continue
            st = pemain.quest.get(qid, {})
            kode = self._kode_quest(pemain, qid, st)
            if kode != 4:  # tampilkan semua kecuali yang terkunci level
                daftar.append((qid, kode, st.get("progres", 0),
                               q["butuh"]))
        return None, daftar

    def quest_ambil(self, pemain, qid):
        q = G.QUEST.get(qid)
        if q is None:
            return "quest tidak ada"
        kode = self._kode_quest(pemain, qid, pemain.quest.get(qid, {}))
        if kode != 0:
            return "quest tidak bisa diambil sekarang"
        pemain.quest[qid] = {"kode": 1, "progres": 0, "ulang": 0}
        return None

    def quest_serah(self, pemain, qid):
        q = G.QUEST.get(qid)
        st = pemain.quest.get(qid)
        if q is None or st is None or st["kode"] != 2:
            return "quest belum selesai"
        if q["jenis"] == 1:  # harus bawa item
            slot_item = next(
                (s for s, it in pemain.inv.items()
                 if it["id"] == q["sasaran"] and it["jumlah"] >= q["butuh"]),
                None)
            if slot_item is None:
                return "item belum cukup"
            pemain.buang_item(slot_item, q["butuh"])
        pemain.gold += q["hadiah_gold"]
        self._beri_exp(pemain, q["hadiah_exp"])
        # hadiah senjata tier 2/3 dari quest 20/21
        if q.get("hadiah_item"):
            tier = 1 if qid == 20 else 2
            senjata_id = {0: 200, 1: 210, 2: 220, 3: 230}[pemain.job] + tier
            pemain.tambah_item(senjata_id, 1, 0)
        if qid in G.QUEST_ULANG:
            st["kode"] = 0
            st["progres"] = 0
            st["ulang"] = st.get("ulang", 0) + 1
        else:
            st["kode"] = 3
        return None

    def quest_batal(self, pemain, qid):
        st = pemain.quest.get(qid)
        if st is None or st["kode"] not in (1, 2):
            return "quest tidak aktif"
        del pemain.quest[qid]
        return None

    def _kode_quest(self, pemain, qid, st):
        """0 baru, 1 jalan, 2 siap, 3 selesai, 4 terkunci."""
        if st.get("kode") is not None:
            return st["kode"]
        q = G.QUEST[qid]
        if pemain.level < q["lv"]:
            return 4
        if qid in G.QUEST_RANTAI:
            idx = G.QUEST_RANTAI.index(qid)
            if idx > 0:
                prev_st = pemain.quest.get(G.QUEST_RANTAI[idx - 1], {})
                if prev_st.get("kode") != 3:
                    return 4
        return 0

    def quest_update_progres(self, pemain, jenis, sasaran, jumlah=1):
        """Dipanggil saat mob mati (jenis 0) atau item diambil (jenis 1)."""
        naik = []
        for qid, st in list(pemain.quest.items()):
            if st.get("kode") != 1:
                continue
            q = G.QUEST.get(qid)
            if not q or q["jenis"] != jenis or q["sasaran"] != sasaran:
                continue
            st["progres"] = min(st["progres"] + jumlah, q["butuh"])
            if st["progres"] >= q["butuh"]:
                st["kode"] = 2
            naik.append(qid)
        return naik

    def _dekat_npc(self, pemain, jenis):
        info = G.MAP.get(pemain.map_id, {})
        for nx, _, nj in info.get("npc", []):
            if nj == jenis and abs(int(pemain.x) - nx) <= 90:
                return True
        return False

    def naik_skill(self, pemain, skill_id):
        if pemain.poin < 1:
            return "tidak ada poin skill"
        s = G.SKILL.get(skill_id)
        if s is None:
            return "skill tidak ada"
        if s["job"] != pemain.job:
            return "skill bukan untuk job kamu"
        kunci = str(skill_id)
        lv = pemain.skill.get(kunci, 0)
        if lv >= G.SKILL_LEVEL_MAKS:
            return "skill sudah maksimal"
        pemain.skill[kunci] = lv + 1
        pemain.poin -= 1
        return None

    # ------------------------------------------------------------ party
    def party_ajak(self, pemain, target_eid):
        peta = self.peta[pemain.map_id]
        target = peta.pemain.get(target_eid)
        if target is None:
            return "pemain tidak ada di sini", None
        if pemain.eid == target.eid:
            return "tidak bisa mengajak diri sendiri", None
        return None, target

    # ------------------------------------------------------------ trade
    def _trade_id(self):
        self._trade_counter += 1
        return self._trade_counter

    def trade_ajak(self, pemain, target_eid):
        if pemain.trade:
            return "kamu sedang berdagang", None
        peta = self.peta[pemain.map_id]
        target = peta.pemain.get(target_eid)
        if target is None:
            return "pemain tidak ada", None
        if not pemain.hidup:
            return "tidak bisa berdagang sambil tumbang", None
        if target.trade:
            return "dia sedang berdagang", None
        t = Trade(self._trade_id(), pemain, target)
        pemain.trade = t
        target.trade = t
        self.catat("trade_ajak", pemain.nama, target.nama)
        return None, t

    def trade_terima(self, pemain):
        t = pemain.trade
        if t is None:
            return "tidak ada ajakan dagang", None
        if t.aktif:
            return "dagang sudah dimulai", None
        t.aktif = True
        self.catat("trade_mulai", t.a.nama, t.b.nama)
        return None, t

    def trade_batal(self, pemain, alasan="dibatalkan"):
        t = pemain.trade
        if t is None:
            return
        t.a.trade = None
        t.b.trade = None
        self.catat("trade_batal", t.a.nama, t.b.nama, alasan)

    def trade_tawar(self, pemain, gold, daftar):
        """daftar = [(slot, jumlah)]. Setiap perubahan membuka kunci kedua
        pihak supaya tidak ada manipulasi di detik terakhir."""
        t = pemain.trade
        if t is None or not t.aktif:
            return "tidak sedang berdagang", None
        if gold < 0 or gold > G.TRADE_GOLD_MAKS:
            return "jumlah gold tidak masuk akal", None
        if gold > pemain.gold:
            return "gold kamu tidak cukup", None
        if len(daftar) > G.TRADE_SLOT_MAKS:
            return "terlalu banyak barang", None
        for slot, jumlah in daftar:
            it = pemain.inv.get(slot)
            if not it or jumlah < 1 or it["jumlah"] < jumlah:
                return "slot tas tidak valid", None
        t.tawar[pemain.char_id] = {"gold": gold, "item": daftar}
        t.kunci[t.a.char_id] = False
        t.kunci[t.b.char_id] = False
        return None, t

    def trade_kunci(self, pemain):
        t = pemain.trade
        if t is None or not t.aktif:
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
            gold_masuk = t.tawar[pengirim.char_id]["gold"]
            pajak = max(0, gold_masuk * G.TRADE_PAJAK_PERSEN // 100)
            penerima.gold += gold_masuk - pajak
        self.catat("trade_sukses", a.nama, b.nama,
                   "%dg" % t.tawar[a.char_id]["gold"],
                   "%dg" % t.tawar[b.char_id]["gold"],
                   "pajak=%d%%" % G.TRADE_PAJAK_PERSEN)
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
                        pemain.hp = pemain.hp_maks
                        pemain.mp = pemain.mp_maks
                        peristiwa.append(("hidup_lagi", peta.map_id, pemain))
                    continue
                regen_hp = 1 + pemain.level // 8
                regen_mp = 1 + pemain.level // 12
                pemain.hp = min(pemain.hp_maks, pemain.hp + regen_hp)
                pemain.mp = min(pemain.mp_maks, pemain.mp + regen_mp)
        # periksa war
        peristiwa += self._cek_war(skr)
        return peristiwa

    def _ai_mob(self, peta, mob, skr, peristiwa):
        # cari target terdekat
        target = None
        jarak_t = G.AGGRO_RANGE
        if mob.target_eid:
            target = peta.pemain.get(mob.target_eid)
            if target and (not target.hidup
                           or abs(int(target.x) - int(mob.x)) > G.VIEW_RANGE):
                target = None
                mob.target_eid = None
        if target is None:
            for p in peta.pemain.values():
                if not p.hidup:
                    continue
                d = abs(int(p.x) - int(mob.x))
                if d < jarak_t:
                    jarak_t = d
                    target = p
            if target:
                mob.target_eid = target.eid
        if target is None:
            return
        # gerak
        dx = int(target.x) - int(mob.x)
        if abs(dx) > G.ATTACK_RANGE_MELEE:
            mob.arah = 1 if dx > 0 else -1
            mob.x = max(0, min(G.LEBAR_MAP,
                               mob.x + mob.arah * G.WALK_SPEED))
            peristiwa.append(("mob_gerak", peta.map_id, mob))
        # serang
        if (abs(dx) <= G.ATTACK_RANGE_MELEE
                and skr - mob.terakhir_serang >= 1200):
            mob.terakhir_serang = skr
            dmg = self._damage(mob.info["atk"], target.dfn, self.rng)
            target.hp = max(0, target.hp - dmg)
            peristiwa.append(("mob_serang", peta.map_id, mob, target, dmg))
            if target.hp == 0 and target.hidup:
                target.hidup = False
                target.mati_pada = skr
                hilang = target.gold // 20
                target.gold = max(0, target.gold - hilang)
                peristiwa.append(("pemain_mati", peta.map_id, target, hilang))

    # ------------------------------------------------------------ guild
    def guild_buat(self, pemain, nama, con=None):
        import db as DB
        nama = nama.strip()
        if len(nama) < G.GUILD_NAMA_MIN or len(nama) > G.GUILD_NAMA_MAKS:
            return "nama guild %d-%d karakter" % (
                G.GUILD_NAMA_MIN, G.GUILD_NAMA_MAKS), None
        if pemain.guild_id:
            return "kamu sudah punya guild", None
        if pemain.gold < G.GUILD_BIAYA_BUAT:
            return "biaya buat guild %d gold" % G.GUILD_BIAYA_BUAT, None
        if con:
            cek = con.execute("SELECT id FROM guild WHERE nama = ? COLLATE NOCASE",
                              (nama,)).fetchone()
            if cek:
                return "nama guild sudah dipakai", None
            pemain.gold -= G.GUILD_BIAYA_BUAT
            gid = DB.guild_buat(con, nama, pemain.char_id, pemain.nama)
            baris = DB.guild_satu(con, gid)
            g = GuildData(baris)
            g.anggota[pemain.char_id] = {
                "nama": pemain.nama, "pangkat": G.P_KETUA, "online": True
            }
            self.guild[gid] = g
            pemain.guild_id = gid
            pemain.guild_pangkat = G.P_KETUA
            self.catat("guild_buat", pemain.nama, nama)
            return None, g
        return "koneksi DB tidak tersedia", None

    def guild_undang(self, pemain, target_eid):
        g = self.guild_pemain(pemain)
        if g is None:
            return "kamu tidak punya guild", None
        if pemain.guild_pangkat < G.P_PERWIRA:
            return "hanya perwira/ketua yang bisa mengundang", None
        peta = self.peta[pemain.map_id]
        target = peta.pemain.get(target_eid)
        if target is None:
            return "pemain tidak ada di sini", None
        if target.guild_id:
            return "dia sudah punya guild", None
        if len(g.anggota) >= G.guild_anggota_maks(g.level):
            return "guild sudah penuh", None
        return None, (g, target)

    def guild_terima_undangan(self, pemain, gid, con=None):
        import db as DB
        g = self.guild.get(gid)
        if g is None:
            return "guild tidak ada"
        if pemain.guild_id:
            return "kamu sudah punya guild"
        if len(g.anggota) >= G.guild_anggota_maks(g.level):
            return "guild sudah penuh"
        pemain.guild_id = gid
        pemain.guild_pangkat = G.P_ANGGOTA
        g.anggota[pemain.char_id] = {
            "nama": pemain.nama, "pangkat": G.P_ANGGOTA, "online": True
        }
        g.kotor = True
        if con:
            DB.guild_tambah_anggota(con, gid, pemain.char_id,
                                    pemain.nama, G.P_ANGGOTA)
        self.catat("guild_terima", pemain.nama, g.nama)
        return None

    def guild_keluar(self, pemain, con=None):
        import db as DB
        g = self.guild_pemain(pemain)
        if g is None:
            return "kamu tidak punya guild"
        if pemain.guild_pangkat == G.P_KETUA:
            return "ketua harus bubarkan guild dulu"
        g.anggota.pop(pemain.char_id, None)
        pemain.guild_id = None
        pemain.guild_pangkat = G.P_ANGGOTA
        g.kotor = True
        if con:
            DB.guild_hapus_anggota(con, pemain.char_id)
        self.catat("guild_keluar", pemain.nama, g.nama)
        return None

    def guild_tendang(self, pemain, target_char_id, con=None):
        import db as DB
        g = self.guild_pemain(pemain)
        if g is None or pemain.guild_pangkat < G.P_PERWIRA:
            return "tidak punya wewenang"
        angg = g.anggota.get(target_char_id)
        if angg is None:
            return "bukan anggota guild"
        if angg["pangkat"] >= pemain.guild_pangkat:
            return "tidak bisa menendang yang pangkatnya sama atau lebih tinggi"
        target = self.pemain_by_char.get(target_char_id)
        if target:
            target.guild_id = None
            target.guild_pangkat = G.P_ANGGOTA
        g.anggota.pop(target_char_id, None)
        g.kotor = True
        if con:
            DB.guild_hapus_anggota(con, target_char_id)
        self.catat("guild_tendang", pemain.nama, angg["nama"])
        return None

    def guild_sumbang(self, pemain, jumlah, con=None):
        import db as DB
        g = self.guild_pemain(pemain)
        if g is None:
            return "kamu tidak punya guild", 0
        jumlah = max(G.GUILD_SUMBANG_MIN, int(jumlah))
        if pemain.gold < jumlah:
            return "gold kurang", 0
        pemain.gold -= jumlah
        g.kas += jumlah
        exp_dapat = jumlah * G.GUILD_EXP_PER_GOLD
        g.exp += exp_dapat
        # naik level guild
        while True:
            butuh = G.guild_exp_naik(g.level)
            if butuh <= 0 or g.exp < butuh:
                break
            g.exp -= butuh
            g.level += 1
        g.kotor = True
        if con:
            DB.guild_update(con, g.gid, g.level, g.exp, g.kas)
        self.catat("guild_sumbang", pemain.nama, str(jumlah))
        return None, exp_dapat

    def guild_bubar(self, pemain, con=None):
        import db as DB
        g = self.guild_pemain(pemain)
        if g is None:
            return "kamu tidak punya guild"
        if pemain.guild_pangkat != G.P_KETUA:
            return "hanya ketua yang bisa membubarkan guild"
        # online anggota dikeluarkan
        for char_id in list(g.anggota.keys()):
            p = self.pemain_by_char.get(char_id)
            if p:
                p.guild_id = None
                p.guild_pangkat = G.P_ANGGOTA
        if con:
            DB.guild_hapus(con, g.gid)
        del self.guild[g.gid]
        self.catat("guild_bubar", pemain.nama, g.nama)
        return None

    # ------------------------------------------------------------ war
    def war_deklarasi(self, pemain, nama_lawan, taruhan):
        g = self.guild_pemain(pemain)
        if g is None:
            return "kamu tidak punya guild", None
        if pemain.guild_pangkat != G.P_KETUA:
            return "hanya ketua yang bisa deklarasi perang", None
        if g.level < G.WAR_LEVEL_MIN:
            return "guild harus level %d" % G.WAR_LEVEL_MIN, None
        taruhan = int(taruhan)
        if not (G.WAR_TARUHAN_MIN <= taruhan <= G.WAR_TARUHAN_MAKS):
            return "taruhan %d-%d" % (G.WAR_TARUHAN_MIN, G.WAR_TARUHAN_MAKS), None
        if g.kas < taruhan:
            return "kas guild tidak cukup", None
        # cari guild lawan
        lawan = next((x for x in self.guild.values()
                      if x.nama.lower() == nama_lawan.lower()), None)
        if lawan is None:
            return "guild '%s' tidak ditemukan" % nama_lawan, None
        if lawan.gid == g.gid:
            return "tidak bisa perang dengan guild sendiri", None
        if g.war_id or lawan.war_id:
            return "salah satu guild sedang dalam perang", None
        return None, (g, lawan, taruhan)

    def war_terima(self, pemain, wid):
        w = self._war.get(wid)
        if w is None:
            return "tantangan perang tidak ada"
        g = self.guild_pemain(pemain)
        if g is None or g.gid != w.guild_b.gid:
            return "bukan untukmu"
        if pemain.guild_pangkat != G.P_KETUA:
            return "hanya ketua yang bisa"
        w.guild_a.kas -= w.taruhan
        w.guild_b.kas -= w.taruhan
        w.guild_a.kotor = True
        w.guild_b.kotor = True
        w.guild_a.war_id = wid
        w.guild_b.war_id = wid
        self.catat("war_mulai", w.guild_a.nama, w.guild_b.nama)
        return None

    def war_ajukan(self, g_ajak, g_lawan, taruhan):
        self._war_counter += 1
        wid = self._war_counter
        w = WarData(wid, g_ajak, g_lawan, taruhan, sekarang())
        self._war[wid] = w
        return wid, w

    def war_bunuh(self, pemain, mob_level):
        g = self.guild_pemain(pemain)
        if g is None or g.war_id is None:
            return
        w = self._war.get(g.war_id)
        if w is None:
            return
        w.skor[g.gid] = w.skor.get(g.gid, 0) + G.war_skor_mob(mob_level)

    def _cek_war(self, skr):
        peristiwa = []
        for wid, w in list(self._war.items()):
            if skr >= w.selesai:
                hasil = self._selesaikan_war(w)
                del self._war[wid]
                peristiwa.append(("war_selesai", wid, hasil))
        return peristiwa

    def _selesaikan_war(self, w):
        sa = w.skor.get(w.guild_a.gid, 0)
        sb = w.skor.get(w.guild_b.gid, 0)
        seri = sa == sb
        if seri:
            menang = None
            kalah = None
            w.guild_a.kas += w.taruhan
            w.guild_b.kas += w.taruhan
            hadiah_kas = w.taruhan
        else:
            if sa > sb:
                menang, kalah = w.guild_a, w.guild_b
            else:
                menang, kalah = w.guild_b, w.guild_a
            menang.kas += w.taruhan * 2
            menang.menang += 1
            kalah.kalah += 1
            hadiah_kas = w.taruhan * 2
        for g in (w.guild_a, w.guild_b):
            g.war_id = None
            g.kotor = True
        w.guild_a.exp += G.WAR_EXP_MENANG if (not seri and menang == w.guild_a) \
            else G.WAR_EXP_KALAH
        w.guild_b.exp += G.WAR_EXP_MENANG if (not seri and menang == w.guild_b) \
            else G.WAR_EXP_KALAH
        return {
            "menang": menang.nama if menang else None,
            "menang_id": menang.gid if menang else None,
            "kalah_id": kalah.gid if kalah else None,
            "skor_a": sa, "skor_b": sb,
            "hadiah_kas": hadiah_kas,
            "seri": seri,
        }

    def catat(self, *args):
        pass  # di-override atau diganti DB.catat di app.py
