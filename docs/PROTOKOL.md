# Protokol WIRA NUSA

TCP, biner, big-endian. Satu paket:

```
[u16 panjang][u8 opcode][payload...]
```

`panjang` menghitung opcode + payload (jadi total byte di kabel =
`panjang + 2`). Batas keras 8192 byte per paket; lebih dari itu koneksi
langsung diputus. Teks memakai modified UTF-8 persis seperti
`DataOutputStream.writeUTF` di Java: `[u16 jumlah byte][isi]`.

Tipe yang dipakai di tabel di bawah:

| kode | arti |
|---|---|
| b | unsigned byte |
| sb | signed byte (dipakai untuk arah -1/1) |
| s | signed short |
| us | unsigned short |
| i | signed int 32-bit |
| teks | modified UTF-8 |

---

## Klien -> server

| op | nama | payload |
|---|---|---|
| 1 | LOGIN | teks akun, teks sandi |
| 2 | DAFTAR | teks akun, teks sandi |
| 3 | BUAT_CHAR | teks nama, b job, b rambut, b kulit |
| 4 | PILIH_CHAR | i char_id |
| 10 | GERAK | s x, sb arah, b state |
| 11 | SERANG | us skill_id (0 = serangan biasa), i target_eid |
| 12 | AMBIL | i drop_id |
| 13 | CHAT | b kanal (0 map, 1 party, 2 global), teks isi |
| 14 | PAKAI_ITEM | b slot inventori |
| 15 | PAKAI_EQUIP | b slot inventori |
| 16 | LEPAS_EQUIP | b slot equip |
| 17 | PINDAH_MAP | b indeks portal |
| 18 | PARTY | b aksi (0 buat, 1 gabung + i party_id, 2 keluar) |
| 19 | TRADE | lihat bagian v1.1 |
| 20 | NAIK_SKILL | us skill_id |
| 21 | TOKO | b aksi (0 minta daftar; 1 beli + us item + us jumlah; 2 jual + b slot + us jumlah) |
| 22 | UPGRADE | b slot equip |
| 23 | QUEST | lihat bagian v1.1 |
| 24 | GUILD | lihat bagian v1.2 |
| 25 | MAIL | lihat bagian v1.2 |
| 26 | LELANG | lihat bagian v1.2 |
| 30 | PING | i nonce |

## Server -> klien

| op | nama | payload |
|---|---|---|
| 100 | LOGIN_OK | teks versi server |
| 101 | TOLAK | teks alasan |
| 102 | DAFTAR_CHAR | b jumlah, lalu per karakter: i id, teks nama, b job, s level, b rambut, b kulit, b map |
| 103 | MASUK_MAP | b map_id, teks nama, teks tema, teks tile, us lebar, s tanah, b aman, i eid_kamu, s x, b n_portal {us x, b tujuan, us x_tujuan}, b n_npc {us x, teks nama, b jenis} |
| 104 | ENTITAS_TAMBAH | b jenis (0 pemain, 1 mob), i eid, teks nama, b job/mob_id, b rambut, b kulit, s level, s x, s y, sb arah, i hp, i hp_maks, us senjata, b plus, us baju, us topi, us sayap |
| 105 | ENTITAS_HAPUS | i eid |
| 106 | ENTITAS_GERAK | i eid, s x, sb arah, b state |
| 107 | ENTITAS_SERANG | i eid, us skill_id, i target_eid |
| 108 | DAMAGE | i eid kena, i damage, i hp sisa, i eid penyerang |
| 109 | MATI | i eid |
| 110 | HIDUP_LAGI | i eid |
| 111 | DROP_TAMBAH | i drop_id, us item_id, us jumlah, b plus, s x |
| 112 | DROP_HAPUS | i drop_id |
| 113 | INVENTORI | b n {b slot, us item, us jumlah, b plus}, b n_equip {b slot, us item, us jumlah, b plus} |
| 114 | STATUS | i hp, i hp_maks, i mp, i mp_maks, s level, i exp, i exp_butuh, i gold, s atk, s dfn, b poin, b n_skill {us id, b lv} |
| 115 | CHAT | b kanal, teks pengirim, teks isi |
| 116 | PARTY | i party_id, b n {i char_id, teks nama, i hp, i hp_maks} |
| 117 | TRADE | lihat bagian v1.1 |
| 118 | NAIK_LEVEL | i eid, s level |
| 119 | TOKO_ISI | b n {us item_id, i harga} |
| 120 | PESAN | teks |
| 121 | QUEST | lihat bagian v1.1 |
| 122 | GUILD | lihat bagian v1.2 |
| 123 | MAIL | lihat bagian v1.2 |
| 124 | LELANG | lihat bagian v1.2 |
| 130 | PONG | i nonce |

---

## Urutan wajib

```
klien: DAFTAR (opsional) -> LOGIN
server: LOGIN_OK, DAFTAR_CHAR
klien: BUAT_CHAR (opsional, server balas DAFTAR_CHAR lagi) -> PILIH_CHAR
server: MASUK_MAP, STATUS, INVENTORI, lalu ENTITAS_TAMBAH untuk
        setiap pemain/mob/drop yang terlihat
```

Semua paket dalam game sebelum `PILIH_CHAR` dijawab `TOLAK`.

## Aturan yang ditegakkan server

1. Klien **tidak pernah** mengirim angka damage, exp, gold, atau hasil
   upgrade. Semua dihitung server.
2. `GERAK` divalidasi: perpindahan maksimal =
   `WALK_SPEED * RUN_TOLERANCE * selisih_waktu / TICK_MS + 24` piksel.
   Kalau lewat, posisi tidak berubah, pelanggaran dicatat, dan server
   mengirim balik posisi resmi sebagai koreksi.
3. `SERANG` mengecek jarak (`jarak job + 12`), cooldown skill, MP, dan
   apakah skill itu memang milik job pemain dan sudah dipelajari.
4. `TOKO` beli/jual hanya di map bertanda `aman`.
5. `AMBIL` mengecek jarak 48 piksel dan hak loot 10 detik pertama.
6. Satu karakter tidak bisa online dua kali, walau dari akun yang sama.
7. Paket rusak / panjang tidak masuk akal: koneksi itu saja yang
   diputus, server tetap hidup (ada di selftest).

## Menambah opcode baru

1. Tambahkan konstanta di `server/protocol.py` **dan** `client/src/Msg.java`
   dengan nilai yang sama.
2. Tangani di `Server.tangani_game` (server) dan `GameScr.tangani` (klien).
3. Tambahkan cek di `server/selftest.py` supaya tidak diam-diam rusak
   di kemudian hari.

## Quest NPC dan dagang antar pemain (v1.1)

Opcode baru:

| Arah | Nama | Nilai |
|---|---|---|
| klien -> server | `C_QUEST` | 23 |
| server -> klien | `S_QUEST` | 121 |

`C_TRADE` (19) dan `S_TRADE` (117) sudah ada sejak v1.0, isinya dijelaskan di bawah.

### C_QUEST

```
b aksi
  aksi 0 : b npc_idx        bicara dengan NPC di map sekarang
  aksi 1 : us quest_id      ambil quest
  aksi 2 : us quest_id      serahkan quest
  aksi 3 : us quest_id      batalkan quest
  aksi 4 :                  minta jurnal quest yang sedang jalan
```

Aturan server:

- aksi 0/1/2/3 hanya diterima kalau jarak pemain ke NPC pemilik quest <= 90 px.
- maksimal `QUEST_AKTIF_MAKS` (5) quest aktif sekaligus.
- progres quest bunuh dihitung di server lewat hook `mob_mati`, termasuk untuk
  anggota party yang sedang dekat, jadi klien tidak pernah mengirim progres.
- quest kumpul dicek dari isi tas saat diserahkan; bahannya ikut hangus.

### S_QUEST

```
b mode                 0 = dialog NPC, 1 = jurnal
b n
  us quest_id
  b  kode              0 bisa ambil, 1 jalan, 2 siap serah,
                       3 selesai, 4 syarat kurang
  us progres
  us butuh
  b  jenis             0 bunuh, 1 kumpul, 2 bicara
  us sasaran           mob_id atau item_id
  teks nama
  teks teks            kalimat NPC sesuai kode
```

### C_TRADE

```
b aksi
  aksi 0 : i eid                       ajak pemain berdagang
  aksi 1 :                             terima ajakan
  aksi 2 :                             batalkan sesi
  aksi 3 : i gold, b n{ b slot, us jumlah }   ganti tawaran
  aksi 4 :                             kunci tawaran
```

### S_TRADE

```
b mode
  mode 0 : i eid, teks nama            ada yang mengajak dagang
  mode 1 : i eid, teks nama            sesi dimulai
  mode 2 : i goldKamu, b n{ us item, us jumlah, b plus },
           i goldLawan, b m{ us item, us jumlah, b plus },
           b kunciKamu, b kunciLawan
  mode 3 :                             transaksi berhasil
  mode 4 : teks alasan                 sesi batal
```

### Aturan anti-curang dagang

- Kedua pemain harus di map yang sama dan berjarak <= `TRADE_JARAK` (120 px)
  saat mengajak DAN saat transaksi dieksekusi.
- Maksimal `TRADE_SLOT_MAKS` (6) tumpukan per sisi, gold maksimal
  `TRADE_GOLD_MAKS`.
- Slot dobel dalam satu tawaran ditolak; jumlah tidak boleh melebihi isi tas.
- Mengubah tawaran otomatis membuka kembali kunci kedua pihak.
- Transaksi baru jalan kalau dua kunci menyala; kalau salah satu keluar,
  pindah map, atau menjauh, sesi dibatalkan tanpa barang berpindah.
- Setelah sukses, server langsung menulis karakter + item kedua pihak ke
  database dan mencatat baris `trade` di tabel `catatan`.

### Tombol klien

- `4` bicara dengan NPC terdekat (buka daftar quest); kalau tidak ada NPC
  dekat, jurnal quest yang terbuka.
- Di panel quest: `5` ambil/serah, `3` batal, `4` jurnal, `#` tutup.
- `6` ajak pemain terdekat berdagang, atau terima ajakan yang masuk.
- Di panel dagang: `5` tawarkan item terpilih, `1` tambah 100 gold,
  `3` kosongkan tawaran, `9` kunci, `*` batal.

## v1.2 - guild, war, surat, lelang

Opcode baru:

| arah | nama | nilai |
|---|---|---|
| klien | C_GUILD | 24 |
| klien | C_MAIL | 25 |
| klien | C_LELANG | 26 |
| server | S_GUILD | 122 |
| server | S_MAIL | 123 |
| server | S_LELANG | 124 |

### C_GUILD (b aksi)

| aksi | isi | arti |
|---|---|---|
| 0 | teks nama | dirikan guild (biaya 50.000 gold) |
| 1 | i eid | undang pemain di peta yang sama |
| 2 | i gid | terima undangan (berlaku 60 detik) |
| 3 | - | keluar dari guild |
| 4 | i charId | pecat anggota (perwira ke atas) |
| 5 | i charId, b pangkat | ubah pangkat (ketua saja) |
| 6 | i gold | sumbang kas, minimal 100 gold |
| 7 | - | minta info guild |
| 8 | - | bubarkan guild (ketua saja) |
| 9 | teks namaGuild, i taruhan | deklarasi perang |
| 10 | - | terima tantangan perang |
| 11 | - | tolak tantangan |
| 12 | - | minta status perang berjalan |

### S_GUILD (b mode)

- mode 0 info: `i gid, teks nama, b level, i exp, i expNaik, i kas, b pangkatKamu, us menang, us kalah, b bonusExp, b bonusGold, b n{i charId, teks nama, b pangkat, i sumbang, b online, s level}`
- mode 1: belum punya guild (tanpa isi)
- mode 2 undangan: `i gid, teks namaGuild, teks pengundang`
- mode 3 status war: `i warId, teks namaA, teks namaB, i skorA, i skorB, i sisaDetik, i taruhan`
- mode 4 tantangan masuk: `teks namaPenantang, i taruhan`
- mode 5 hasil war: `teks pemenang, i skorA, i skorB, i hadiahKas, b seri`

### C_MAIL (b aksi)

| aksi | isi | arti |
|---|---|---|
| 0 | - | minta daftar kotak surat |
| 1 | i id | baca isi surat (menandai sudah dibaca) |
| 2 | i id | ambil gold dan lampiran |
| 3 | i id | hapus surat (lampiran harus diambil dulu) |
| 4 | teks ke, teks judul, teks isi, i gold, b n{b slot, us jumlah} | kirim surat, biaya 100 gold |

### S_MAIL (b mode)

- mode 0 daftar: `b n{i id, teks dari, teks judul, b dibaca, i gold, b jmlLampiran, i waktu}`
- mode 1 isi: `i id, teks dari, teks judul, teks isi, i gold, b n{us item, us jumlah, b plus}`

### C_LELANG (b aksi)

| aksi | isi | arti |
|---|---|---|
| 0 | us itemId (0 = semua), b halaman | lihat papan lelang |
| 1 | - | lihat lapak sendiri |
| 2 | b slot, us jumlah, i harga | pasang lapak |
| 3 | i id | beli lapak |
| 4 | i id | tarik lapak sendiri |

### S_LELANG

`b mode (0 pasar, 1 lapak saya), b halaman, b n{i id, teks penjual, us itemId, us jumlah, b plus, i harga, i sisaDetik}`

### Perintah chat

Keypad ponsel tidak cukup untuk semua aksi, jadi ada perintah teks di kanal chat:

- `/guild NamaGuild` dirikan guild
- `/war NamaGuild taruhan` tantang perang
- `/lapak slot harga [jumlah]` pasang lapak dari slot tas
- `/surat NamaTujuan judul isi...` kirim surat
