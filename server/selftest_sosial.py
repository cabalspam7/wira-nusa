"""Uji bagian sosial v1.2: guild, perang antar guild, surat, dan lelang.

Dipanggil dari selftest.py lewat jalankan(cek, bagian).
"""

import json
import os
import tempfile

import db as DB
import gamedata as G
import pasar as PASAR
from world import Dunia, Pemain, sekarang


def jalankan(cek, bagian):
    d = tempfile.mkdtemp(prefix="wira-sosial-")
    con, _baru = DB.buka(os.path.join(d, "sosial.db"))
    akun = DB.buat_akun(con, "sosial", "rahasia")
    ds = Dunia(seed=11)

    def orang(nama, gold=1000, job=0, level=10):
        dasar = G.statistik_dasar(job, level)
        cid = DB.buat_karakter(con, akun, nama, job, 0, 0, dasar["hp_maks"],
                               dasar["mp_maks"], gold, G.MAP_AWAL,
                               G.SPAWN_AWAL_X)
        data = DB.muat_karakter(con, cid)
        data["skill"] = json.loads(data["skill"] or "{}")
        data["quest"] = {}
        data["level"] = level
        p = Pemain(ds.eid_baru(), data, {}, {})
        ds.masuk(p)
        return p

    def punya(pemain, item_id):
        return sum(it["jumlah"] for it in pemain.inv.values()
                   if it["id"] == item_id)

    def slot_dari(pemain, item_id):
        for s in sorted(pemain.inv):
            if pemain.inv[s]["id"] == item_id:
                return s
        return -1

    # ------------------------------------------------- guild dan perang
    bagian("== 5. guild dan war antar guild")
    ketua = orang("Ketua", 300000)
    rekan = orang("Rekan", 120000)
    asing = orang("Asing", 300000)

    err, _g = ds.guild_buat(ketua, "ab")
    cek(err is not None, "nama guild terlalu pendek ditolak")
    err, _g = ds.guild_buat(ketua, "Wira!Sakti")
    cek(err is not None, "nama guild dengan tanda aneh ditolak")
    gold_awal = ketua.gold
    err, g1 = ds.guild_buat(ketua, "Wira Sakti")
    cek(err is None and g1["level"] == 1, "guild berhasil didirikan")
    cek(ketua.gold == gold_awal - G.GUILD_BIAYA_BUAT, "biaya guild dipotong")
    cek(ds.guild_pangkat(ketua) == G.P_KETUA, "pendiri jadi ketua")
    err, _g = ds.guild_buat(ketua, "Guild Kedua")
    cek(err is not None, "tidak bisa punya dua guild")
    err, _g = ds.guild_buat(asing, "wira sakti")
    cek(err is not None, "nama guild kembar ditolak")

    cek(ds.guild_undang(rekan, asing) is not None,
        "bukan anggota tidak bisa mengundang")
    cek(ds.guild_undang(ketua, rekan) is None, "ketua bisa mengundang")
    err, _g = ds.guild_terima(asing, g1["id"])
    cek(err is not None, "yang tidak diundang tidak bisa masuk")
    err, _g = ds.guild_terima(rekan, g1["id"])
    cek(err is None and rekan.guild == g1["id"], "undangan diterima")
    cek(len(g1["anggota"]) == 2, "anggota guild jadi dua")

    cek(ds.guild_set_pangkat(rekan, ketua.char_id, G.P_ANGGOTA) is not None,
        "anggota biasa tidak bisa mengatur pangkat")
    cek(ds.guild_set_pangkat(ketua, rekan.char_id, G.P_PERWIRA) is None,
        "ketua menaikkan rekan jadi perwira")
    cek(ds.guild_pangkat(rekan) == G.P_PERWIRA, "pangkat perwira tercatat")
    cek(ds.guild_pecat(rekan, ketua.char_id) is not None,
        "perwira tidak bisa memecat ketua")
    cek(ds.guild_pecat(ketua, ketua.char_id) is not None,
        "tidak bisa memecat diri sendiri")

    err, _naik = ds.guild_sumbang(rekan, 50)
    cek(err is not None, "sumbangan di bawah minimum ditolak")
    err, _naik = ds.guild_sumbang(rekan, 10 ** 9)
    cek(err is not None, "sumbangan melebihi gold ditolak")
    gold_rekan = rekan.gold
    err, naik = ds.guild_sumbang(rekan, 40000)
    cek(err is None and g1["kas"] == 40000, "kas guild bertambah")
    cek(rekan.gold == gold_rekan - 40000, "gold penyumbang berkurang")
    cek(g1["anggota"][rekan.char_id]["sumbang"] == 40000,
        "jasa sumbangan tercatat per anggota")
    cek(naik >= 1 and g1["level"] >= 2, "guild naik level dari sumbangan")
    cek(G.guild_bonus(g1["level"], "exp") > 0, "bonus exp guild aktif")
    cek(ds.guild_bonus_persen(rekan, "gold") ==
        G.guild_bonus(g1["level"], "gold"), "bonus gold ikut level guild")
    cek(G.guild_anggota_maks(g1["level"]) > G.guild_anggota_maks(1),
        "kapasitas anggota naik ikut level")
    cek(ds.guild_keluar(ketua) is not None,
        "ketua tidak bisa keluar sebelum mewariskan jabatan")

    err, g2 = ds.guild_buat(asing, "Naga Kembar")
    cek(err is None, "guild kedua berdiri")
    ds.guild_tambah_exp(g2, 400000)
    g2["kas"] = 200000
    cek(g2["level"] >= G.WAR_LEVEL_MIN, "guild kedua cukup level untuk perang")

    taruhan = 20000
    err, _a = ds.war_deklarasi(rekan, "Naga Kembar", taruhan)
    cek(err is not None, "perwira tidak bisa menyatakan perang")
    err, _a = ds.war_deklarasi(ketua, "Guild Hantu", taruhan)
    cek(err is not None, "tidak bisa menantang guild yang tidak ada")
    err, _a = ds.war_deklarasi(ketua, "Wira Sakti", taruhan)
    cek(err is not None, "tidak bisa menantang guild sendiri")
    err, _a = ds.war_deklarasi(ketua, "Naga Kembar", 1)
    cek(err is not None, "taruhan di bawah minimum ditolak")
    err, _ajakan = ds.war_deklarasi(ketua, "Naga Kembar", taruhan)
    cek(err is None, "tantangan perang terkirim")
    kas_a, kas_b = g1["kas"], g2["kas"]
    err, w = ds.war_terima(asing)
    cek(err is None and w is not None, "perang dimulai")
    cek(not w["selesai"] and ds.war_aktif(g1["id"]) is w,
        "perang terdaftar aktif")
    cek(g1["kas"] == kas_a - taruhan and g2["kas"] == kas_b - taruhan,
        "taruhan ditahan dari kedua kas")
    err, _a = ds.war_deklarasi(ketua, "Naga Kembar", taruhan)
    cek(err is not None, "tidak bisa perang dobel")

    skor_awal = w["skor"][g1["id"]]
    ds.war_bunuh(ketua, 20)
    ds.war_bunuh(rekan, 20)
    cek(w["skor"][g1["id"]] == skor_awal + 2 * G.war_skor_mob(20),
        "skor perang bertambah dari mob")
    ds.war_bunuh(asing, 5)
    cek(w["skor"][g2["id"]] == G.war_skor_mob(5), "skor lawan terpisah")
    cek(G.war_skor_mob(40) > G.war_skor_mob(5), "mob kuat memberi skor lebih")

    hasil = ds.war_selesai(w, "uji")
    cek(w["selesai"] and hasil is not None, "perang ditutup")
    cek(g1["kas"] == kas_a - taruhan + taruhan * 2,
        "pemenang membawa pulang seluruh pot")
    cek(g1["menang"] == 1 and g2["kalah"] == 1, "catatan menang kalah")
    cek(ds.war_aktif(g1["id"]) is None, "tidak ada perang aktif lagi")
    err, _a = ds.war_deklarasi(ketua, "Naga Kembar", taruhan)
    cek(err is not None, "masa istirahat setelah perang berlaku")

    DB.simpan_guild(con, g1)
    ds2 = Dunia(seed=12)
    ds2.guild_muat(DB.muat_guild_semua(con))
    ulang = ds2.guild.get(g1["id"])
    cek(ulang is not None and ulang["nama"] == "Wira Sakti",
        "guild tersimpan dan bisa dimuat ulang")
    cek(len(ulang["anggota"]) == len(g1["anggota"]),
        "anggota guild ikut tersimpan")
    cek(ds2.guild_by_nama.get("wira sakti") == g1["id"],
        "indeks nama guild ikut dimuat")
    cek(ulang["kas"] == g1["kas"] and ulang["menang"] == 1,
        "kas dan rekor perang ikut tersimpan")

    cek(ds.guild_bubar(rekan) is not None, "bukan ketua tidak bisa membubarkan")
    cek(ds.guild_bubar(ketua) is None, "ketua membubarkan guild")
    cek(ketua.guild is None and rekan.guild is None,
        "anggota lepas setelah guild bubar")
    cek(g1["id"] in ds.guild_dihapus, "guild ditandai untuk dihapus dari db")

    # -------------------------------------------------------- surat
    bagian("== 6. surat (mail)")
    pengirim = orang("Pengirim", 50000)
    penerima = orang("Penerima", 1000)
    penonton = orang("Penonton", 1000)
    pengirim.tambah_item(602, 4)
    pengirim.tambah_item(200, 1, 3)

    err, _m = PASAR.kirim_surat(con, pengirim, "Hantu", "Hai", "isi")
    cek(err is not None, "kirim ke nama yang tidak ada ditolak")
    err, _m = PASAR.kirim_surat(con, pengirim, "Pengirim", "Hai", "isi")
    cek(err is not None, "kirim ke diri sendiri ditolak")
    err, _m = PASAR.kirim_surat(con, pengirim, "Penerima", "Hai", "isi", -5)
    cek(err is not None, "gold negatif ditolak")

    slot_kayu = slot_dari(pengirim, 602)
    slot_pedang = slot_dari(pengirim, 200)
    gold_kirim = pengirim.gold
    err, mid = PASAR.kirim_surat(con, pengirim, "Penerima", "Titipan",
                                 "buat kamu", 5000,
                                 [(slot_kayu, 2), (slot_pedang, 1)])
    cek(err is None and mid, "surat dengan gold dan lampiran terkirim")
    cek(pengirim.gold <= gold_kirim - 5000, "gold dan biaya kirim dipotong")
    cek(punya(pengirim, 602) == 2, "barang lampiran keluar dari tas")

    daftar = PASAR.daftar_surat(con, penerima.char_id)
    cek(len(daftar) == 1 and not daftar[0]["dibaca"],
        "surat masuk dan belum dibaca")
    cek(len(daftar[0]["lampiran"]) == 2, "dua lampiran tercatat")
    cek(daftar[0]["dari_nama"] == "Pengirim", "nama pengirim tercatat")
    err, _m = PASAR.baca_surat(con, penonton.char_id, mid)
    cek(err is not None, "orang lain tidak bisa membaca surat")
    err, m = PASAR.baca_surat(con, penerima.char_id, mid)
    cek(err is None and m["isi"] == "buat kamu", "isi surat terbaca")
    cek(PASAR.daftar_surat(con, penerima.char_id)[0]["dibaca"],
        "surat berubah jadi berstatus dibaca")

    gold_terima = penerima.gold
    err, hasil = PASAR.ambil_lampiran(con, penerima, mid)
    cek(err is None and hasil is not None, "lampiran diambil")
    cek(penerima.gold == gold_terima + 5000, "gold lampiran masuk")
    cek(punya(penerima, 602) == 2, "barang lampiran masuk tas")
    plus_ok = any(it["id"] == 200 and it["plus"] == 3
                  for it in penerima.inv.values())
    cek(plus_ok, "tingkat tempa barang ikut terkirim")
    err, _h = PASAR.ambil_lampiran(con, penerima, mid)
    cek(err is not None, "lampiran tidak bisa diambil dua kali")
    cek(PASAR.hapus_surat(con, penonton.char_id, mid) is not None,
        "orang lain tidak bisa menghapus surat")
    cek(PASAR.hapus_surat(con, penerima.char_id, mid) is None,
        "surat yang sudah diambil bisa dihapus")
    cek(len(PASAR.daftar_surat(con, penerima.char_id)) == 0,
        "kotak surat bersih")

    PASAR.surat_sistem(con, penerima.char_id, "Kabar", "halo dari sistem", 100)
    kotak = PASAR.daftar_surat(con, penerima.char_id)
    cek(len(kotak) == 1 and kotak[0]["gold"] == 100, "surat sistem masuk")
    cek(DB.mail_hitung(con, penerima.char_id) == 1, "hitungan surat benar")

    # ------------------------------------------------------- lelang
    bagian("== 7. lelang (papan lapak)")
    penjual = orang("Penjual", 20000)
    pembeli = orang("Pembeli", 100000)
    pembeli2 = orang("Pembeli2", 100000)
    penjual.tambah_item(602, 10)
    penjual.tambah_item(201, 1, 2)
    slot_kayu = slot_dari(penjual, 602)
    slot_pedang = slot_dari(penjual, 201)

    err, _l = PASAR.pasang_lelang(con, penjual, slot_kayu, 1, 1)
    cek(err is not None, "harga di bawah batas ditolak")
    err, _l = PASAR.pasang_lelang(con, penjual, 29, 1, 5000)
    cek(err is not None, "slot kosong tidak bisa dipasang")
    err, _l = PASAR.pasang_lelang(con, penjual, slot_kayu, 99, 5000)
    cek(err is not None, "jumlah melebihi stok ditolak")
    kayu_awal = punya(penjual, 602)
    err, lid = PASAR.pasang_lelang(con, penjual, slot_kayu, 3, 6000)
    cek(err is None and lid, "lapak kayu dipasang")
    cek(punya(penjual, 602) == kayu_awal - 3, "barang lapak keluar dari tas")
    err, lid2 = PASAR.pasang_lelang(con, penjual, slot_pedang, 1, 50000)
    cek(err is None, "lapak pedang dipasang")

    rows = PASAR.daftar_lelang(con)
    cek(len(rows) == 2, "dua lapak tampil di papan")
    cek(rows[0]["penjual_nama"] == "Penjual", "nama penjual tampil di papan")
    cek(len(PASAR.daftar_lelang(con, 602)) == 1, "papan bisa disaring per barang")
    cek(len(PASAR.lelang_saya(con, penjual.char_id)) == 2, "lapak saya terdata")

    err, _h = PASAR.beli_lelang(con, penjual, lid)
    cek(err is not None, "tidak bisa membeli lapak sendiri")
    miskin = orang("Miskin", 100)
    err, _h = PASAR.beli_lelang(con, miskin, lid)
    cek(err is not None, "gold kurang tidak bisa membeli")
    gold_beli = pembeli.gold
    err, hasil = PASAR.beli_lelang(con, pembeli, lid)
    cek(err is None and hasil["jumlah"] == 3, "lapak dibeli")
    cek(pembeli.gold == gold_beli - 6000, "gold pembeli terpotong")
    cek(punya(pembeli, 602) == 3, "barang masuk tas pembeli")
    potongan = G.lelang_potongan(6000)
    cek(potongan == 6000 * G.LELANG_BIAYA_PERSEN // 100,
        "potongan pasar %d persen" % G.LELANG_BIAYA_PERSEN)
    surat_penjual = PASAR.daftar_surat(con, penjual.char_id)
    cek(len(surat_penjual) == 1 and surat_penjual[0]["judul"] == "Lapak laku",
        "hasil penjualan dikirim lewat surat")
    cek(surat_penjual[0]["gold"] == 6000 - potongan, "gold bersih di surat")
    err, _h = PASAR.beli_lelang(con, pembeli2, lid)
    cek(err is not None, "dua pembeli rebutan: yang kedua ditolak")

    cek(PASAR.tarik_lelang(con, pembeli, lid2) is not None,
        "orang lain tidak bisa menarik lapak")
    cek(PASAR.tarik_lelang(con, penjual, lid2) is None, "lapak ditarik")
    judul = [s["judul"] for s in PASAR.daftar_surat(con, penjual.char_id)]
    cek("Lapak ditarik" in judul, "barang tarikan dikembalikan lewat surat")
    cek(len(PASAR.lelang_saya(con, penjual.char_id)) == 0, "lapak saya bersih")
    cek(PASAR.tarik_lelang(con, penjual, lid2) is not None,
        "lapak yang sudah tutup tidak bisa ditarik lagi")

    penuh = orang("Penuh", 500000)
    for i in range(G.LELANG_MAKS_PER_PEMAIN + 2):
        penuh.tambah_item(200, 1, i % 3)
    galat = None
    dipasang = 0
    for s in sorted(penuh.inv)[:G.LELANG_MAKS_PER_PEMAIN + 1]:
        galat, lid3 = PASAR.pasang_lelang(con, penuh, s, 1, 1000)
        if lid3:
            dipasang += 1
    cek(dipasang == G.LELANG_MAKS_PER_PEMAIN and galat is not None,
        "batas %d lapak per pemain" % G.LELANG_MAKS_PER_PEMAIN)

    con.execute("UPDATE lelang SET kadaluarsa = 1 WHERE penjual_id = ?",
                (penuh.char_id,))
    con.commit()
    jumlah = PASAR.proses_kadaluarsa(con)
    cek(jumlah == G.LELANG_MAKS_PER_PEMAIN, "lapak kedaluwarsa diproses semua")
    judul = [s["judul"] for s in PASAR.daftar_surat(con, penuh.char_id)]
    cek("Lapak kedaluwarsa" in judul, "barang kedaluwarsa dikembalikan")
    cek(len(PASAR.daftar_lelang(con)) == 0, "papan lelang kosong lagi")
