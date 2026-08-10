# Catatan Balancing WIRA NUSA

Semua angka ada di `server/gamedata.py` dan `server/gamedata_sosial.py`. Ubah di
sana, jalankan `python3 server/selftest.py`, dan konsistensinya (item drop yang
tidak ada, skill milik job hantu, portal ke map kosong) langsung ketahuan.

## Waktu dan gerak

| Nilai | Angka | Alasan |
|---|---|---|
| Tick | 10 Hz (100 ms) | cukup halus untuk HP jadul, hemat paket |
| Kecepatan jalan | 6 px/tick | layar 240 px habis dalam ~4 detik |
| Toleransi anti-cheat | 3x kecepatan | ampun buat lag, tetap menutup teleport |
| Jangkauan pandang | 420 px | entitas di luar itu tidak dikirim |
| Respawn mob | 8 detik | grinding tidak jadi menunggu |
| Respawn pemain | 5 detik | hukuman terasa tapi tidak menyiksa |
| Umur barang jatuh | 60 detik | lantai tidak penuh sampah |

## Kurva level

```
exp_untuk(lv) = 40 + lv^2 * 14 + lv^3 / 3
```

- Lv 1 -> 2: ~54 exp (2-3 celeng)
- Lv 30: ~21 ribu exp
- Lv 59 -> 60: ~117 ribu exp

Level maks 60. Naik level memulihkan HP/MP penuh dan memberi 1 poin skill.

## Job

| Job | HP | MP | ATK | DEF | Jangkauan | Rasa main |
|---|---|---|---|---|---|---|
| Pedang | 120 | 30 | 14 | 10 | dekat | tahan pukul, aman buat pemula |
| Sepasang | 100 | 40 | 17 | 7 | dekat | damage tertinggi, gampang mati |
| Dukun | 80 | 80 | 11 | 5 | dekat | area + sembuh, wajib di party |
| Senapan | 95 | 50 | 15 | 6 | 150 px | aman kalau rajin mundur |

Setiap job punya 3 skill (serangan kuat, area/utility, sembuh atau buff),
maks level 5, tiap level menambah 18% efek.

## Rumus damage

```
mentah  = ATK * 100 / (100 + DEF * 3)
damage  = mentah +/- sampai 10 persen
```

Pembagian, bukan pengurangan, supaya DEF tetap berguna di level tinggi
tanpa pernah bikin damage jadi nol. Minimum damage selalu 1.

## Mob dan progresi map

| Map | Lebar | Mob | Level target |
|---|---|---|---|
| Desa Ambar | 1600 | tidak ada (aman) | 1 |
| Hutan Larik | 2400 | Celeng Liar (lv2), Kuntilanak (lv8) | 1-12 |
| Gurun Gurat | 2800 | Genderuwo (lv16), Buto Ijo (lv28) | 12-30 |
| Kawah Lebur | 3200 | Buto Ijo, Naga Kawah (lv40, boss) | 30-60 |

Mob memburu dalam radius 120 px dan berhenti mengejar di 240 px, jadi
selalu ada jalan kabur -- penting karena kematian menghapus 5% gold.

## Ekonomi

- Gold awal: 300
- Harga jual = 25% harga beli (menutup celah beli-jual berulang)
- Gold hilang saat mati: 5%
- Sumber gold utama: mob, dibagi proporsional dengan damage

## Upgrade item

| Plus | Peluang | Batu Tempa |
|---|---|---|
| +1 | 95% | 1 |
| +2 | 90% | 1 |
| +3 | 82% | 2 |
| +4 | 72% | 2 |
| +5 | 60% | 3 |
| +6 | 48% | 4 |
| +7 | 36% | 5 |
| +8 | 25% | 7 |
| +9 | 15% | 9 |

Gagal = batu hangus, **item tidak pernah hilang atau turun tingkat**.
Itu keputusan sadar: upgrade jadi grind, bukan judi yang bikin pemain
berhenti main. Bonus per tingkat +12% dari stat dasar item, jadi +9
kira-kira setara dua tingkat senjata -- kuat, tapi tidak menghapus
gunanya senjata map berikutnya.

## Party

- Maksimal 5 orang
- Total exp party = 130% exp normal, dibagi rata ke anggota yang sedang
  di map yang sama
- Jadi party 2 orang = 65% masing-masing (rugi kalau cuma numpang),
  tapi kecepatan bunuh naik jauh lebih dari itu, terutama kalau ada Dukun

## Kalau mau di-tune

1. Terlalu lambat di awal: turunkan konstanta `lv^2 * 14`.
2. Boss terlalu gampang: naikkan `dfn` Naga Kawah, jangan HP-nya --
   HP besar cuma bikin pertarungan lama, DEF bikin gear terasa penting.
3. Ekonomi inflasi: turunkan gold mob, jangan naikkan harga toko.
4. Setelah tiap perubahan, jalankan selftest. Kalau ada item/mob/skill
   yang salah tunjuk, `validasi()` akan menolak server start.

## Tabel Quest (v1.1)

Jenis: 0 = bunuh mob, 1 = kumpul item, 2 = bicara.
Quest rantai (`berikut`) baru terbuka setelah quest sebelumnya selesai DAN
level pemain cukup. Quest `ulang` bisa diambil berkali-kali (grinding harian).

| ID | Nama | NPC | Lv | Syarat | Sasaran | Jumlah | EXP | Gold | Hadiah item | Rantai ke |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Celeng Perusak Ladang | Pak Tua | 1 | - | Celeng Liar | 8 | 120 | 200 | Ramuan Merah x3 | 2 |
| 2 | Kayu untuk Pagar | Pak Tua | 3 | quest 1 | Kayu Jati | 5 | 260 | 300 | Ramuan Biru x3 | 3 |
| 3 | Tangis di Hutan Larik | Pak Tua | 8 | quest 2 | Kuntilanak | 6 | 900 | 800 | Batu Tempa x1 | 4 |
| 4 | Bayangan di Gurun | Pak Tua | 16 | quest 3 | Genderuwo | 5 | 3.500 | 2.200 | Topi Anyam x1 | 5 |
| 5 | Raksasa Hijau | Pak Tua | 28 | quest 4 | Buto Ijo | 3 | 12.000 | 8.000 | Kristal Wira x2 | 6 |
| 6 | Naga Kawah Lebur | Pak Tua | 40 | quest 5 | Naga Kawah | 1 | 60.000 | 40.000 | Sayap Naga x1 | - |
| 10 | Setoran Kayu (ulang) | Pedagang | 2 | - | Kayu Jati | 20 | 400 | 1.200 | - | - |
| 11 | Setoran Bijih (ulang) | Pedagang | 5 | - | Bijih Besi | 10 | 700 | 1.800 | - | - |
| 20 | Bahan Tempaan | Pandai Besi | 12 | - | Batu Tempa | 3 | 1.500 | 0 | senjata tier 2 sesuai job | 21 |
| 21 | Api Terakhir | Pandai Besi | 30 | quest 20 | Kristal Wira | 5 | 20.000 | 0 | senjata tier 3 sesuai job | - |

Catatan balance:

- Rantai Pak Tua dirancang menemani pemain dari level 1 sampai 40; tiap quest
  memberi sekitar 15-25% dari exp yang dibutuhkan untuk naik level di rentang
  itu, jadi quest tidak menggantikan grinding, hanya mempercepatnya.
- Quest 20/21 adalah satu-satunya jalur mendapatkan senjata tier 2 dan tier 3
  tanpa membeli, supaya pemain gratisan tetap bisa mengejar.
- Dua quest ulang (10 dan 11) sengaja memberi gold lebih besar daripada exp
  supaya jadi sumber gold utama untuk pasar antar pemain.

## Ekonomi dagang antar pemain

- Tidak ada pajak dagang tatap muka: semua gold yang berpindah tetap utuh.
  Kalau inflasi terasa, kenakan potongan 2-5% di `_trade_eksekusi`.
- Batas 6 tumpukan per sesi bikin penipuan "tumpuk banyak biar bingung" susah,
  dan tampilan dua kolom di klien selalu menunjukkan isi tawaran lawan.
- Semua transaksi tercatat di tabel `catatan` dengan jenis `trade`, jadi kalau
  ada laporan penipuan, riwayatnya bisa ditelusuri.

## Guild (v1.2)

| Level | Exp untuk naik | Kapasitas anggota | Bonus exp | Bonus gold |
|---|---|---|---|---|
| 1 | 30.000 | 10 | 0% | 0% |
| 2 | 90.000 | 15 | 2% | 2% |
| 3 | 240.000 | 20 | 4% | 4% |
| 4 | 600.000 | 30 | 7% | 7% |
| 5 | maks | 40 | 10% | 10% |

- Biaya mendirikan guild 50.000 gold, dipotong langsung dari ketua.
- 1 gold sumbangan = 1 exp guild, minimum sumbang 100 gold. Artinya level 5
  butuh total 960.000 gold sumbangan: target jangka panjang untuk guild aktif,
  bukan sesuatu yang bisa dibeli satu orang di hari pertama.
- Bonus dibatasi 10% supaya ikut guild terasa berguna tapi pemain solo tidak
  jadi warga kelas dua.
- Pangkat: Anggota (0), Perwira (1, boleh mengundang dan memecat anggota),
  Ketua (2, boleh atur pangkat, deklarasi perang, dan bubarkan guild).

## Perang guild (v1.2)

| Nilai | Angka |
|---|---|
| Durasi perang | 30 menit |
| Jeda antar perang | 60 menit |
| Level guild minimum | 2 |
| Taruhan | 5.000 - 500.000 gold dari kas |
| Skor per mob | 10 + 2 x level mob |
| Exp guild pemenang | 25.000 |
| Exp guild yang kalah | 5.000 |

- Skor dari mob, bukan dari PvP, supaya perang tidak jadi ajang bully pemain
  level rendah di map lawan.
- Taruhan ditahan dari kas kedua guild saat perang dimulai; pemenang membawa
  seluruh pot. Kalau seri, taruhan dikembalikan.
- Yang kalah tetap dapat exp guild, jadi guild kecil tidak takut menantang.

## Surat / mail (v1.2)

| Nilai | Angka |
|---|---|
| Kotak masuk | 30 surat |
| Biaya kirim | 100 gold |
| Lampiran | maks 4 tumpuk |
| Gold per surat | maks 2.000.000.000 |
| Umur surat | 14 hari |
| Judul / isi | 32 / 180 karakter |

- Biaya kirim kecil tapi ada, supaya surat tidak dipakai buat spam iklan.
- Lampiran hanya bisa diambil sekali dan slot tas dicek dulu, jadi barang tidak
  pernah hilang di tengah jalan.

## Papan lelang (v1.2)

| Nilai | Angka |
|---|---|
| Lapak per pemain | 5 |
| Durasi lapak | 24 jam |
| Potongan pasar | 5% dari harga jual |
| Harga | 10 - 2.000.000.000 gold |
| Entri per halaman | 12 |

- Potongan 5% adalah satu-satunya penyedot gold permanen di v1.2. Ini penting:
  semua sumber gold lain menambah uang ke ekonomi, lelang menariknya keluar.
  Kalau inflasi masih terasa, naikkan ke 8% sebelum menyentuh gold drop mob.
- Batas 5 lapak per pemain menahan pemain kaya menguasai seluruh papan.
- Lapak yang tidak laku dan yang ditarik dikembalikan lewat surat, bukan
  langsung ke tas, supaya tas penuh tidak pernah bikin barang hilang.
