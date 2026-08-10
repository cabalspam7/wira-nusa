#!/usr/bin/env python3
"""Protokol biner WIRA NUSA.

Satu paket di kabel:

    [u16 panjang][u8 opcode][payload ...]

panjang = jumlah byte SETELAH field panjang (jadi 1 + len(payload)).
Semua angka big-endian, sama seperti DataOutputStream di Java, supaya
sisi client cukup pakai DataInputStream/DataOutputStream tanpa konversi.

String memakai format modified-UTF8 milik Java (writeUTF): u16 panjang byte
lalu byte UTF-8. Karakter di luar BMP tidak dipakai game ini, tapi encoder
di bawah tetap menangani surrogate pair supaya tidak diam-diam rusak.
"""

import struct

MAX_PACKET = 8192

# ---- klien -> server
C_LOGIN = 1
C_DAFTAR = 2
C_BUAT_CHAR = 3
C_PILIH_CHAR = 4
C_GERAK = 10
C_SERANG = 11
C_AMBIL = 12
C_CHAT = 13
C_PAKAI_ITEM = 14
C_PAKAI_EQUIP = 15
C_LEPAS_EQUIP = 16
C_PINDAH_MAP = 17
C_PARTY = 18
C_TRADE = 19
C_NAIK_SKILL = 20
C_TOKO = 21
C_UPGRADE = 22
C_QUEST = 23
C_GUILD = 24
C_MAIL = 25
C_LELANG = 26
C_PING = 30

# ---- server -> klien
S_LOGIN_OK = 100
S_TOLAK = 101
S_DAFTAR_CHAR = 102
S_MASUK_MAP = 103
S_ENTITAS_TAMBAH = 104
S_ENTITAS_HAPUS = 105
S_ENTITAS_GERAK = 106
S_ENTITAS_SERANG = 107
S_DAMAGE = 108
S_MATI = 109
S_HIDUP_LAGI = 110
S_DROP_TAMBAH = 111
S_DROP_HAPUS = 112
S_INVENTORI = 113
S_STATUS = 114
S_CHAT = 115
S_PARTY = 116
S_TRADE = 117
S_NAIK_LEVEL = 118
S_TOKO_ISI = 119
S_PESAN = 120
S_QUEST = 121
S_GUILD = 122
S_MAIL = 123
S_LELANG = 124
S_PONG = 130

NAMA_OP = {v: k for k, v in list(globals().items())
           if k.startswith(("C_", "S_")) and isinstance(v, int)}


class ProtokolError(Exception):
    pass


def _utf_bytes(teks):
    """Modified UTF-8 ala Java: NUL jadi 2 byte, sisanya UTF-8 biasa."""
    keluar = bytearray()
    for ch in teks:
        c = ord(ch)
        if c == 0:
            keluar += b"\xc0\x80"
        elif c < 0x80:
            keluar.append(c)
        elif c < 0x800:
            keluar.append(0xC0 | (c >> 6))
            keluar.append(0x80 | (c & 0x3F))
        elif c < 0x10000:
            keluar.append(0xE0 | (c >> 12))
            keluar.append(0x80 | ((c >> 6) & 0x3F))
            keluar.append(0x80 | (c & 0x3F))
        else:  # surrogate pair
            c -= 0x10000
            hi = 0xD800 | (c >> 10)
            lo = 0xDC00 | (c & 0x3FF)
            for s in (hi, lo):
                keluar.append(0xE0 | (s >> 12))
                keluar.append(0x80 | ((s >> 6) & 0x3F))
                keluar.append(0x80 | (s & 0x3F))
    return bytes(keluar)


class Tulis(object):
    """Perakit paket. Pakai sebagai context manager atau panggil paket()."""

    def __init__(self, opcode):
        self.opcode = opcode
        self.buf = bytearray()

    def b(self, v):
        self.buf.append(int(v) & 0xFF)
        return self

    def sb(self, v):
        self.buf += struct.pack(">b", max(-128, min(127, int(v))))
        return self

    def s(self, v):
        self.buf += struct.pack(">h", max(-32768, min(32767, int(v))))
        return self

    def us(self, v):
        self.buf += struct.pack(">H", int(v) & 0xFFFF)
        return self

    def i(self, v):
        self.buf += struct.pack(">i", int(v))
        return self

    def teks(self, v):
        raw = _utf_bytes(v if v is not None else "")
        if len(raw) > 0xFFFF:
            raise ProtokolError("teks terlalu panjang")
        self.buf += struct.pack(">H", len(raw)) + raw
        return self

    def paket(self):
        isi = bytes([self.opcode]) + bytes(self.buf)
        if len(isi) > MAX_PACKET:
            raise ProtokolError("paket %d byte melebihi batas" % len(isi))
        return struct.pack(">H", len(isi)) + isi


class Baca(object):
    """Pembaca payload. Semua getter memvalidasi sisa buffer."""

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def _ambil(self, n):
        if self.pos + n > len(self.data):
            raise ProtokolError("payload habis di posisi %d" % self.pos)
        potong = self.data[self.pos:self.pos + n]
        self.pos += n
        return potong

    def b(self):
        return self._ambil(1)[0]

    def sb(self):
        return struct.unpack(">b", self._ambil(1))[0]

    def s(self):
        return struct.unpack(">h", self._ambil(2))[0]

    def us(self):
        return struct.unpack(">H", self._ambil(2))[0]

    def i(self):
        return struct.unpack(">i", self._ambil(4))[0]

    def teks(self, maks=64):
        n = struct.unpack(">H", self._ambil(2))[0]
        raw = self._ambil(n)
        try:
            hasil = raw.replace(b"\xc0\x80", b"\x00").decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise ProtokolError("teks bukan UTF-8 valid")
        if len(hasil) > maks:
            raise ProtokolError("teks melebihi %d karakter" % maks)
        return hasil

    def sisa(self):
        return len(self.data) - self.pos


class Pemotong(object):
    """Memecah aliran TCP jadi paket utuh. Tahan paket terpotong."""

    def __init__(self):
        self.buf = bytearray()

    def masuk(self, data):
        self.buf += data
        keluar = []
        while len(self.buf) >= 2:
            n = struct.unpack(">H", self.buf[:2])[0]
            if n == 0:
                raise ProtokolError("panjang paket nol")
            if n > MAX_PACKET:
                raise ProtokolError("panjang paket %d tidak masuk akal" % n)
            if len(self.buf) < 2 + n:
                break
            isi = bytes(self.buf[2:2 + n])
            del self.buf[:2 + n]
            keluar.append((isi[0], Baca(isi[1:])))
        return keluar
