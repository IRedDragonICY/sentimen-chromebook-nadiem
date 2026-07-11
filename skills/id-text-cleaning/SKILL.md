---
name: id-text-cleaning
description: Normalisasi & pembersihan teks media sosial Indonesia untuk NLP — penanganan emoji sebagai sinyal, unifikasi CSV crawling yang bermasalah (koma di timestamp, skema campur), deteksi spam judi/promo tahan-obfuscation, dan kunci near-duplikat anti-kebocoran. Pakai saat menyiapkan korpus komentar IG/TikTok/X berbahasa Indonesia untuk pelabelan atau training.
---

# Pembersihan Teks Media Sosial Indonesia

Kaidah dari membangun korpus 38 ribu komentar Instagram. Prinsip menyeluruh:
**teks mentah tidak pernah dibuang** — buat representasi turunan sesuai
kebutuhan, dan pakai fungsi normalisasi yang sama saat training dan inferensi.

## 1. Parsing CSV crawling: jangan percaya header

Crawler sering menghasilkan CSV cacat halus. Dua jebakan yang wajib diantisipasi:

- **Koma tak terkutip di dalam field.** Timestamp `30/6/2026, 21.43.41` memecah
  satu kolom jadi dua field → parser naif menggeser semua kolom (likes terbaca
  sebagai jam). Deteksi: bandingkan `len(row)` dengan `len(header)`; validasi
  bentuk tiap field dengan regex (tanggal `D/M/YYYY`, jam `HH.MM.SS`); gabung
  kembali. Baris yang tak lolos → catat sebagai anomali, jangan tebak diam-diam.
- **Skema campur antar file.** Sebagian file punya kolom ekstra (mis.
  `type, parent_id` untuk thread). Deteksi dari header, pertahankan info
  berharga (reply vs komentar utama), samakan skema saat menggabung.

Verifikasi kebenaran parser dengan invarian yang harus 100% benar: `likes`
selalu numerik, timestamp selalu ter-parse. Bila tidak, parser salah.

## 2. Normalisasi: NFKC dulu, selalu

`unicodedata.normalize("NFKC", teks)` melipat huruf "mewah" (𝗞𝗢𝗟𝗘𝗠𝗔𝗫 → KOLEMAX,
𝑖𝑡𝑎𝑙𝑖𝑐 → italic) dan bentuk kompatibilitas lain. Ini satu baris yang menggagalkan
sebagian besar obfuscation spam sekaligus. Lakukan **sebelum** apa pun:
lowercasing, pencocokan kata kunci, atau tokenisasi. Buang kategori kontrol (`Cc`)
kecuali newline/tab, rapikan whitespace.

Untuk input MODEL: pertahankan case dan emoji (keduanya sinyal). Untuk
PENCOCOKAN (spam, dedup): casefold + strip lebih agresif.

## 3. Emoji adalah sinyal, bukan noise

Di korpus emosional, belasan persen komentar bisa **hanya emoji** (di sini
11,4%). Membuangnya menghapus pembawa afeksi terbesar. Sebaliknya:
- Deteksi "emoji-only" (emoji + tanda baca/spasi saja) sebagai kategori sendiri.
- Petakan emoji dominan → emosi secara deterministik (😭😢💔🥀 → duka;
  😂🤣 → sinis; 😡🤬 → marah; 🙏🤲💪❤🔥 → harapan). Ambil kemunculan pertama.
- Rentang emoji yang praktis: blok 1F000–1FAFF, 2600–27BF (dingbats/simbol),
  panah & geometri yang lazim dipakai ekspresif; ingat variation selector
  (FE0F), ZWJ (200D), dan skin-tone modifier menempel pada grafem.

## 4. Deteksi spam tahan-obfuscation

Exact-match keyword akan meleset. Pelaku memakai huruf Unicode mewah, spasi
sisipan (`PUL AU777`), homoglyph, dan angka bervariasi. Resep:
1. NFKC + casefold lebih dulu (melumpuhkan huruf mewah).
2. Regex kosakata domain: judi (slot/gacor/maxwin/wd/nama situs/"dikasih menang"/
   "modal Nrb"), jasa (bor sumur/sedot wc), promo (giveaway/link di bio/olshop).
3. Perlakukan hasil sebagai **sinyal lemah**, bukan vonis. Untuk statistik
   akhir, latih detektor dari label — regex hanya untuk stratifikasi & seed.
4. Selalu laporkan proporsi spam dan efek menyertakan-vs-mengecualikannya
   (transparansi menaikkan kredibilitas angka sentimen).

## 5. Kunci near-duplikat (anti-kebocoran & anti-spam berulang)

Buat kunci kanonik yang menyamakan varian dangkal: NFKC + casefold, buang non-
huruf, untuk komentar emoji-only pakai himpunan emoji terurut sebagai kunci.
Efek: "😭😭😭" dan "😭😭" satu klaster; spam "menang 7,2jt" dan "menang 12,6jt"
satu klaster. Gunakan klaster untuk (a) split train/test group-aware —
komentar near-identik tak boleh lintas split, dan (b) sampling wakil klaster
alih-alih baris mentah.

## Anti-pola

- `pandas.read_csv` langsung pada CSV crawling tanpa memeriksa pergeseran kolom.
- Menghapus emoji di awal pipeline "biar bersih".
- Deteksi spam exact-match tanpa NFKC.
- Split train/test per baris saat ada duplikat → metrik bocor & optimistis.
- Lowercasing/menghapus tanda baca sebelum menyimpan teks mentah untuk audit.
