# Catatan Keputusan

Jejak keputusan teknis besar proyek ini: apa yang dipilih, mengapa, alternatif yang
ditolak, dan risikonya. Diurutkan kronologis. Keputusan yang belum final ditandai
**[sementara]** dan akan dikunci setelah ada bukti dari data.

---

## D1 — Strategi parsing CSV: validasi jumlah field + regex, gabungkan timestamp yang pecah

**Konteks.** Kolom `timestamp` berisi koma tanpa kutip (`30/6/2026, 21.43.41`), sehingga
setiap baris punya satu field lebih banyak daripada yang dijanjikan header. Satu file
(`DYR3czaxB9E.csv`) memakai skema berbeda dengan kolom `type, parent_id` (struktur thread).

**Keputusan.** Parser membaca dengan modul `csv` standar, lalu memvalidasi bentuk setiap
baris: jumlah field harus `len(header) + 1`, field tanggal harus cocok `D/M/YYYY`, field jam
harus cocok `HH.MM.SS`. Dua field itu digabung kembali menjadi satu timestamp. Baris yang
tidak lolos validasi dicatat sebagai anomali, bukan ditebak diam-diam. Informasi thread
(`type`, `parent_id`) dipertahankan, bukan dibuang.

**Alternatif yang ditolak.** (a) `pandas.read_csv` langsung — menggeser kolom dan merusak
`likes`/`komentar` tanpa peringatan. (b) Parse "dari kanan" tanpa validasi — bekerja untuk
data sekarang tapi gagal senyap bila ada baris aneh di masa depan.

**Verifikasi.** Di seluruh 38.845 baris: 0 anomali, `likes` 100% numerik, timestamp 100%
ter-parse. Angka profil brief terkonfirmasi (36.665 username unik; 11,42% emoji-only;
389 komentar kosong; 3.497 komentar ≤3 karakter).

**Risiko.** Bila crawler menghasilkan format timestamp lain di file baru, parser akan
menandainya anomali — perilaku yang diinginkan (gagal terlihat, bukan gagal senyap).

---

## D2 — Lingkungan: Python 3.12 via uv, bukan Python sistem 3.14

**Konteks.** Python sistem adalah 3.14 — terlalu baru untuk rantai PyTorch/transformers
yang stabil. Tersedia GPU RTX 4050 Laptop (6 GB VRAM), RAM 62 GB, akses internet.

**Keputusan.** `uv` mengelola virtualenv Python 3.12 di `.venv/`, dependensi dikunci di
`requirements.txt` (di-pin). Fine-tuning dilakukan lokal di GPU; 6 GB VRAM cukup untuk
encoder kelas base (IndoBERT-base ~110 juta parameter) dengan fp16 + batch sedang.

**Risiko.** VRAM 6 GB membatasi ukuran model — model kelas large tidak muat nyaman untuk
fine-tuning. Diterima: target produk memang model kecil-cepat yang bisa dipakai orang di
CPU, bukan model raksasa.

---

## D3 — [sementara] Skema label tiga lapis: spam → sikap → emosi

**Konteks.** Bukti dari data: sentimen di wacana ini terarah ke target. Komentar terpopuler
("Inilah fungsi dari menaikkan gaji para hakim 280%") negatif terhadap peradilan sekaligus
tersirat membela Nadiem. Polaritas tunggal pos/neg/netral akan menyesatkan agregat.
Selain itu 11,4% komentar hanya emoji (murni sinyal afeksi), dan ada spam judi/jasa yang
mencemari statistik.

**Keputusan (arah).** Tiga field per komentar:
1. `spam` (biner) — judi/promosi/jasa; dideteksi lebih dulu, dikecualikan dari statistik
   sentimen, tapi proporsinya dilaporkan transparan.
2. `sikap` (label tunggal, ~6 kelas): dukung-nadiem, kritik-nadiem, kritik-peradilan,
   kritik-pemerintah, netral-informasional, tidak-jelas/lainnya. Label tunggal "sikap
   dominan" dengan aturan preseden di guideline — bukan multi-label ABSA penuh.
3. `emosi` (~5 kelas): marah, duka/simpati, harapan/dukungan, sinis, netral. Komentar
   emoji-only mendapat sinyal utamanya di sini.

**Mengapa bukan ABSA multi-label penuh?** Reliabilitas anotasi. Dengan satu anotator LLM
dan gold set terbatas, kesepakatan label tunggal bisa diukur dan dipertanggungjawabkan;
multi-label per target menggandakan ruang kesalahan dan menyulitkan evaluasi jujur.
Kombinasi "sikap dominan (yang sudah memuat target)" + "emosi" menangkap sebagian besar
struktur multi-arah wacana ini dengan biaya kompleksitas jauh lebih rendah.

**Kunci skema** menunggu kalibrasi guideline terhadap contoh batu-uji (sarkasme, emoji-only,
multi-target, code-mixing) — lihat tugas #2. Jika kelas tertentu terbukti tak bisa
dibedakan secara konsisten, kelas digabung, bukan dipaksakan.

---

## D4 — [sementara] Strategi pelabelan: gold set multi-pass + silver LLM + fine-tune IndoBERT

**Keputusan (arah).**
- **Gold set** ±600 komentar, sampel terstratifikasi (post × gelombang peristiwa × tipe teks
  × tier likes), dilabeli beberapa pass independen dengan konsistensi test–retest diukur dan
  ketidaksepakatan diadjudikasi. *Kejujuran*: anotasinya dikerjakan satu anotator ahli
  (LLM dengan guideline tertulis), bukan panel manusia independen — ini keterbatasan yang
  akan dinyatakan eksplisit di model card, bukan disembunyikan.
- **Silver labels** ±6–8 ribu komentar via LLM-annotator dengan guideline terkunci, untuk
  training. Konsistensi diuji dengan duplikat tersembunyi dan pelabelan ulang sub-sampel.
- **Model produksi**: fine-tune encoder Indonesia (kandidat utama IndoBERT-base dari
  IndoBenchmark; pembanding XLM-R-base bila code-mixing terbukti menyakiti) dengan head
  multi-task. Hasilnya artefak kecil, cepat, offline, reproducible — "bisa dipakai orang".
- **Baseline pembanding** yang wajib dilaporkan: TF-IDF + linear, dan LLM zero-shot pada
  gold set. Kalau fine-tune tidak mengalahkan baseline, itu dilaporkan apa adanya.
- **Anti-kebocoran**: 6.190 baris adalah duplikat teks (33.185 teks unik dari 38.845).
  Split train/val/test dilakukan per klaster near-duplikat, bukan per baris.

**Alternatif yang ditolak.** LLM sebagai classifier produksi — kualitas per-komentar bagus
tapi tidak reproducible, mahal, lambat untuk 38 ribu komentar + inferensi interaktif, dan
membuat "model yang bisa dipakai orang" bergantung pada API eksternal.

---

## D5 — Empat gelombang peristiwa, bukan dua

**Konteks.** Brief menyebut dua gelombang (penangkapan Mei, vonis Jun–Jul). Verifikasi
langsung menemukan empat klaster: **Sep 2025** (fase penyelidikan awal, file DON94SnAD_0),
**Jan–Feb 2026** (fase KPK/e-katalog, DTVFd_Rk-KJ + klaster Feb di DUdN5deExTD),
**14–17 Mei 2026** (penangkapan), **30 Jun–11 Jul 2026** (tuntutan/vonis; puncak 14.566
komentar pada 30 Jun). Ada pula komentar hingga 11 Jul 2026.

**Keputusan.** Analisis waktu dan stratifikasi sampling memakai empat fase ini sebagai
dimensi peristiwa. UI menyajikan pergeseran sikap antar fase.
