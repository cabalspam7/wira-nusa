#!/usr/bin/env python3
"""Penyimpanan SQLite untuk WIRA NUSA.

Satu file DB, WAL, foreign key nyala. Password disimpan sebagai
PBKDF2-HMAC-SHA256 dengan salt per akun -- tidak pernah plaintext.
Inventori dan equipment disimpan sebagai baris terpisah supaya bisa
di-query (misal untuk audit item hasil upgrade).
"""

import hashlib
import json
import os
import secrets
import sqlite3
import time

PBKDF2_PUTARAN = 120000

SKEMA = """
CREATE TABLE IF NOT EXISTS akun (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nama      TEXT NOT NULL UNIQUE,
    salt      TEXT NOT NULL,
    hash      TEXT NOT NULL,
    dibuat    INTEGER NOT NULL,
    terakhir  INTEGER,
    banned    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS karakter (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    akun_id   INTEGER NOT NULL REFERENCES akun(id) ON DELETE CASCADE,
    nama      TEXT NOT NULL UNIQUE,
    job       INTEGER NOT NULL,
    rambut    INTEGER NOT NULL DEFAULT 0,
    kulit     INTEGER NOT NULL DEFAULT 0,
    level     INTEGER NOT NULL DEFAULT 1,
    exp       INTEGER NOT NULL DEFAULT 0,
    gold      INTEGER NOT NULL DEFAULT 0,
    hp        INTEGER NOT NULL DEFAULT 0,
    mp        INTEGER NOT NULL DEFAULT 0,
    map_id    INTEGER NOT NULL DEFAULT 1,
    x         INTEGER NOT NULL DEFAULT 200,
    poin      INTEGER NOT NULL DEFAULT 0,
    skill     TEXT NOT NULL DEFAULT '{}',
    dibuat    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS item (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    char_id   INTEGER NOT NULL REFERENCES karakter(id) ON DELETE CASCADE,
    slot      INTEGER NOT NULL,
    dipakai   INTEGER NOT NULL DEFAULT 0,
    item_id   INTEGER NOT NULL,
    jumlah    INTEGER NOT NULL DEFAULT 1,
    plus      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quest (
    char_id   INTEGER NOT NULL REFERENCES karakter(id) ON DELETE CASCADE,
    quest_id  INTEGER NOT NULL,
    status    INTEGER NOT NULL DEFAULT 0,
    progres   INTEGER NOT NULL DEFAULT 0,
    kali      INTEGER NOT NULL DEFAULT 0,
    diubah    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (char_id, quest_id)
);

CREATE TABLE IF NOT EXISTS catatan (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu   INTEGER NOT NULL,
    jenis   TEXT NOT NULL,
    char_id INTEGER,
    isi     TEXT
);

CREATE TABLE IF NOT EXISTS guild (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nama      TEXT NOT NULL UNIQUE,
    ketua_id  INTEGER NOT NULL,
    level     INTEGER NOT NULL DEFAULT 1,
    exp       INTEGER NOT NULL DEFAULT 0,
    kas       INTEGER NOT NULL DEFAULT 0,
    menang    INTEGER NOT NULL DEFAULT 0,
    kalah     INTEGER NOT NULL DEFAULT 0,
    war_akhir INTEGER NOT NULL DEFAULT 0,
    dibuat    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS guild_anggota (
    guild_id  INTEGER NOT NULL REFERENCES guild(id) ON DELETE CASCADE,
    char_id   INTEGER NOT NULL PRIMARY KEY,
    pangkat   INTEGER NOT NULL DEFAULT 0,
    sumbang   INTEGER NOT NULL DEFAULT 0,
    masuk     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mail (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ke_id     INTEGER NOT NULL,
    dari_id   INTEGER NOT NULL DEFAULT 0,
    dari_nama TEXT NOT NULL DEFAULT 'Sistem',
    judul     TEXT NOT NULL DEFAULT '',
    isi       TEXT NOT NULL DEFAULT '',
    gold      INTEGER NOT NULL DEFAULT 0,
    lampiran  TEXT NOT NULL DEFAULT '[]',
    dibaca    INTEGER NOT NULL DEFAULT 0,
    diambil   INTEGER NOT NULL DEFAULT 0,
    waktu     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lelang (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    penjual_id   INTEGER NOT NULL,
    penjual_nama TEXT NOT NULL,
    item_id      INTEGER NOT NULL,
    jumlah       INTEGER NOT NULL DEFAULT 1,
    plus         INTEGER NOT NULL DEFAULT 0,
    harga        INTEGER NOT NULL,
    waktu        INTEGER NOT NULL,
    kadaluarsa   INTEGER NOT NULL,
    status       INTEGER NOT NULL DEFAULT 0,
    pembeli_id   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mail_ke ON mail(ke_id);
CREATE INDEX IF NOT EXISTS idx_lelang_status ON lelang(status, kadaluarsa);
CREATE INDEX IF NOT EXISTS idx_lelang_penjual ON lelang(penjual_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_item_slot
    ON item(char_id, dipakai, slot);
CREATE INDEX IF NOT EXISTS idx_char_akun ON karakter(akun_id);
CREATE INDEX IF NOT EXISTS idx_catatan_waktu ON catatan(waktu);
"""


def buka(path):
    baru = not os.path.exists(path)
    direktori = os.path.dirname(os.path.abspath(path))
    if direktori:
        os.makedirs(direktori, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(SKEMA)
    con.commit()
    return con, baru


def _hash(sandi, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", sandi.encode("utf-8"), bytes.fromhex(salt), PBKDF2_PUTARAN
    ).hex()


# ------------------------------------------------------------------ akun

def buat_akun(con, nama, sandi):
    salt = secrets.token_hex(16)
    try:
        cur = con.execute(
            "INSERT INTO akun (nama, salt, hash, dibuat) VALUES (?,?,?,?)",
            (nama, salt, _hash(sandi, salt), int(time.time())))
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def cek_akun(con, nama, sandi):
    row = con.execute("SELECT * FROM akun WHERE nama = ?", (nama,)).fetchone()
    if row is None:
        return None, "akun tidak ditemukan"
    if row["banned"]:
        return None, "akun diblokir"
    if not secrets.compare_digest(_hash(sandi, row["salt"]), row["hash"]):
        return None, "sandi salah"
    con.execute("UPDATE akun SET terakhir = ? WHERE id = ?",
                (int(time.time()), row["id"]))
    con.commit()
    return row["id"], None


# -------------------------------------------------------------- karakter

def daftar_karakter(con, akun_id):
    return [dict(r) for r in con.execute(
        "SELECT * FROM karakter WHERE akun_id = ? ORDER BY id", (akun_id,))]


def buat_karakter(con, akun_id, nama, job, rambut, kulit, hp, mp, gold, map_id, x):
    try:
        cur = con.execute(
            """INSERT INTO karakter
               (akun_id, nama, job, rambut, kulit, hp, mp, gold, map_id, x, dibuat)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (akun_id, nama, job, rambut, kulit, hp, mp, gold, map_id, x,
             int(time.time())))
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def muat_karakter(con, char_id):
    row = con.execute("SELECT * FROM karakter WHERE id = ?", (char_id,)).fetchone()
    return dict(row) if row else None


def simpan_karakter(con, c):
    con.execute(
        """UPDATE karakter SET level=?, exp=?, gold=?, hp=?, mp=?, map_id=?,
           x=?, poin=?, skill=? WHERE id=?""",
        (c["level"], c["exp"], c["gold"], c["hp"], c["mp"], c["map_id"],
         c["x"], c["poin"], json.dumps(c["skill"]), c["id"]))
    con.commit()


# ------------------------------------------------------------------ item

def muat_item(con, char_id):
    inv, eq = {}, {}
    for r in con.execute("SELECT * FROM item WHERE char_id = ?", (char_id,)):
        entri = dict(id=r["item_id"], jumlah=r["jumlah"], plus=r["plus"])
        (eq if r["dipakai"] else inv)[r["slot"]] = entri
    return inv, eq


def simpan_item(con, char_id, inv, eq):
    con.execute("DELETE FROM item WHERE char_id = ?", (char_id,))
    baris = []
    for slot, it in inv.items():
        baris.append((char_id, slot, 0, it["id"], it["jumlah"], it.get("plus", 0)))
    for slot, it in eq.items():
        baris.append((char_id, slot, 1, it["id"], it["jumlah"], it.get("plus", 0)))
    con.executemany(
        "INSERT INTO item (char_id, slot, dipakai, item_id, jumlah, plus)"
        " VALUES (?,?,?,?,?,?)", baris)
    con.commit()


# ----------------------------------------------------------------- quest

def muat_quest(con, char_id):
    """quest_id -> dict(status, progres, kali)."""
    keluar = {}
    for r in con.execute("SELECT * FROM quest WHERE char_id = ?", (char_id,)):
        keluar[r["quest_id"]] = dict(status=r["status"], progres=r["progres"],
                                     kali=r["kali"])
    return keluar


def simpan_quest(con, char_id, quest):
    skr = int(time.time())
    baris = [(char_id, int(qid), q["status"], q["progres"], q.get("kali", 0), skr)
             for qid, q in quest.items()]
    con.execute("DELETE FROM quest WHERE char_id = ?", (char_id,))
    if baris:
        con.executemany(
            "INSERT INTO quest (char_id, quest_id, status, progres, kali, diubah)"
            " VALUES (?,?,?,?,?,?)", baris)
    con.commit()


def catat(con, jenis, char_id=None, isi=""):
    con.execute("INSERT INTO catatan (waktu, jenis, char_id, isi) VALUES (?,?,?,?)",
                (int(time.time()), jenis, char_id, isi))
    con.commit()


# ----------------------------------------------------------------- guild

def muat_guild_semua(con):
    """Semua guild lengkap dengan anggotanya (dipanggil sekali saat boot)."""
    keluar = []
    for r in con.execute("SELECT * FROM guild ORDER BY id"):
        g = dict(r)
        g["anggota"] = {}
        for a in con.execute(
                "SELECT * FROM guild_anggota WHERE guild_id = ?", (r["id"],)):
            g["anggota"][a["char_id"]] = dict(pangkat=a["pangkat"],
                                              sumbang=a["sumbang"],
                                              masuk=a["masuk"])
        keluar.append(g)
    return keluar


def buat_guild(con, nama, ketua_id):
    try:
        cur = con.execute(
            "INSERT INTO guild (nama, ketua_id, dibuat) VALUES (?,?,?)",
            (nama, ketua_id, int(time.time())))
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def simpan_guild(con, g):
    """Simpan satu guild + seluruh anggotanya. `g` = dict ala muat_guild_semua.

    Memakai INSERT OR REPLACE dengan id eksplisit supaya id di memori
    (world.Dunia) dan di DB selalu sama, termasuk untuk guild yang baru
    dibuat saat server sedang jalan.
    """
    con.execute(
        """INSERT OR REPLACE INTO guild
           (id, nama, ketua_id, level, exp, kas, menang, kalah, war_akhir, dibuat)
           VALUES (?,?,?,?,?,?,?,?,?,COALESCE(
               (SELECT dibuat FROM guild WHERE id = ?), ?))""",
        (g["id"], g["nama"], g["ketua_id"], g["level"], g["exp"], g["kas"],
         g.get("menang", 0), g.get("kalah", 0), g.get("war_akhir", 0),
         g["id"], int(time.time())))
    con.execute("DELETE FROM guild_anggota WHERE guild_id = ?", (g["id"],))
    baris = [(g["id"], cid, a.get("pangkat", 0), a.get("sumbang", 0),
              a.get("masuk", 0)) for cid, a in g["anggota"].items()]
    if baris:
        con.executemany(
            "INSERT OR REPLACE INTO guild_anggota"
            " (guild_id, char_id, pangkat, sumbang, masuk) VALUES (?,?,?,?,?)",
            baris)
    con.commit()


def hapus_guild(con, guild_id):
    con.execute("DELETE FROM guild_anggota WHERE guild_id = ?", (guild_id,))
    con.execute("DELETE FROM guild WHERE id = ?", (guild_id,))
    con.commit()


# ------------------------------------------------------------------ mail

def mail_kirim(con, ke_id, dari_id, dari_nama, judul, isi, gold=0, lampiran=None):
    cur = con.execute(
        """INSERT INTO mail (ke_id, dari_id, dari_nama, judul, isi, gold,
           lampiran, waktu) VALUES (?,?,?,?,?,?,?,?)""",
        (ke_id, dari_id, dari_nama, judul, isi, gold,
         json.dumps(lampiran or []), int(time.time())))
    con.commit()
    return cur.lastrowid


def _baris_mail(r):
    d = dict(r)
    try:
        d["lampiran"] = json.loads(r["lampiran"])
    except (ValueError, TypeError):
        d["lampiran"] = []
    return d


def mail_masuk(con, char_id, batas=50):
    return [_baris_mail(r) for r in con.execute(
        "SELECT * FROM mail WHERE ke_id = ? ORDER BY id DESC LIMIT ?",
        (char_id, batas))]


def mail_satu(con, mail_id):
    r = con.execute("SELECT * FROM mail WHERE id = ?", (mail_id,)).fetchone()
    return _baris_mail(r) if r else None


def mail_hitung(con, char_id):
    r = con.execute("SELECT COUNT(*) c FROM mail WHERE ke_id = ?",
                    (char_id,)).fetchone()
    return r["c"] if r else 0


def mail_tandai_baca(con, mail_id):
    con.execute("UPDATE mail SET dibaca = 1 WHERE id = ?", (mail_id,))
    con.commit()


def mail_tandai_diambil(con, mail_id):
    con.execute("UPDATE mail SET diambil = 1, gold = 0, lampiran = '[]',"
                " dibaca = 1 WHERE id = ?", (mail_id,))
    con.commit()


def mail_hapus(con, mail_id):
    con.execute("DELETE FROM mail WHERE id = ?", (mail_id,))
    con.commit()


def mail_bersihkan(con, umur_detik):
    """Hapus surat lama yang lampirannya sudah diambil / memang kosong."""
    batas = int(time.time()) - int(umur_detik)
    cur = con.execute(
        "DELETE FROM mail WHERE waktu < ? AND gold = 0 AND lampiran = '[]'",
        (batas,))
    con.commit()
    return cur.rowcount


# ---------------------------------------------------------------- lelang

def lelang_pasang(con, penjual_id, penjual_nama, item_id, jumlah, plus, harga,
                  durasi_detik):
    skr = int(time.time())
    cur = con.execute(
        """INSERT INTO lelang (penjual_id, penjual_nama, item_id, jumlah,
           plus, harga, waktu, kadaluarsa) VALUES (?,?,?,?,?,?,?,?)""",
        (penjual_id, penjual_nama, item_id, jumlah, plus, harga, skr,
         skr + int(durasi_detik)))
    con.commit()
    return cur.lastrowid


def lelang_satu(con, lelang_id):
    r = con.execute("SELECT * FROM lelang WHERE id = ?", (lelang_id,)).fetchone()
    return dict(r) if r else None


def lelang_daftar(con, item_id=None, batas=12, lompat=0):
    skr = int(time.time())
    if item_id:
        rows = con.execute(
            """SELECT * FROM lelang WHERE status = 0 AND kadaluarsa > ?
               AND item_id = ? ORDER BY harga ASC, id ASC LIMIT ? OFFSET ?""",
            (skr, item_id, batas, lompat))
    else:
        rows = con.execute(
            """SELECT * FROM lelang WHERE status = 0 AND kadaluarsa > ?
               ORDER BY id DESC LIMIT ? OFFSET ?""", (skr, batas, lompat))
    return [dict(r) for r in rows]


def lelang_milik(con, penjual_id):
    return [dict(r) for r in con.execute(
        "SELECT * FROM lelang WHERE penjual_id = ? AND status = 0"
        " ORDER BY id DESC", (penjual_id,))]


def lelang_hitung_aktif(con, penjual_id):
    r = con.execute(
        "SELECT COUNT(*) c FROM lelang WHERE penjual_id = ? AND status = 0",
        (penjual_id,)).fetchone()
    return r["c"] if r else 0


def lelang_tutup(con, lelang_id, status, pembeli_id=0):
    """status: 1 terjual, 2 ditarik penjual, 3 kadaluarsa.

    Update dilakukan bersyarat status masih 0 supaya dua pembeli yang
    menekan tombol bersamaan tidak bisa membeli barang yang sama.
    """
    cur = con.execute(
        "UPDATE lelang SET status = ?, pembeli_id = ? WHERE id = ? AND status = 0",
        (status, pembeli_id, lelang_id))
    con.commit()
    return cur.rowcount > 0


def lelang_kadaluarsa(con):
    """Lelang aktif yang sudah lewat waktu (belum diproses)."""
    return [dict(r) for r in con.execute(
        "SELECT * FROM lelang WHERE status = 0 AND kadaluarsa <= ?",
        (int(time.time()),))]
