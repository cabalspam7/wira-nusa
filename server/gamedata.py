#!/usr/bin/env python3
"""Data statis WIRA NUSA: job, skill, item, mob, map, drop table.

Semua angka balance ada di satu file supaya bisa diubah tanpa menyentuh
logika. Server ini otoritatif: client tidak pernah mengirim damage, cuma
niat ("gw serang target X pakai skill Y"), dan angka dihitung di sini.
"""

# ------------------------------------------------------------------ dunia

TICK_HZ = 10                 # tick server per detik
TICK_MS = 1000 // TICK_HZ
GRAVITY = 3                  # dipakai untuk validasi lompat
JUMP_V = 22
WALK_SPEED = 6               # piksel per tick, dipakai anti-speedhack
RUN_TOLERANCE = 3            # kelonggaran lag sebelum posisi dikoreksi
ATTACK_RANGE_MELEE = 34
ATTACK_RANGE_RANGED = 150
RESPAWN_MOB_MS = 8000
RESPAWN_PLAYER_MS = 5000
DROP_UMUR_MS = 60000
AGGRO_RANGE = 120
PARTY_MAKS = 5
PARTY_BAGI_EXP = 130         # persen total exp saat party (dibagi rata)
VIEW_RANGE = 420             # jarak broadcast entitas

# ------------------------------------------------------------------- job
# hp/mp/atk/def dasar di level 1, lalu pertumbuhan per level
JOB = {
    0: dict(nama="Pedang", hp=120, mp=30, atk=14, dfn=10,
            hp_up=18, mp_up=3, atk_up=3, dfn_up=2, jarak=ATTACK_RANGE_MELEE),
    1: dict(nama="Sepasang", hp=100, mp=40, atk=17, dfn=7,
            hp_up=14, mp_up=4, atk_up=4, dfn_up=1, jarak=ATTACK_RANGE_MELEE),
    2: dict(nama="Dukun", hp=80, mp=80, atk=11, dfn=5,
            hp_up=11, mp_up=9, atk_up=2, dfn_up=1, jarak=ATTACK_RANGE_RANGED),
    3: dict(nama="Senapan", hp=95, mp=50, atk=15, dfn=6,
            hp_up=13, mp_up=5, atk_up=3, dfn_up=1, jarak=ATTACK_RANGE_RANGED),
}

LEVEL_MAKS = 60


def exp_untuk(level):
    """Kurva exp: landai di awal, curam setelah 30."""
    if level >= LEVEL_MAKS:
        return 0
    return 40 + level * level * 14 + (level ** 3) // 3


def statistik_dasar(job, level):
    j = JOB[job]
    n = level - 1
    return dict(
        hp_maks=j["hp"] + j["hp_up"] * n,
        mp_maks=j["mp"] + j["mp_up"] * n,
        atk=j["atk"] + j["atk_up"] * n,
        dfn=j["dfn"] + j["dfn_up"] * n,
        jarak=j["jarak"],
    )


# ----------------------------------------------------------------- skill
# tipe: 0 damage target, 1 damage area, 2 sembuh, 3 buff sementara
SKILL = {
    # Pedang
    1: dict(job=0, nama="Tebas Ganda", tipe=0, mp=6, cd=1200, dmg=140, lv_min=1),
    2: dict(job=0, nama="Putaran Angin", tipe=1, mp=14, cd=4000, dmg=120,
            radius=70, lv_min=10),
    3: dict(job=0, nama="Kulit Baja", tipe=3, mp=18, cd=15000, durasi=8000,
            dfn_persen=60, lv_min=20),
    # Sepasang
    11: dict(job=1, nama="Sambar Kembar", tipe=0, mp=7, cd=1000, dmg=125, lv_min=1),
    12: dict(job=1, nama="Badai Bilah", tipe=1, mp=16, cd=4500, dmg=110,
             radius=60, lv_min=10),
    13: dict(job=1, nama="Langkah Bayang", tipe=3, mp=15, cd=12000, durasi=6000,
             atk_persen=45, lv_min=20),
    # Dukun
    21: dict(job=2, nama="Bola Api", tipe=0, mp=8, cd=1100, dmg=165, lv_min=1),
    22: dict(job=2, nama="Hujan Bara", tipe=1, mp=22, cd=5000, dmg=150,
             radius=90, lv_min=10),
    23: dict(job=2, nama="Pulih", tipe=2, mp=20, cd=6000, heal=180, lv_min=5),
    # Senapan
    31: dict(job=3, nama="Tembakan Tepat", tipe=0, mp=7, cd=900, dmg=150, lv_min=1),
    32: dict(job=3, nama="Rentetan", tipe=1, mp=18, cd=4200, dmg=115,
             radius=80, lv_min=10),
    33: dict(job=3, nama="Bidik", tipe=3, mp=14, cd=11000, durasi=7000,
             atk_persen=50, lv_min=20),
}

SKILL_LEVEL_MAKS = 5
SKILL_KENAIKAN = 18   # persen damage tambahan per level skill

# ------------------------------------------------------------------ item
# jenis: 0 consumable, 1 senjata, 2 baju, 3 topi, 4 sayap, 5 bahan
ITEM = {
    # consumable
    100: dict(nama="Ramuan Merah", jenis=0, harga=30, hp=80, tumpuk=99),
    101: dict(nama="Ramuan Biru", jenis=0, harga=40, mp=60, tumpuk=99),
    102: dict(nama="Batu Teleport", jenis=0, harga=120, teleport=1, tumpuk=20),
    # senjata per job, tier 0-2 (ikon w0/w1/w2)
    200: dict(nama="Pedang Kayu", jenis=1, job=0, tier=0, atk=6, lv=1, harga=80),
    201: dict(nama="Pedang Besi", jenis=1, job=0, tier=1, atk=22, lv=12, harga=900),
    202: dict(nama="Pedang Nusa", jenis=1, job=0, tier=2, atk=52, lv=30, harga=6400),
    210: dict(nama="Sepasang Belati", jenis=1, job=1, tier=0, atk=7, lv=1, harga=80),
    211: dict(nama="Sepasang Kilat", jenis=1, job=1, tier=1, atk=24, lv=12, harga=900),
    212: dict(nama="Sepasang Naga", jenis=1, job=1, tier=2, atk=55, lv=30, harga=6400),
    220: dict(nama="Tongkat Rotan", jenis=1, job=2, tier=0, atk=8, lv=1, harga=80),
    221: dict(nama="Tongkat Pusaka", jenis=1, job=2, tier=1, atk=26, lv=12, harga=900),
    222: dict(nama="Tongkat Lebur", jenis=1, job=2, tier=2, atk=60, lv=30, harga=6400),
    230: dict(nama="Senapan Sumpit", jenis=1, job=3, tier=0, atk=7, lv=1, harga=80),
    231: dict(nama="Senapan Baja", jenis=1, job=3, tier=1, atk=23, lv=12, harga=900),
    232: dict(nama="Senapan Petir", jenis=1, job=3, tier=2, atk=56, lv=30, harga=6400),
    # baju
    300: dict(nama="Baju Lurik", jenis=2, dfn=5, lv=1, harga=70),
    301: dict(nama="Baju Rantai", jenis=2, dfn=18, lv=12, harga=850),
    302: dict(nama="Baju Pusaka", jenis=2, dfn=44, lv=30, harga=6000),
    # topi
    400: dict(nama="Ikat Kepala", jenis=3, dfn=3, hp=20, lv=1, harga=60),
    401: dict(nama="Caping Baja", jenis=3, dfn=11, hp=60, lv=12, harga=700),
    402: dict(nama="Helm Wira", jenis=3, dfn=26, hp=180, lv=30, harga=5200),
    # sayap (kosmetik + stat kecil)
    500: dict(nama="Sayap Kapas", jenis=4, dfn=2, lv=10, harga=1500),
    501: dict(nama="Sayap Surya", jenis=4, dfn=6, atk=4, lv=25, harga=9000),
    502: dict(nama="Sayap Purba", jenis=4, dfn=12, atk=10, lv=40, harga=26000),
    # bahan
    600: dict(nama="Batu Tempa", jenis=5, harga=250, tumpuk=99),
    601: dict(nama="Kristal Wira", jenis=5, harga=900, tumpuk=99),
    602: dict(nama="Kayu Jati", jenis=5, harga=25, tumpuk=99),
    603: dict(nama="Bijih Besi", jenis=5, harga=45, tumpuk=99),
}

SLOT_EQUIP = {1: 0, 2: 1, 3: 2, 4: 3}   # jenis item -> slot equip
INVENTORI_MAKS = 30

# upgrade senjata/armor: +1..+9, peluang sukses turun, butuh Batu Tempa
UPGRADE_MAKS = 9
UPGRADE_PELUANG = [95, 90, 82, 72, 60, 48, 36, 25, 15]   # persen per level
UPGRADE_BATU = [1, 1, 2, 2, 3, 4, 5, 7, 9]
UPGRADE_BONUS = 12   # persen stat dasar per +1


def stat_upgrade(dasar, plus):
    return dasar + (dasar * UPGRADE_BONUS * plus) // 100


# ------------------------------------------------------------------- mob
MOB = {
    1: dict(nama="Celeng Liar", sprite="celeng", lv=2, hp=60, atk=8, dfn=2,
            exp=12, gold=8, jarak=30, w=20, h=16, speed=3),
    2: dict(nama="Kuntilanak", sprite="kunti", lv=8, hp=180, atk=20, dfn=6,
            exp=44, gold=26, jarak=34, w=18, h=26, speed=4),
    3: dict(nama="Genderuwo", sprite="genderuwo", lv=16, hp=520, atk=42, dfn=16,
            exp=140, gold=80, jarak=36, w=26, h=28, speed=3),
    4: dict(nama="Buto Ijo", sprite="buto", lv=28, hp=1500, atk=88, dfn=34,
            exp=420, gold=240, jarak=40, w=30, h=30, speed=3),
    5: dict(nama="Naga Kawah", sprite="naga", lv=40, hp=9000, atk=170, dfn=60,
            exp=3200, gold=2400, jarak=60, w=40, h=32, speed=2, boss=1),
}

# drop: (item_id, peluang per-10000, jumlah_min, jumlah_maks)
DROP = {
    1: [(100, 1800, 1, 2), (602, 2200, 1, 3), (200, 60, 1, 1), (210, 60, 1, 1)],
    2: [(100, 1500, 1, 3), (101, 1200, 1, 2), (603, 1800, 1, 3), (600, 220, 1, 1)],
    3: [(101, 1600, 2, 4), (600, 700, 1, 2), (201, 90, 1, 1), (301, 80, 1, 1),
        (401, 80, 1, 1)],
    4: [(600, 1400, 2, 4), (601, 260, 1, 1), (202, 45, 1, 1), (302, 45, 1, 1),
        (500, 120, 1, 1)],
    5: [(601, 6000, 3, 6), (502, 400, 1, 1), (202, 900, 1, 1), (222, 900, 1, 1),
        (232, 900, 1, 1), (212, 900, 1, 1)],
}

# ------------------------------------------------------------------- map
# lebar dunia dalam piksel, tema latar, tile, daftar spawn mob, portal
MAP = {
    1: dict(nama="Desa Ambar", tema="desa", tile="tanah", lebar=1600, tanah=200,
            aman=1,
            spawn=[],
            portal=[(1520, 2, 80)],
            npc=[(300, "Pak Tua", 0), (520, "Pedagang", 1), (700, "Pandai Besi", 2)]),
    2: dict(nama="Hutan Larik", tema="hutan", tile="tanah", lebar=2400, tanah=210,
            aman=0,
            spawn=[(1, 10), (2, 4)],
            portal=[(60, 1, 1440), (2320, 3, 90)],
            npc=[]),
    3: dict(nama="Gurun Gurat", tema="gurun", tile="pasir", lebar=2800, tanah=205,
            aman=0,
            spawn=[(2, 8), (3, 6)],
            portal=[(60, 2, 2240), (2720, 4, 100)],
            npc=[]),
    4: dict(nama="Kawah Lebur", tema="kawah", tile="lava", lebar=3200, tanah=215,
            aman=0,
            spawn=[(3, 6), (4, 6), (5, 1)],
            portal=[(60, 3, 2640)],
            npc=[]),
}

MAP_AWAL = 1
SPAWN_AWAL_X = 200

# toko NPC: daftar item yang dijual di desa
TOKO = [100, 101, 102, 200, 210, 220, 230, 300, 400, 600]

GOLD_AWAL = 300


def validasi():
    """Cek konsistensi data. Dipanggil saat start dan oleh selftest."""
    masalah = []
    for sid, s in SKILL.items():
        if s["job"] not in JOB:
            masalah.append("skill %d job tidak dikenal" % sid)
        if s["tipe"] == 1 and "radius" not in s:
            masalah.append("skill %d area tanpa radius" % sid)
        if s["tipe"] == 3 and "durasi" not in s:
            masalah.append("skill %d buff tanpa durasi" % sid)
    for iid, it in ITEM.items():
        if it["jenis"] == 1 and it.get("job") not in JOB:
            masalah.append("senjata %d tanpa job valid" % iid)
        if it["jenis"] == 1 and not 0 <= it.get("tier", -1) <= 2:
            masalah.append("senjata %d tier di luar 0-2" % iid)
    for mid, tabel in DROP.items():
        if mid not in MOB:
            masalah.append("drop untuk mob %d yang tidak ada" % mid)
        total = sum(row[1] for row in tabel)
        if total > 10000:
            masalah.append("drop mob %d totalnya %d > 10000" % (mid, total))
        for row in tabel:
            if row[0] not in ITEM:
                masalah.append("drop mob %d menunjuk item %d" % (mid, row[0]))
    for mapid, m in MAP.items():
        for x, tujuan, _ in m["portal"]:
            if tujuan not in MAP:
                masalah.append("map %d portal ke map %d" % (mapid, tujuan))
            if not 0 <= x <= m["lebar"]:
                masalah.append("map %d portal di luar batas" % mapid)
        for mob_id, _ in m["spawn"]:
            if mob_id not in MOB:
                masalah.append("map %d spawn mob %d" % (mapid, mob_id))
    if len(UPGRADE_PELUANG) != UPGRADE_MAKS or len(UPGRADE_BATU) != UPGRADE_MAKS:
        masalah.append("tabel upgrade panjangnya tidak cocok")
    for qid, q in QUEST.items():
        mapid, idx = q["npc"]
        if mapid not in MAP or idx >= len(MAP[mapid]["npc"]):
            masalah.append("quest %d menunjuk NPC yang tidak ada" % qid)
        if q["jenis"] == 0 and q["sasaran"] not in MOB:
            masalah.append("quest %d menyuruh bunuh mob %d" % (qid, q["sasaran"]))
        if q["jenis"] == 1 and q["sasaran"] not in ITEM:
            masalah.append("quest %d minta item %d" % (qid, q["sasaran"]))
        if q["butuh"] and q["butuh"] not in QUEST:
            masalah.append("quest %d butuh quest %d" % (qid, q["butuh"]))
        if q.get("berikut") and q["berikut"] not in QUEST:
            masalah.append("quest %d lanjut ke quest %d" % (qid, q["berikut"]))
        if q.get("ulang") and q.get("berikut"):
            masalah.append("quest %d berulang tapi punya lanjutan" % qid)
        for iid, _ in q.get("item", []):
            if iid not in ITEM:
                masalah.append("hadiah quest %d item %d tidak ada" % (qid, iid))
        for job, iid in (q.get("hadiah_job") or {}).items():
            if job not in JOB or iid not in ITEM:
                masalah.append("hadiah job quest %d tidak valid" % qid)
        if q["jumlah"] < 1 or q["jumlah"] > 999:
            masalah.append("quest %d jumlahnya aneh" % qid)
    masalah.extend(validasi_sosial())
    return masalah


# ----------------------------------------------------------------- quest
# jenis: 0 bunuh mob, 1 kumpulkan item (diserahkan/hangus), 2 bicara ke NPC
#
# npc  = (map_id, indeks npc di MAP[map_id]["npc"])
# lv   = level minimal untuk mengambil
# butuh= quest_id yang wajib selesai duluan (0 = bebas)
# ulang= 1 kalau boleh diulang berkali-kali (quest harian tanpa harian)
#
# Teks sengaja pendek: layar HP cuma muat sekitar 3 baris per dialog.
QUEST = {
    # --- rantai cerita Pak Tua -------------------------------------
    1: dict(nama="Celeng Perusak Ladang", npc=(1, 0), lv=1, butuh=0,
            jenis=0, sasaran=1, jumlah=8,
            mulai="Ladangku diobrak-abrik celeng dari Hutan Larik."
                  " Bereskan 8 ekor, ya.",
            jalan="Celengnya masih ada. Coba cek dekat pohon tumbang.",
            selesai="Lega rasanya. Ini untuk bekalmu.",
            exp=120, gold=200, item=[(100, 3)], berikut=2),
    2: dict(nama="Kayu untuk Pagar", npc=(1, 0), lv=3, butuh=1,
            jenis=1, sasaran=602, jumlah=5,
            mulai="Pagarku jebol. Bawakan 5 Kayu Jati dari hutan.",
            jalan="Kayu jati sering jatuh dari celeng yang kalah.",
            selesai="Pas sekali ukurannya. Terima kasih, Wira.",
            exp=260, gold=300, item=[(101, 3)], berikut=3),
    3: dict(nama="Tangis di Hutan Larik", npc=(1, 0), lv=8, butuh=2,
            jenis=0, sasaran=2, jumlah=6,
            mulai="Malam-malam ada tangis dari hutan. Usir 6 kuntilanak.",
            jalan="Jangan lawan sendirian kalau HP-mu tipis.",
            selesai="Desa bisa tidur nyenyak lagi.",
            exp=900, gold=800, item=[(600, 1)], berikut=4),
    4: dict(nama="Bayangan di Gurun", npc=(1, 0), lv=16, butuh=3,
            jenis=0, sasaran=3, jumlah=5,
            mulai="Pedagang hilang di Gurun Gurat. Genderuwo pelakunya."
                  " Habisi 5.",
            jalan="Genderuwo kuat memukul. Bawa ramuan yang cukup.",
            selesai="Jalur dagang aman kembali. Pakai ini.",
            exp=3500, gold=2200, item=[(401, 1)], berikut=5),
    5: dict(nama="Raksasa Hijau", npc=(1, 0), lv=28, butuh=4,
            jenis=0, sasaran=4, jumlah=3,
            mulai="Buto Ijo turun dari kawah. Tiga saja sudah cukup jadi"
                  " peringatan.",
            jalan="Serang selagi dia berbalik. Jangan diam di depannya.",
            selesai="Kau memang wira sejati.",
            exp=12000, gold=8000, item=[(601, 2)], berikut=6),
    6: dict(nama="Naga Kawah Lebur", npc=(1, 0), lv=40, butuh=5,
            jenis=0, sasaran=5, jumlah=1,
            mulai="Sumber semua kekacauan ada di dasar kawah. Bawa party.",
            jalan="Sendirian hampir mustahil. Ajak empat kawan.",
            selesai="Namamu akan disebut turun-temurun.",
            exp=60000, gold=40000, item=[(502, 1)], berikut=0),
    # --- Pedagang: quest ekonomi, boleh diulang ---------------------
    10: dict(nama="Setoran Kayu", npc=(1, 1), lv=2, butuh=0, ulang=1,
             jenis=1, sasaran=602, jumlah=20,
             mulai="Aku beli 20 Kayu Jati, harga di atas pasar.",
             jalan="Kumpulkan dulu 20 batang, baru balik ke sini.",
             selesai="Bisnis lancar. Datang lagi kapan saja.",
             exp=400, gold=1200, item=[], berikut=0),
    11: dict(nama="Setoran Bijih", npc=(1, 1), lv=5, butuh=0, ulang=1,
             jenis=1, sasaran=603, jumlah=10,
             mulai="Bijih besi lagi mahal. Bawakan 10, kubayar tunai.",
             jalan="Kuntilanak sering menjatuhkan bijih besi.",
             selesai="Kubayar sesuai janji.",
             exp=700, gold=1800, item=[], berikut=0),
    # --- Pandai Besi: hadiah senjata sesuai job ---------------------
    20: dict(nama="Bahan Tempaan", npc=(1, 2), lv=12, butuh=0,
             jenis=1, sasaran=600, jumlah=3,
             mulai="Bawakan 3 Batu Tempa, kubuatkan senjata sepadan"
                   " dengan jurusmu.",
             jalan="Batu Tempa jatuh dari makhluk hutan yang lebih tua.",
             selesai="Sudah jadi. Rawat baik-baik.",
             exp=1500, gold=0, item=[], hadiah_job={0: 201, 1: 211, 2: 221, 3: 231},
             berikut=21),
    21: dict(nama="Api Terakhir", npc=(1, 2), lv=30, butuh=20,
             jenis=1, sasaran=601, jumlah=5,
             mulai="Kristal Wira lima biji. Kutempa senjata pamungkasmu.",
             jalan="Kristal Wira hanya jatuh dari Buto Ijo dan Naga.",
             selesai="Ini tempaan terbaik seumur hidupku.",
             exp=20000, gold=0, item=[], hadiah_job={0: 202, 1: 212, 2: 222, 3: 232},
             berikut=0),
}

QUEST_AKTIF_MAKS = 5

# status quest yang disimpan per karakter
Q_AKTIF = 0
Q_SIAP = 1        # syarat sudah terpenuhi, tinggal lapor NPC
Q_SELESAI = 2


def quest_npc(map_id, npc_idx):
    """Semua quest yang dipegang satu NPC."""
    keluar = []
    for qid in sorted(QUEST.keys()):
        if QUEST[qid]["npc"] == (map_id, npc_idx):
            keluar.append(qid)
    return keluar


def hadiah_item(qid, job):
    """Daftar (item_id, jumlah) hadiah, termasuk yang tergantung job."""
    q = QUEST[qid]
    keluar = list(q.get("item", []))
    per_job = q.get("hadiah_job")
    if per_job and job in per_job:
        keluar.append((per_job[job], 1))
    return keluar


# ----------------------------------------------------------------- trade
TRADE_JARAK = 120        # piksel, dua pemain harus berdekatan
TRADE_SLOT_MAKS = 6      # item per sisi dalam satu transaksi
TRADE_GOLD_MAKS = 2000000000


# ------------------------------------------------- fitur sosial (v1.2)
# Guild, war antar guild, mail, dan lelang. Dipisah supaya file ini tidak
# kepanjangan; semua namanya tetap bisa diakses lewat G.<nama>.
from gamedata_sosial import *          # noqa: E402,F401,F403
from gamedata_sosial import validasi_sosial   # noqa: E402,F401
