# WIRA NUSA

MMORPG J2ME (MIDP-2.0 / CLDC-1.0) bergaya nusantara: client jar buat HP
Java/emulator + server otoritatif Python. Semua kode, aset, dan desainnya
ditulis dari nol untuk proyek ini.

> Ini **bukan** hasil decompile, reskin, atau private server dari game
> orang lain. Yang diambil dari `ksatria_3.0.9_java.jar` cuma pelajaran
> soal *bentuk* teknisnya (client tipis + socket + paperdoll), bukan
> kode, aset, atau protokolnya.

---

## Isi

```
assets/          PNG hasil generate (paperdoll, mob, latar, ubin, UI)
client/src/      8 file Java: MIDlet, canvas game, jaringan, protokol, UI
client/stubs/    stub javax.microedition.* supaya bisa compile tanpa WTK
client/build.sh  skrip build jar + jad
server/          server Python: protokol, data game, dunia, DB, TCP, selftest
tools/           generator aset dan generator stub
docs/            spesifikasi protokol dan catatan balancing
```

> **Catatan**: folder `assets/` dan `client/stubs/` tidak di-commit ke repo
> karena isinya file turunan (biner PNG + stub compile). Buat dulu sebelum
> build dengan dua perintah di bawah.

---

## Mulai cepat (server)

```bash
git clone https://github.com/cabalspam7/wira-nusa
cd wira-nusa

# generate aset PNG orisinal  ->  ASSET_OK
python3 tools/gen_assets.py

# selftest server (tidak perlu aset)  ->  271 lulus / 0 gagal
python3 server/selftest.py

# jalankan server
python3 server/app.py --host 0.0.0.0 --port 7777 --db data/wira.db
```

Atau lewat **Makefile**:

```bash
make          # = make assets + make test
make server   # jalankan server
```

---

## Mulai cepat (client)

```bash
# 1. generate stub compile (sekali saja)
python3 tools/gen_stubs.py      # ->  STUB_OK  (client/stubs/...)

# 2. generate aset (kalau belum)
python3 tools/gen_assets.py     # ->  ASSET_OK

# 3. compile + package
cd client
./build.sh                      # butuh JDK 8+  ->  BUILD_OK
# atau dengan WTK asli:
WTK=/opt/WTK2.5.2 ./build.sh
```

Hasil: `client/dist/WiraNusa.jar` + `WiraNusa.jad`.

Or via Makefile:

```bash
make stubs    # gen_stubs.py
make jar      # stubs + build.sh
```

---

## Yang sudah jalan

- **Login + daftar akun** (PBKDF2, sandi tidak pernah disimpan polos)
- **3 karakter per akun**, 4 job: Pedang, Sepasang, Dukun, Senapan
- **4 map**: Desa Ambar (aman) -> Hutan Larik -> Gurun Gurat -> Kawah Lebur
- **5 mob** termasuk boss Naga Kawah, AI aggro + kejar + respawn
- **Tempur real-time** 10 tick/detik, damage dihitung server
- **12 skill** (3 per job): serang, area, sembuh, buff
- **Drop + loot**, hak loot 10 detik buat yang paling banyak nyerang
- **Inventori 40 slot**, equip 8 slot, tumpuk item
- **Upgrade item +1..+9** dengan peluang menurun
- **Toko** beli/jual; **party** 5 orang + bonus exp; **chat** map/party/global
- **Level 1-60**, poin skill, respawn otomatis
- **Paperdoll**: kaki, badan, kepala, rambut/topi, sayap, senjata — 12 frame
- **Quest NPC**: 12 quest (cerita, setoran, tempaan) dengan progres server
- **Dagang antar pemain**: sistem dua kunci + batal otomatis kalau menjauh
- **Guild**: buat, undang, tendang, sumbang, naik level, perang antar guild
- **Surat**: kirm/baca/lampiran item+gold antar pemain, kotak 30 surat
- **Lelang**: pasang lapak, beli, tarik, halaman, 24 jam kedaluwarsa
- **Anti-cheat dasar**: damage/harga/progres quest semuanya dihitung server;
  kecepatan gerak divalidasi; jarak serang & ambil drop dicek

## Status validasi

| Bagian | Status |
|---|---|
| Server Python | **Lulus selftest**: 271 cek / 0 gagal (termasuk TCP end-to-end) |
| Aset PNG | Digenerate programatik — jalankan `python3 tools/gen_assets.py` |
| Stub kompilasi | Digenerate programatik — jalankan `python3 tools/gen_stubs.py` |
| Client Java (.jar) | **Belum pernah dicompile di mesin ini** — tidak ada JDK di sandbox. Compile dan tes jar di komputer lokal kamu. Kalau ada error, kirim dan langsung diperbaiki. |

---

## Cara jalanin server (produksi)

```bash
# systemd (direkomendasikan)
sudo nano /etc/systemd/system/wiranusa.service
```

```ini
[Unit]
Description=Wira Nusa Game Server
After=network.target

[Service]
WorkingDirectory=/opt/wiranusa
ExecStart=/usr/bin/python3 server/app.py --host 0.0.0.0 --port 7777 --db /var/lib/wiranusa/wira.db
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now wiranusa
```

Buka port 7777 TCP di firewall. Backup folder `/var/lib/wiranusa/` secara berkala.

---

## Cara tes client

- **FreeJ2ME** (PC/RetroArch): buka jar, aktifkan izin jaringan.
- **KEmulator Nnmod** (Windows): paling gampang buat debug, ada log konsol.
- **J2ME Loader** (Android): install jar, set layar 240×320, izin internet.
- **HP Java asli**: butuh jar yang sudah di-preverify dan biasanya ditanya
  izin "akses jaringan" tiap konek — itu normal untuk MIDlet tidak ditandatangani.

Isi kolom **Server** dengan IP mesin server (bukan `127.0.0.1` dari HP),
lalu Daftar → Masuk → Buat karakter.

---

## Kontrol

| Tombol | Aksi |
|---|---|
| `4` / kiri | jalan kiri / bicara NPC |
| `6` / kanan | jalan kanan / ajak dagang |
| `5` / OK | serang target terdekat |
| `3` | ambil drop terdekat |
| `2` / atas | masuk portal terdekat |
| `1` | buka toko (hanya di desa) |
| `7` | tas / inventori |
| `8` | panel party |
| `9` | panel skill |
| `*` | panel sosial (guild, surat, lelang) |
| `#` | chat |
| `0` | menu |

Di dalam panel: `2/8` pilih, `5` pakai/konfirm, `#` tutup.

Perintah chat khusus:

```
/guild NamaGuild          buat guild baru
/war NamaGuild 10000      tantang perang + taruhan
/lapak 3 5000             pasang slot 3 ke lelang harga 5000
/surat Pemain Judul isi   kirim surat
```

---

## Arsitektur

```
MIDlet (client tipis)                Server Python (otoritatif)
  input tombol  ---> niat --------->  validasi + hitung damage/exp/drop
  gambar layar  <--- keadaan <------  broadcast ke semua pemain di map
  cache gambar                        SQLite: akun, karakter, item
```

Client tidak menyimpan angka apapun yang menentukan hasil pertarungan.
Cheat memori di emulator cuma mengubah tampilan lokal — server tetap
menolak gerakan ilegal.

Detail paket per opcode: `docs/PROTOKOL.md`  
Angka balancing: `docs/BALANCE.md`

---

## Lisensi

Kode, aset, dan konten proyek ini orisinal dan bebas dipakai untuk
tujuan non-komersial. Dilarang mendistribusikan ulang dengan klaim
sebagai karya orang lain.
