#!/usr/bin/env python3
"""Data statis untuk fitur sosial WIRA NUSA v1.2.

Dipisah dari gamedata.py supaya file utama tidak kebablasan panjang.
gamedata.py mengimpor semua isi modul ini di bagian bawahnya, jadi
kode lain cukup memakai G.GUILD_BIAYA_BUAT dan sejenisnya.
"""

# ----------------------------------------------------------------- guild
GUILD_BIAYA_BUAT = 50000       # gold yang dipotong dari ketua
GUILD_LEVEL_MAKS = 5
GUILD_NAMA_MIN = 3
GUILD_NAMA_MAKS = 16

# indeks = level - 1
GUILD_ANGGOTA_MAKS = [10, 15, 20, 30, 40]
# exp yang dibutuhkan untuk naik dari level indeks ke level berikutnya
GUILD_EXP_NAIK = [30000, 90000, 240000, 600000]
# 1 gold sumbangan = sekian exp guild
GUILD_EXP_PER_GOLD = 1
GUILD_SUMBANG_MIN = 100

# pangkat
P_ANGGOTA = 0
P_PERWIRA = 1
P_KETUA = 2
NAMA_PANGKAT = {P_ANGGOTA: "Anggota", P_PERWIRA: "Perwira", P_KETUA: "Ketua"}

# bonus pasif per level guild (persen)
GUILD_BONUS_EXP = [0, 2, 4, 7, 10]
GUILD_BONUS_GOLD = [0, 2, 4, 7, 10]


def guild_anggota_maks(level):
    i = max(1, min(int(level), GUILD_LEVEL_MAKS)) - 1
    return GUILD_ANGGOTA_MAKS[i]


def guild_exp_naik(level):
    """Exp yang dibutuhkan untuk naik dari `level`. 0 = sudah maksimal."""
    i = max(1, min(int(level), GUILD_LEVEL_MAKS)) - 1
    if i >= len(GUILD_EXP_NAIK):
        return 0
    return GUILD_EXP_NAIK[i]


def guild_bonus(level, jenis):
    i = max(1, min(int(level), GUILD_LEVEL_MAKS)) - 1
    return (GUILD_BONUS_EXP if jenis == "exp" else GUILD_BONUS_GOLD)[i]


# ------------------------------------------------------------------- war
WAR_DURASI_MS = 30 * 60 * 1000     # satu perang berjalan 30 menit
WAR_COOLDOWN_MS = 60 * 60 * 1000   # jeda sebelum guild boleh perang lagi
WAR_LEVEL_MIN = 2                  # guild harus level 2 untuk deklarasi
WAR_TARUHAN_MIN = 5000             # kas yang dipertaruhkan tiap sisi
WAR_TARUHAN_MAKS = 500000
WAR_SKOR_MOB = 10                  # skor dasar per mob
WAR_SKOR_PER_LEVEL = 2             # tambahan skor per level mob
WAR_EXP_MENANG = 25000             # exp guild untuk pemenang
WAR_EXP_KALAH = 5000


def war_skor_mob(mob_level):
    return WAR_SKOR_MOB + WAR_SKOR_PER_LEVEL * max(1, int(mob_level))


# ------------------------------------------------------------------ mail
MAIL_KOTAK_MAKS = 30           # surat di kotak masuk
MAIL_BIAYA_KIRIM = 100         # gold, dipotong dari pengirim
MAIL_LAMPIRAN_MAKS = 4         # tumpuk item per surat
MAIL_GOLD_MAKS = 2000000000
MAIL_UMUR_HARI = 14            # surat lewat umur ini dibersihkan
MAIL_JUDUL_MAKS = 32
MAIL_ISI_MAKS = 180


# ---------------------------------------------------------------- lelang
LELANG_MAKS_PER_PEMAIN = 5
LELANG_DURASI_JAM = 24
LELANG_BIAYA_PERSEN = 5        # potongan untuk penjual saat laku
LELANG_HARGA_MIN = 10
LELANG_HARGA_MAKS = 2000000000
LELANG_HALAMAN = 12            # entri per halaman yang dikirim ke klien


def lelang_potongan(harga):
    return max(1, int(harga) * LELANG_BIAYA_PERSEN // 100)


def validasi_sosial():
    """Cek konsistensi angka. Dipanggil dari gamedata.validasi()."""
    salah = []
    if len(GUILD_ANGGOTA_MAKS) != GUILD_LEVEL_MAKS:
        salah.append("GUILD_ANGGOTA_MAKS tidak sepanjang GUILD_LEVEL_MAKS")
    if len(GUILD_EXP_NAIK) != GUILD_LEVEL_MAKS - 1:
        salah.append("GUILD_EXP_NAIK harus GUILD_LEVEL_MAKS - 1 entri")
    if len(GUILD_BONUS_EXP) != GUILD_LEVEL_MAKS:
        salah.append("GUILD_BONUS_EXP tidak sepanjang GUILD_LEVEL_MAKS")
    if len(GUILD_BONUS_GOLD) != GUILD_LEVEL_MAKS:
        salah.append("GUILD_BONUS_GOLD tidak sepanjang GUILD_LEVEL_MAKS")
    for i in range(1, len(GUILD_ANGGOTA_MAKS)):
        if GUILD_ANGGOTA_MAKS[i] <= GUILD_ANGGOTA_MAKS[i - 1]:
            salah.append("kapasitas anggota guild tidak naik di level " + str(i + 1))
    for i in range(1, len(GUILD_EXP_NAIK)):
        if GUILD_EXP_NAIK[i] <= GUILD_EXP_NAIK[i - 1]:
            salah.append("GUILD_EXP_NAIK tidak menanjak di indeks " + str(i))
    if WAR_TARUHAN_MIN >= WAR_TARUHAN_MAKS:
        salah.append("taruhan war minimum lebih besar dari maksimum")
    if WAR_LEVEL_MIN > GUILD_LEVEL_MAKS:
        salah.append("WAR_LEVEL_MIN melebihi level guild maksimum")
    if LELANG_HARGA_MIN >= LELANG_HARGA_MAKS:
        salah.append("harga lelang minimum lebih besar dari maksimum")
    if not 0 < LELANG_BIAYA_PERSEN < 50:
        salah.append("potongan lelang di luar akal sehat")
    if MAIL_LAMPIRAN_MAKS < 1:
        salah.append("lampiran surat minimal satu")
    return salah
