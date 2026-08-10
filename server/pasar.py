#!/usr/bin/env python3
"""Mail dan lelang WIRA NUSA (v1.2).

Dua fitur ini sengaja tidak disimpan di memori: semuanya lewat SQLite,
supaya pemain yang sedang offline tetap bisa menerima barang, gold, dan
hasil penjualan. Semua aturan main ada di sini; app.py cuma menerjemahkan
paket biner ke pemanggilan fungsi di modul ini.

Aturan emas: barang tidak pernah boleh ada di dua tempat sekaligus.
- Kirim surat  -> item keluar dari tas SEBELUM baris mail dibuat.
- Pasang lelang-> item keluar dari tas SEBELUM baris lelang dibuat.
- Beli lelang  -> baris lelang dikunci dulu (UPDATE ... WHERE status = 0),
                  baru gold pembeli dipotong dan surat dikirim.
"""

import time

import db as DB
import gamedata as G


def _skr():
    return int(time.time())


def cari_char(con, nama):
    """(char_id, nama asli) atau (None, None). Nama tidak peka huruf besar."""
    r = con.execute("SELECT id, nama FROM karakter WHERE nama = ? COLLATE NOCASE",
                    (nama,)).fetchone()
    if r is None:
        return None, None
    return r["id"], r["nama"]


def _slot_kosong_pemain(pemain):
    return sum(1 for s in range(G.INVENTORI_MAKS) if s not in pemain.inv)


def _potong(teks, maks):
    teks = (teks or "").replace("\n", " ").strip()
    return teks[:maks]


# ------------------------------------------------------------------ mail

def kirim_surat(con, pengirim, ke_nama, judul, isi, gold=0, lampiran=None):
    """lampiran = daftar (slot_tas, jumlah). Mengembalikan (err, mail_id)."""
    lampiran = lampiran or []
    gold = int(gold)
    judul = _potong(judul, G.MAIL_JUDUL_MAKS)
    isi = _potong(isi, G.MAIL_ISI_MAKS)
    if gold < 0 or gold > G.MAIL_GOLD_MAKS:
        return "jumlah gold tidak masuk akal", None
    if len(lampiran) > G.MAIL_LAMPIRAN_MAKS:
        return "lampiran maksimal %d tumpuk" % G.MAIL_LAMPIRAN_MAKS, None
    ke_id, ke_asli = cari_char(con, ke_nama)
    if ke_id is None:
        return "karakter tujuan tidak ada", None
    if ke_id == pengirim.char_id:
        return "tidak bisa berkirim surat ke diri sendiri", None
    if DB.mail_hitung(con, ke_id) >= G.MAIL_KOTAK_MAKS:
        return "kotak surat tujuan penuh", None
    if pengirim.gold < gold + G.MAIL_BIAYA_KIRIM:
        return "gold kurang (ongkos kirim %d)" % G.MAIL_BIAYA_KIRIM, None

    # cek dulu semua slot valid, baru dieksekusi -- supaya tidak setengah jalan
    rencana = []
    dipakai = {}
    for slot, jumlah in lampiran:
        slot = int(slot)
        jumlah = int(jumlah)
        it = pengirim.inv.get(slot)
        if it is None or jumlah < 1:
            return "slot lampiran kosong", None
        dipakai[slot] = dipakai.get(slot, 0) + jumlah
        if dipakai[slot] > it["jumlah"]:
            return "jumlah lampiran melebihi isi tas", None
        rencana.append((slot, jumlah, it["id"], it.get("plus", 0)))

    isi_lampiran = []
    for slot, jumlah, item_id, plus in rencana:
        pengirim.buang_item(slot, jumlah)
        isi_lampiran.append([item_id, jumlah, plus])
    pengirim.gold -= gold + G.MAIL_BIAYA_KIRIM

    mail_id = DB.mail_kirim(con, ke_id, pengirim.char_id, pengirim.nama,
                            judul or "(tanpa judul)", isi, gold, isi_lampiran)
    DB.catat(con, "mail", pengirim.char_id,
             "ke=%s gold=%d lampiran=%d id=%s"
             % (ke_asli, gold, len(isi_lampiran), mail_id))
    return None, mail_id


def surat_sistem(con, ke_id, judul, isi, gold=0, lampiran=None):
    """Surat dari 'Sistem' -- dipakai lelang, hadiah war, refund."""
    return DB.mail_kirim(con, ke_id, 0, "Sistem", _potong(judul, G.MAIL_JUDUL_MAKS),
                         _potong(isi, G.MAIL_ISI_MAKS), int(gold), lampiran or [])


def daftar_surat(con, char_id):
    return DB.mail_masuk(con, char_id, G.MAIL_KOTAK_MAKS)


def baca_surat(con, char_id, mail_id):
    m = DB.mail_satu(con, mail_id)
    if m is None or m["ke_id"] != char_id:
        return "surat tidak ada", None
    if not m["dibaca"]:
        DB.mail_tandai_baca(con, mail_id)
        m["dibaca"] = 1
    return None, m


def ambil_lampiran(con, pemain, mail_id):
    """(err, dict(gold, item)). Semua lampiran diambil sekaligus."""
    m = DB.mail_satu(con, mail_id)
    if m is None or m["ke_id"] != pemain.char_id:
        return "surat tidak ada", None
    if m["diambil"] or (not m["gold"] and not m["lampiran"]):
        return "surat ini tidak ada lampirannya", None
    if len(m["lampiran"]) > _slot_kosong_pemain(pemain):
        return "tas penuh", None
    if pemain.gold + m["gold"] > G.MAIL_GOLD_MAKS:
        return "gold kamu akan melebihi batas", None

    diterima = []
    for baris in m["lampiran"]:
        item_id, jumlah, plus = int(baris[0]), int(baris[1]), int(baris[2])
        if not pemain.tambah_item(item_id, jumlah, plus):
            # tidak seharusnya terjadi karena slot sudah dicek, tapi kalau
            # gagal, sisanya dibiarkan di surat supaya tidak hilang.
            sisa = m["lampiran"][len(diterima):]
            con.execute("UPDATE mail SET lampiran = ?, gold = 0, dibaca = 1"
                        " WHERE id = ?", (_json(sisa), mail_id))
            con.commit()
            pemain.gold += m["gold"]
            return "tas penuh, sebagian masih di surat", dict(gold=m["gold"],
                                                             item=diterima)
        diterima.append((item_id, jumlah, plus))
    pemain.gold += m["gold"]

    DB.mail_tandai_diambil(con, mail_id)
    DB.catat(con, "mail_ambil", pemain.char_id,
             "id=%d gold=%d item=%d" % (mail_id, m["gold"], len(diterima)))
    return None, dict(gold=m["gold"], item=diterima)


def _json(obj):
    import json
    return json.dumps(obj)


def hapus_surat(con, char_id, mail_id):
    m = DB.mail_satu(con, mail_id)
    if m is None or m["ke_id"] != char_id:
        return "surat tidak ada"
    if m["gold"] or m["lampiran"]:
        return "ambil dulu lampirannya"
    DB.mail_hapus(con, mail_id)
    return None


def bersihkan_surat(con):
    return DB.mail_bersihkan(con, G.MAIL_UMUR_HARI * 24 * 3600)


# ---------------------------------------------------------------- lelang

def pasang_lelang(con, pemain, slot, jumlah, harga):
    """(err, lelang_id)."""
    slot = int(slot)
    jumlah = int(jumlah)
    harga = int(harga)
    if harga < G.LELANG_HARGA_MIN or harga > G.LELANG_HARGA_MAKS:
        return "harga di luar batas (%d - %d)" % (G.LELANG_HARGA_MIN,
                                                  G.LELANG_HARGA_MAKS), None
    it = pemain.inv.get(slot)
    if it is None or jumlah < 1 or jumlah > it["jumlah"]:
        return "slot tas tidak valid", None
    info = G.ITEM.get(it["id"])
    if info is None:
        return "barang tidak dikenal", None
    if DB.lelang_hitung_aktif(con, pemain.char_id) >= G.LELANG_MAKS_PER_PEMAIN:
        return "lapak kamu sudah %d, tutup dulu satu" % G.LELANG_MAKS_PER_PEMAIN, None

    item_id = it["id"]
    plus = it.get("plus", 0)
    pemain.buang_item(slot, jumlah)
    lid = DB.lelang_pasang(con, pemain.char_id, pemain.nama, item_id, jumlah,
                           plus, harga, G.LELANG_DURASI_JAM * 3600)
    DB.catat(con, "lelang_pasang", pemain.char_id,
             "id=%s item=%d x%d +%d harga=%d" % (lid, item_id, jumlah, plus, harga))
    return None, lid


def daftar_lelang(con, item_id=None, halaman=0):
    lompat = max(0, int(halaman)) * G.LELANG_HALAMAN
    return DB.lelang_daftar(con, item_id, G.LELANG_HALAMAN, lompat)


def lelang_saya(con, char_id):
    return DB.lelang_milik(con, char_id)


def beli_lelang(con, pembeli, lelang_id):
    """(err, dict(item_id, jumlah, plus, harga, penjual))."""
    row = DB.lelang_satu(con, lelang_id)
    if row is None or row["status"] != 0:
        return "lapak sudah tidak ada", None
    if row["kadaluarsa"] <= _skr():
        return "lapak sudah kedaluwarsa", None
    if row["penjual_id"] == pembeli.char_id:
        return "itu lapak kamu sendiri", None
    if pembeli.gold < row["harga"]:
        return "gold kamu kurang", None
    if _slot_kosong_pemain(pembeli) < 1:
        return "tas penuh", None
    # kunci baris dulu: pembeli kedua akan gagal di sini, bukan setelah bayar
    if not DB.lelang_tutup(con, lelang_id, 1, pembeli.char_id):
        return "barang keburu dibeli orang lain", None

    pembeli.gold -= row["harga"]
    pembeli.tambah_item(row["item_id"], row["jumlah"], row["plus"])
    bersih = row["harga"] - G.lelang_potongan(row["harga"])
    surat_sistem(con, row["penjual_id"], "Lapak laku",
                 "%s membeli %s. Potongan pasar %d persen."
                 % (pembeli.nama, G.ITEM[row["item_id"]]["nama"],
                    G.LELANG_BIAYA_PERSEN),
                 gold=bersih)
    DB.catat(con, "lelang_beli", pembeli.char_id,
             "id=%d penjual=%d harga=%d bersih=%d"
             % (lelang_id, row["penjual_id"], row["harga"], bersih))
    return None, dict(item_id=row["item_id"], jumlah=row["jumlah"],
                      plus=row["plus"], harga=row["harga"],
                      penjual=row["penjual_nama"])


def tarik_lelang(con, pemain, lelang_id):
    row = DB.lelang_satu(con, lelang_id)
    if row is None or row["status"] != 0:
        return "lapak sudah tidak ada"
    if row["penjual_id"] != pemain.char_id:
        return "itu bukan lapak kamu"
    if not DB.lelang_tutup(con, lelang_id, 2, 0):
        return "lapak sudah tidak ada"
    surat_sistem(con, pemain.char_id, "Lapak ditarik",
                 "Barang dari lapak yang kamu tutup dikembalikan.",
                 lampiran=[[row["item_id"], row["jumlah"], row["plus"]]])
    return None


def proses_kadaluarsa(con):
    """Kembalikan barang lapak yang habis waktunya lewat surat. -> jumlah."""
    n = 0
    for row in DB.lelang_kadaluarsa(con):
        if not DB.lelang_tutup(con, row["id"], 3, 0):
            continue
        surat_sistem(con, row["penjual_id"], "Lapak kedaluwarsa",
                     "Barang yang tidak laku dikembalikan ke kamu.",
                     lampiran=[[row["item_id"], row["jumlah"], row["plus"]]])
        n += 1
    return n
