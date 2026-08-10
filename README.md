# WIRA NUSA

MMORPG J2ME (MIDP-2.0 / CLDC-1.0) bergaya nusantara: client jar buat HP
Java/emulator + server otoritatif Python. Semua kode, aset, dan desainnya
ditulis dari nol untuk proyek ini.

> Ini **bukan** hasil decompile, reskin, atau private server dari game orang
> lain. Yang dipelajari dari game J2ME lama cuma *bentuk* teknisnya (client
> tipis + socket + paperdoll), bukan kode, aset, atau protokolnya.

---

## Isi

```
assets/          84 file PNG hasil generate (paperdoll, mob, latar, ubin, UI)
client/src/      8 file Java: MIDlet, canvas game, jaringan, protokol, UI
client/stubs/    30 stub javax.microedition.* supaya bisa compile tanpa WTK
client/build.sh  skrip build jar + jad
server/          server Python: protokol, data game, dunia, DB, pasar, TCP, selftest
tools/           generator aset dan generator stub
docs/            spesifikasi protokol dan catatan balancing
```

## Fitur

### Inti

- **Login + daftar akun** (PBKDF2 + salt, sandi tidak pernah disimpan polos)
- **3 karakter per akun**, 4 job: Pedang, Sepasang, Dukun, Senapan
- **4 map**: Desa Ambar (aman) -> Hutan Larik -> Gurun Gurat -> Kawah Lebur
- **5 mob** termasuk boss Naga Kawah, dengan AI aggro, kejar, pukul, respawn
- **Tempur real-time** 10 tick/detik, damage sepenuhnya dihitung server
- **12 skill** (3 per job): serang, area, sembuh, buff
- **Drop + loot** dengan hak loot 10 detik untuk penyerang terbanyak
- **Inventori 30 slot**, equip senjata/baju/topi/sayap, item bisa ditumpuk
- **Tempa item +1..+9**, peluang menurun, batu tempa hangus kalau gagal
- **Toko** beli/jual, **party** 5 orang dengan bonus exp, **chat** map/party/global
- **Level 1-60**, kurva exp, poin statistik, respawn otomatis
- **Paperdoll**: kaki, badan, kepala, rambut/topi, sayap, senjata, 12 frame animasi

### v1.1 - Quest NPC + dagang tatap muka

- 12 quest: rantai cerita 6 tahap dari Pak Tua, quest setoran berulang dari
  Pedagang, quest tempaan dari Pandai Besi (senjata tier 2 dan 3 per job)
- Jenis quest: bunuh mob, kumpul item, bicara. Progres dihitung di server dan
  ikut terbagi ke anggota party yang sedang dekat
- Maks 5 quest aktif, bisa dibatalkan, quest berulang mencatat jumlah selesai
- Dagang dua sisi: ajakan, tawaran gold + maks 6 tumpuk barang per sisi,
  sistem dua kunci, mengubah tawaran otomatis membuka kunci kedua pihak
- Sesi dagang batal otomatis kalau lawan keluar, pindah map, atau menjauh
  lebih dari 120 px. Barang tidak pernah berpindah sebagian

### v1.2 - Guild, perang guild, surat, dan lelang

- **Guild** 5 level: biaya dirikan 50.000 gold, kas guild, sumbangan anggota
  menaikkan level guild, kapasitas anggota dan bonus exp/gold ikut naik
- **Pangkat** anggota / perwira / ketua: undang, pecat, atur pangkat,
  wariskan jabatan ketua, keluar, bubarkan guild
- **Perang antar guild**: tantangan resmi dari ketua ke ketua, taruhan dari
  kas kedua guild, skor dari mob (bobot ikut level mob), durasi 30 menit,
  masa istirahat 1 jam, pemenang membawa seluruh pot + exp guild
- **Surat / mail**: kirim pesan + gold + maks 4 tumpuk lampiran ke pemain lain
  meskipun sedang offline, kotak 30 surat, umur surat 14 hari, biaya kirim,
  lampiran hanya bisa diambil sekali dan dicek slot tas dulu
- **Papan lelang**: pasang barang (maks 5 lapak per pemain, durasi 24 jam),
  cari per jenis barang, beli, tarik lapak. Potongan pasar 5% dan hasil
  penjualan dikirim lewat surat, jadi dagang tidak perlu tatap muka lagi
- Lapak kedaluwarsa otomatis dikembalikan ke penjual lewat surat
- Perintah chat cepat: `/guild NamaGuild`, `/war NamaGuild taruhan`,
  `/lapak slot harga [jumlah]`, `/surat NamaTujuan judul isi...`

### Anti-cheat

Klien tidak pernah mengirim angka damage, exp, harga, atau progres quest.
Gerakan divalidasi terhadap kecepatan maksimum, jarak serang dicek server,
tempa dan transaksi dihitung server. Cheat memori di emulator paling banter
mengubah tampilan di layar sendiri; server tetap menolak.

## Status validasi (jujur)

| Bagian | Status |
|---|---|
| Server Python | **Sudah dites**: `server/selftest.py` lulus **271 cek, 0 gagal** (`WIRA_TEST_OK`) |
| Aset PNG | **Sudah dibuat & dicek**: 84 file |
| Stub kompilasi | **Sudah digenerate**: 30 file |
| Client Java (.jar) | **Belum pernah dicompile atau dijalankan** -- mesin tempat proyek ini dibuat cuma punya JRE, tanpa `javac`. Compile dan tes jar harus dilakukan di komputer sendiri |

Kalau ada error compile di sisi client, itu wajar untuk ronde pertama; kirim
saja pesan errornya supaya bisa diperbaiki.

## Cara jalanin server

Butuh Python 3.9+ saja, tanpa dependensi luar.

```bash
cd server
python3 selftest.py                      # harus berakhir WIRA_TEST_OK
python3 app.py --host 0.0.0.0 --port 7777 --db data/wira.db
```

Buka port 7777 di firewall/VPS kalau mau diakses HP lain. Untuk produksi,
jalankan lewat systemd dan taruh DB di disk yang dibackup.

## Cara build client

```bash
python3 tools/gen_assets.py    # kalau folder assets/ belum ada
python3 tools/gen_stubs.py     # kalau folder client/stubs/ belum ada
cd client
./build.sh                     # pakai stub, butuh JDK (8 atau 17+)
# atau, hasil paling aman untuk HP asli:
WTK=/opt/WTK2.5.2 ./build.sh   # pakai midpapi + preverify resmi
```

Hasil: `client/dist/WiraNusa.jar` dan `.jad`.

## Cara tes

- **FreeJ2ME** (PC/RetroArch): buka jar, aktifkan izin jaringan
- **KEmulator Nnmod** (Windows): paling gampang buat debug, ada log konsol
- **J2ME Loader** (Android): install jar, set layar 240x320, izin internet
- **HP Java asli**: butuh jar yang sudah di-preverify; biasanya ditanya izin
  akses jaringan tiap konek, itu normal untuk MIDlet tanpa tanda tangan

Saat pertama buka, isi kolom Server dengan IP mesin server (bukan
`127.0.0.1` kalau dites dari HP), lalu Daftar -> Masuk -> Buat karakter.

## Kontrol

| Tombol | Fungsi |
|---|---|
| kiri / kanan | jalan (kiri juga bicara dengan NPC terdekat) |
| 5 atau OK | serang target terdekat (pakai skill yang dipasang) |
| 3 | ambil barang di dekatmu |
| 2 atau atas | masuk portal terdekat |
| 1 | buka toko (hanya di desa) |
| 6 | ajak dagang pemain terdekat / terima ajakan |
| 7 | tas / inventori |
| 8 | party |
| 9 | skill |
| * | menu sosial: jurnal quest, guild, kotak surat, papan lelang |
| # | chat |
| 0 | menu |

## Arsitektur singkat

```
MIDlet (client tipis)                Server Python (otoritatif)
  input tombol  ---> niat --------->  validasi + hitung damage/exp/drop
  gambar layar  <--- keadaan <------  broadcast ke semua pemain di map
  cache gambar                        SQLite: akun, karakter, item, quest,
                                      guild, mail, lelang, log
```

Detail paket per opcode ada di `docs/PROTOKOL.md`, angka balancing di
`docs/BALANCE.md`.

## Rencana lanjutan

- Musik/SFX (butuh aset audio, ukuran jar naik)
- Kompresi paket kalau pemain > 200 per map
- Pajak dagang guild 2-5% masuk kas guild
- Wilayah guild yang bisa direbut lewat perang
- UI input harga lelang yang lebih enak di keypad
