#!/usr/bin/env python3
"""Data statis game WIRA NUSA.

Semua angka balancing ada di sini supaya mudah disetel tanpa harus
memburu kode tersebar. Gunakan G.SESUATU di seluruh kode server;
jangan tulis literal magic number di world.py / app.py.
"""

import hashlib
import os

sys_path_insert = None  # diimpor di world.py

# ------------------------------------------------------------------ umum
TICK_HZ = 10          # tick per detik
TICK_MS = 100         # ms per tick
GRAVITY = 3           # piksel/tick ke bawah
JUMP_V = 22
WALK_SPEED = 6        # piksel/tick horizontal
RUN_TOLERANCE = 3     # faktor toleransi kecepatan anti-speedhack

# ------------------------------------------------------------------ peta
LEBAR_MAP = 1600
TANAH_Y = 200

# ------------------------------------------------------------------ tempur
ATTACK_RANGE_MELEE = 34
ATTACK_RANGE_RANGED = 150
RESPAWN_MOB_MS = 8000
RESPAWN_PLAYER_MS = 5000
DROP_UMUR_MS = 60000
AGGRO_RANGE = 120

# ------------------------------------------------------------------ pemain
INVENTORI_MAKS = 40
EQUIP_SLOT = 8
PARTY_MAKS = 5
PARTY_BAGI_EXP = 130    # persen exp dibagi ke party (lebih dari 100 = bonus)
VIEW_RANGE = 420

LEVEL_MAKS = 60
SKILL_LEVEL_MAKS = 5
SKILL_KENAIKAN = 18      # poin skill per level

# ----------------------------------------------------------------- trade
TRADE_JARAK = 120        # piksel, dua pemain harus berdekatan
TRADE_SLOT_MAKS = 6      # item per sisi dalam satu transaksi
TRADE_GOLD_MAKS = 2000000000
TRADE_PAJAK_PERSEN = 3        # % pajak dari gold yang berpindah tangan


# ------------------------------------------------- fitur sosial (v1.2)
# Guild, war antar guild, mail, dan lelang. Dipisah supaya file ini tidak
# kebablasan panjang.
from gamedata_sosial import (
    GUILD_BIAYA_BUAT, GUILD_LEVEL_MAKS, GUILD_NAMA_MIN, GUILD_NAMA_MAKS,
    GUILD_ANGGOTA_MAKS, GUILD_EXP_NAIK, GUILD_EXP_PER_GOLD, GUILD_SUMBANG_MIN,
    P_ANGGOTA, P_PERWIRA, P_KETUA, NAMA_PANGKAT,
    GUILD_BONUS_EXP, GUILD_BONUS_GOLD,
    guild_anggota_maks, guild_exp_naik, guild_bonus,
    WAR_DURASI_MS, WAR_COOLDOWN_MS, WAR_LEVEL_MIN,
    WAR_TARUHAN_MIN, WAR_TARUHAN_MAKS,
    WAR_SKOR_MOB, WAR_SKOR_PER_LEVEL, WAR_EXP_MENANG, WAR_EXP_KALAH,
    war_skor_mob,
    MAIL_KOTAK_MAKS, MAIL_BIAYA_KIRIM, MAIL_LAMPIRAN_MAKS,
    MAIL_GOLD_MAKS, MAIL_UMUR_HARI, MAIL_JUDUL_MAKS, MAIL_ISI_MAKS,
    LELANG_MAKS_PER_PEMAIN, LELANG_DURASI_JAM, LELANG_BIAYA_PERSEN,
    LELANG_HARGA_MIN, LELANG_HARGA_MAKS, LELANG_HALAMAN,
    lelang_potongan, validasi_sosial,
)

# ------------------------------------------------------------------ job
# 0 Pedang, 1 Sepasang, 2 Dukun, 3 Senapan
JOB = {0: "Pedang", 1: "Sepasang", 2: "Dukun", 3: "Senapan"}
JOB_NAMA = list(JOB.values())

# ----------------------------------------------------------------- skill
# id skill:
#   1xx = Pedang: 101 tebas, 102 hantam area, 103 amuk
#   1xx = Sepasang: 11 tikam, 12 badai pisau, 13 serangan kilat
#   2xx = Dukun: 21 pukul staf, 22 sihir api, 23 sembuh
#   3xx = Senapan: 31 tembak, 32 tembak cepat, 33 granat
SKILL = {
    # Pedang
    101: {"nama": "Tebas", "job": 0, "tipe": 1, "daya": 120, "mp": 5, "jarak": 50},
    102: {"nama": "Hantam Area", "job": 0, "tipe": 1, "daya": 80, "mp": 12,
          "jarak": 70, "area": 100},
    103: {"nama": "Amuk", "job": 0, "tipe": 3, "daya": 0, "mp": 20,
          "efek": "atk+30%", "durasi": 50},
    # Sepasang
    11:  {"nama": "Tikam", "job": 1, "tipe": 1, "daya": 110, "mp": 4, "jarak": 40},
    12:  {"nama": "Badai Pisau", "job": 1, "tipe": 1, "daya": 70, "mp": 14,
          "jarak": 60, "area": 80},
    13:  {"nama": "Serangan Kilat", "job": 1, "tipe": 1, "daya": 150, "mp": 22,
          "jarak": 45},
    # Dukun
    21:  {"nama": "Pukul Staf", "job": 2, "tipe": 1, "daya": 90, "mp": 3, "jarak": 38},
    22:  {"nama": "Sihir Api", "job": 2, "tipe": 1, "daya": 130, "mp": 18,
          "jarak": ATTACK_RANGE_RANGED},
    23:  {"nama": "Sembuh", "job": 2, "tipe": 2, "daya": 80, "mp": 15, "jarak": 0},
    # Senapan
    31:  {"nama": "Tembak", "job": 3, "tipe": 1, "daya": 115, "mp": 6,
          "jarak": ATTACK_RANGE_RANGED},
    32:  {"nama": "Tembak Cepat", "job": 3, "tipe": 1, "daya": 85, "mp": 10,
          "jarak": ATTACK_RANGE_RANGED},
    33:  {"nama": "Granat", "job": 3, "tipe": 1, "daya": 100, "mp": 20,
          "jarak": ATTACK_RANGE_RANGED, "area": 90},
}
SKILL_JOB = {0: [101, 102, 103], 1: [11, 12, 13],
             2: [21, 22, 23], 3: [31, 32, 33]}


def skill_daya_total(skill_id, skill_level, atk):
    """Damage/heal efektif skill berdasar level skill dan atk pemain."""
    s = SKILL.get(skill_id, {})
    base = s.get("daya", 100)
    return int(atk * (base + (skill_level - 1) * 15) // 100)


# ----------------------------------------------------------------- item
# id: 1xx potion, 2xx senjata, 3xx baju, 4xx topi, 5xx aksesori, 6xx material
# slot equip: 0 senjata, 1 baju, 2 topi, 3 sayap, 4-7 cincin/amulet
ITEM = {
    # potion
    100: {"nama": "Potion HP Kecil", "jenis": "potion", "hp": 100, "harga": 50},
    101: {"nama": "Potion HP Sedang", "jenis": "potion", "hp": 300, "harga": 150},
    102: {"nama": "Potion MP", "jenis": "potion", "mp": 80, "harga": 80},
    # senjata (slot 0) — tiap job punya 3 tier
    200: {"nama": "Pedang Besi", "jenis": "senjata", "job": 0, "slot": 0,
          "atk": 18, "harga": 500},
    201: {"nama": "Pedang Baja", "jenis": "senjata", "job": 0, "slot": 0,
          "atk": 32, "harga": 1800},
    202: {"nama": "Pedang Rune", "jenis": "senjata", "job": 0, "slot": 0,
          "atk": 52, "harga": 5000},
    210: {"nama": "Pisau Ganda", "jenis": "senjata", "job": 1, "slot": 0,
          "atk": 14, "harga": 450},
    211: {"nama": "Kujang Ganda", "jenis": "senjata", "job": 1, "slot": 0,
          "atk": 28, "harga": 1600},
    212: {"nama": "Kris Sakti", "jenis": "senjata", "job": 1, "slot": 0,
          "atk": 46, "harga": 4500},
    220: {"nama": "Tongkat Kayu", "jenis": "senjata", "job": 2, "slot": 0,
          "atk": 12, "harga": 400},
    221: {"nama": "Tongkat Giok", "jenis": "senjata", "job": 2, "slot": 0,
          "atk": 24, "harga": 1400},
    222: {"nama": "Staf Naga", "jenis": "senjata", "job": 2, "slot": 0,
          "atk": 42, "harga": 4200},
    230: {"nama": "Senapan Bambu", "jenis": "senjata", "job": 3, "slot": 0,
          "atk": 16, "harga": 480},
    231: {"nama": "Senapan Besi", "jenis": "senjata", "job": 3, "slot": 0,
          "atk": 30, "harga": 1700},
    232: {"nama": "Meriam Tangan", "jenis": "senjata", "job": 3, "slot": 0,
          "atk": 50, "harga": 4800},
    # baju (slot 1)
    300: {"nama": "Baju Kulit", "jenis": "baju", "slot": 1, "dfn": 10, "harga": 400},
    301: {"nama": "Baju Besi", "jenis": "baju", "slot": 1, "dfn": 22, "harga": 1500},
    302: {"nama": "Zirah Rune", "jenis": "baju", "slot": 1, "dfn": 40, "harga": 4500},
    # topi (slot 2)
    400: {"nama": "Ikat Kepala", "jenis": "topi", "slot": 2, "dfn": 4, "harga": 200},
    401: {"nama": "Helm Besi", "jenis": "topi", "slot": 2, "dfn": 12, "harga": 800},
    402: {"nama": "Mahkota Rune", "jenis": "topi", "slot": 2, "dfn": 24, "harga": 3000},
    # sayap (slot 3)
    500: {"nama": "Sayap Kain", "jenis": "sayap", "slot": 3, "dfn": 2, "harga": 600},
    501: {"nama": "Sayap Emas", "jenis": "sayap", "slot": 3, "dfn": 6, "harga": 2500},
    502: {"nama": "Sayap Naga", "jenis": "sayap", "slot": 3, "dfn": 14, "harga": 8000},
    # material
    600: {"nama": "Batu Tempa", "jenis": "material", "harga": 200},
    601: {"nama": "Batu Upgrade", "jenis": "material", "harga": 500},
    602: {"nama": "Kristal Merah", "jenis": "material", "harga": 1000},
    603: {"nama": "Sisik Naga", "jenis": "material", "harga": 2000},
}


def item_atk(item_id, plus=0):
    info = ITEM.get(item_id, {})
    base = info.get("atk", 0)
    return base + plus * 3


def item_dfn(item_id, plus=0):
    info = ITEM.get(item_id, {})
    base = info.get("dfn", 0)
    return base + plus * 2


# ------------------------------------------------------------------ mob
MOB = {
    1: {"nama": "Celeng", "lv": 5, "hp": 120, "atk": 12, "dfn": 5,
        "exp": 30, "gold": 15, "drop": [(100, 20), (600, 10)]},
    2: {"nama": "Kunti", "lv": 15, "hp": 380, "atk": 28, "dfn": 12,
        "exp": 120, "gold": 60, "drop": [(101, 15), (600, 12), (601, 5)]},
    3: {"nama": "Genderuwo", "lv": 28, "hp": 900, "atk": 52, "dfn": 22,
        "exp": 320, "gold": 150, "drop": [(101, 10), (601, 8), (602, 4)]},
    4: {"nama": "Buto", "lv": 42, "hp": 2200, "atk": 88, "dfn": 38,
        "exp": 800, "gold": 380, "drop": [(102, 12), (602, 6), (603, 3)]},
    5: {"nama": "Naga Kawah", "lv": 55, "hp": 8000, "atk": 160, "dfn": 60,
        "exp": 3000, "gold": 1200, "drop": [(102, 15), (603, 8), (502, 2)]},
}

# ------------------------------------------------------------------ map
MAP = {
    1: {
        "nama": "Desa Ambar", "tema": 0, "aman": True,
        "mob": [],
        "portal": [{"x": 1400, "ke": 2, "tujuan_x": 200}],
        "npc": [(600, "Pak Tua", "quest"), (900, "Pedagang", "toko"),
                (1100, "Pandai Besi", "quest")],
        "toko": [100, 101, 102, 200, 210, 220, 230, 300, 400, 600, 601],
    },
    2: {
        "nama": "Hutan Larik", "tema": 1, "aman": False,
        "mob": [(1, 6), (2, 3)],
        "portal": [{"x": 100, "ke": 1, "tujuan_x": 1200},
                   {"x": 1450, "ke": 3, "tujuan_x": 200}],
        "npc": [(800, "Pemburu", "quest")],
        "toko": [],
    },
    3: {
        "nama": "Gurun Gurat", "tema": 2, "aman": False,
        "mob": [(2, 4), (3, 3)],
        "portal": [{"x": 100, "ke": 2, "tujuan_x": 1300},
                   {"x": 1450, "ke": 4, "tujuan_x": 200}],
        "npc": [(700, "Pedagang Gurun", "quest")],
        "toko": [],
    },
    4: {
        "nama": "Kawah Lebur", "tema": 3, "aman": False,
        "mob": [(3, 3), (4, 2), (5, 1)],
        "portal": [{"x": 100, "ke": 3, "tujuan_x": 1300}],
        "npc": [],
        "toko": [],
    },
}

SPAWN_MAP = 1
SPAWN_X = 400

# ------------------------------------------------------------------ exp
_BASE_EXP = 80
_FAKTOR = 1.18


def exp_untuk(level):
    """Exp yang dibutuhkan untuk naik dari level ke level+1.
    Mengembalikan 0 bila level >= LEVEL_MAKS."""
    if level >= LEVEL_MAKS:
        return 0
    return int(_BASE_EXP * (_FAKTOR ** (level - 1)))


def stat_dasar(level, job):
    """Stat dasar (hp_maks, mp_maks, atk, dfn) berdasar level dan job."""
    lv = max(1, int(level))
    if job == 0:    # Pedang: atk tinggi, dfn sedang
        return (lv * 22 + 80, lv * 8 + 40, lv * 4 + 10, lv * 2 + 5)
    elif job == 1:  # Sepasang: atk tertinggi, dfn rendah
        return (lv * 18 + 70, lv * 8 + 40, lv * 5 + 10, lv * 1 + 4)
    elif job == 2:  # Dukun: mp tinggi, atk sedang
        return (lv * 16 + 60, lv * 14 + 60, lv * 3 + 8, lv * 2 + 5)
    else:           # Senapan: jangkauan jauh, stat sedang
        return (lv * 20 + 75, lv * 10 + 45, lv * 4 + 9, lv * 2 + 4)


# ----------------------------------------------------------------- quest
QUEST = {
    # rantai cerita Pak Tua (lv 1-40)
    1:  {"nama": "Awal Mula", "lv": 1, "jenis": 0,
         "sasaran": 1, "butuh": 5,
         "hadiah_exp": 200, "hadiah_gold": 100,
         "npc": (1, 0),
         "mulai": "Bunuh 5 Celeng yang meresahkan desa.",
         "jalan": "Sudah bunuh {p}/{b} Celeng.",
         "selesai": "Terima kasih, nak."},
    2:  {"nama": "Jejak Kunti", "lv": 8, "jenis": 0,
         "sasaran": 2, "butuh": 3,
         "hadiah_exp": 600, "hadiah_gold": 300,
         "npc": (1, 0),
         "mulai": "Bunuh 3 Kunti di Hutan Larik.",
         "jalan": "Sudah bunuh {p}/{b} Kunti.",
         "selesai": "Bagus sekali!"},
    3:  {"nama": "Bahan Tempa", "lv": 10, "jenis": 1,
         "sasaran": 600, "butuh": 10,
         "hadiah_exp": 500, "hadiah_gold": 200,
         "npc": (1, 0),
         "mulai": "Bawa 10 Batu Tempa ke sini.",
         "jalan": "Sudah kumpul {p}/{b} Batu Tempa.",
         "selesai": "Pas untuk tempaku."},
    4:  {"nama": "Genderuwo Jahat", "lv": 20, "jenis": 0,
         "sasaran": 3, "butuh": 5,
         "hadiah_exp": 2000, "hadiah_gold": 800,
         "npc": (1, 0),
         "mulai": "Basmi 5 Genderuwo di Gurun Gurat.",
         "jalan": "Sudah bunuh {p}/{b} Genderuwo.",
         "selesai": "Kampung kita aman sekarang."},
    5:  {"nama": "Buto Raksasa", "lv": 35, "jenis": 0,
         "sasaran": 4, "butuh": 3,
         "hadiah_exp": 6000, "hadiah_gold": 2500,
         "npc": (1, 0),
         "mulai": "Kalahkan 3 Buto di Kawah Lebur.",
         "jalan": "Sudah bunuh {p}/{b} Buto.",
         "selesai": "Prajurit sejati!"},
    6:  {"nama": "Naga Penjaga", "lv": 50, "jenis": 2,
         "sasaran": 0, "butuh": 1,
         "hadiah_exp": 20000, "hadiah_gold": 8000,
         "npc": (1, 0),
         "mulai": "Temui Pak Tua lagi setelah kalahkan Naga Kawah.",
         "jalan": "Naga Kawah menanti di Kawah Lebur.",
         "selesai": "Legenda hidup!"},
    # quest setoran berulang dari Pedagang
    10: {"nama": "Pasokan Potion", "lv": 1, "jenis": 1,
         "sasaran": 100, "butuh": 5,
         "hadiah_exp": 100, "hadiah_gold": 250,
         "npc": (1, 1),
         "mulai": "Bawa 5 Potion HP Kecil.",
         "jalan": "Sudah bawa {p}/{b}.",
         "selesai": "Stok terjaga."},
    11: {"nama": "Sisik untuk Kain", "lv": 40, "jenis": 1,
         "sasaran": 603, "butuh": 3,
         "hadiah_exp": 3000, "hadiah_gold": 1500,
         "npc": (1, 1),
         "mulai": "Bawa 3 Sisik Naga.",
         "jalan": "Sudah bawa {p}/{b}.",
         "selesai": "Bahan langka sekali."},
    # quest hadiah senjata dari Pandai Besi
    20: {"nama": "Uji Pandai Besi", "lv": 15, "jenis": 1,
         "sasaran": 601, "butuh": 5,
         "hadiah_exp": 800, "hadiah_gold": 0,
         "hadiah_item": True,
         "npc": (1, 2),
         "mulai": "Bawa 5 Batu Upgrade, kubuat senjata tier 2.",
         "jalan": "Sudah bawa {p}/{b}.",
         "selesai": "Senjata baru untukmu!"},
    21: {"nama": "Tantangan Maha", "lv": 40, "jenis": 1,
         "sasaran": 603, "butuh": 5,
         "hadiah_exp": 5000, "hadiah_gold": 0,
         "hadiah_item": True,
         "npc": (1, 2),
         "mulai": "Bawa 5 Sisik Naga, kubuat senjata terkuat.",
         "jalan": "Sudah bawa {p}/{b}.",
         "selesai": "Senjata legenda!"},
}
QUEST_RANTAI = [1, 2, 3, 4, 5, 6]
QUEST_ULANG = [10, 11]


# ----------------------------------------------------------------- upgrade
def upgrade_peluang(plus_sekarang):
    """Probabilitas berhasil upgrade (0.0 - 1.0)."""
    tabel = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    i = max(0, min(plus_sekarang, len(tabel) - 1))
    return tabel[i]


# ---------------------------------------------------------------- validasi
def validasi():
    """Kembalikan daftar masalah konsistensi data. [] = aman."""
    masalah = []
    for sid, s in SKILL.items():
        if s["job"] not in JOB:
            masalah.append("skill %d: job tidak dikenal" % sid)
    for iid, it in ITEM.items():
        if "slot" in it and it["slot"] >= EQUIP_SLOT:
            masalah.append("item %d: slot equip %d >= %d" % (
                iid, it["slot"], EQUIP_SLOT))
    for mid, m in MOB.items():
        for did, pct in m["drop"]:
            if did not in ITEM:
                masalah.append("mob %d: drop item %d tidak ada" % (mid, did))
    for qid, q in QUEST.items():
        npc_map, npc_idx = q["npc"]
        if npc_map not in MAP:
            masalah.append("quest %d: map %d tidak ada" % (qid, npc_map))
        elif npc_idx >= len(MAP[npc_map]["npc"]):
            masalah.append("quest %d: npc idx %d tidak ada di map %d" % (
                qid, npc_idx, npc_map))
        if q["jenis"] == 1 and q["sasaran"] not in ITEM:
            masalah.append("quest %d: item sasaran %d tidak ada" % (
                qid, q["sasaran"]))
        if q["jenis"] == 0 and q["sasaran"] not in MOB:
            masalah.append("quest %d: mob sasaran %d tidak ada" % (
                qid, q["sasaran"]))
    masalah += validasi_sosial()
    return masalah
