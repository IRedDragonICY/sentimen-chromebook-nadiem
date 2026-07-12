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

## D3 — Skema label tiga lapis: spam → sikap → emosi ✅ dikunci

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

**Dikunci setelah kalibrasi** terhadap sampel nyata per fase dan contoh batu-uji brief.
Kelas final `sikap`: `pro_nadiem`, `kontra_nadiem`, `kritik_peradilan`, `kritik_pemerintah`,
`netral_informasional`, `tak_jelas`. Kelas `emosi`: `marah`, `duka`, `sinis`, `harapan`,
`netral`. Definisi lengkap + aturan preseden + batas-kasus: `skills/sentiment-labeling-id/SKILL.md`.

Dua kaidah yang lahir dari kalibrasi dan menjadi tulang punggung skema:
1. **Kodekan target yang terlihat, bukan posisi laten.** Kemarahan pada hakim itu ambigu
   secara laten (bisa "vonis zalim" atau "vonis terlalu ringan") — menebaknya akan
   menyuntikkan bias anotator. Maka `kritik_peradilan` berdiri sendiri tanpa
   diterjemahkan menjadi pro/kontra Nadiem.
2. **Emoji-only tidak pernah diberi stance** (selalu `tak_jelas` + emosi dari pemetaan
   deterministik). Melabelnya dari konteks post akan mengajari model noise — teksnya
   sendiri tidak memuat target.

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

---

## D6 — Anotasi dikerjakan in-session tanpa API eksternal; label di-commit sebagai artefak

**Konteks.** Tidak ada `ANTHROPIC_API_KEY` di lingkungan, sehingga pelabelan LLM
terprogram (batch API) tidak tersedia. Anotatornya adalah Claude (Fable 5) langsung di
sesi pengerjaan, mengikuti guideline tertulis di `skills/sentiment-labeling-id/SKILL.md`.

> **Diperbarui oleh [[D8]]:** poin (b) di bawah ditulis sebelum model lokal (ornith/qwen
> via Ollama) tersedia. Silver akhirnya dilabeli anotator LLM lokal terprogram, bukan
> label-langsung — lihat D8. Sisa keputusan D6 (gold in-session, label di-commit) tetap.

**Keputusan.** (a) Gold set dilabeli langsung dengan pass ganda pada subsampel ≥20% dan
kesepakatan test–retest dilaporkan. (b) ~~Silver set = gabungan label langsung + aturan
deterministik~~ → digantikan D8: silver via anotator LLM lokal (ornith:9b). Aturan
deterministik emoji-only tetap dipakai di inferensi. (c) Seluruh file label di-commit ke repo, sehingga
training tetap 100% reproducible dari artefak meski proses anotasinya (sebagaimana semua
anotasi manusia) adalah penilaian yang tidak bisa di-"re-run" mekanis. (d) Template prompt
untuk pelabelan API disertakan di SKILL agar pihak lain bisa memperluas label dengan jalur
terprogram.

**Risiko.** Anotator tunggal → bias sistematis mungkin tak terdeteksi oleh ukuran
konsistensi diri. Mitigasi: guideline publik + label publik (bisa diaudit baris per baris),
dan keterbatasan dinyatakan di model card.

---

## D7 — Anotator silver: qwen lokal via GPU, zero-shot (few-shot ditolak dgn bukti)

**Konteks.** Setelah gold 710 selesai, silver dilabeli dengan LLM lokal (Ollama).
Dua masalah ditemukan & diperbaiki: (a) qwen3.6-abliterated 21GB tak muat 6GB VRAM →
CPU, 15,8 dtk/komentar, output kosong (thinking-mode); (b) `ollama serve` mula-mula
jalan CPU-only karena `CUDA_VISIBLE_DEVICES` kosong di environment (akar yang sama
membuat torch tak lihat GPU). Setelah serve di-restart dengan `CUDA_VISIBLE_DEVICES=0`,
qwen3.5:4b berjalan di GPU (3965 MiB, 65 tok/dtk, ~1,3 dtk/komentar).

**Keputusan.** Anotator = qwen lokal, **zero-shot**, `think=False`, `format=json`,
suhu 0. Few-shot **ditolak**: pada 80 sampel gold, few-shot menurunkan sikap
macro-F1 (0,504 vs 0,568 zero-shot) — exemplar membiasi model kecil. Angka
zero-shot ini sekaligus menjadi **baseline LLM** yang dilaporkan jujur terhadap
gold (bukan diklaim sebagai akurasi model akhir).

**Model final** dipilih dari perbandingan agreement 4b vs 9b terhadap gold (pengguna
menyetujui anggaran waktu panjang, jadi kualitas diutamakan di atas kecepatan).
Silver diperbesar ke ~6000 kandidat karena anggaran waktu memungkinkan lebih
banyak data latih. Silver tetap di-*down-weight* (0,4) saat training karena berisik;
metrik akhir diukur pada gold test, sehingga silver berisik tak bisa menggelembungkan
klaim.

---

## D8 — Anotator silver final: ornith-1.0-9B (dipilih dari perbandingan vs gold)

**Konteks.** Pengguna meminta mencoba ornith-1.0-9B (model coding agentic terbuka).
Karena benchmark unggulnya adalah *coding* (bukan NLU Indonesia), pilihan diverifikasi
empiris terhadap gold, bukan diasumsikan.

**Perbandingan (92 sampel gold terstratifikasi, zero-shot, GPU):**

| model | sikap macro-F1 | acc | emosi macro-F1 | dtk/kom | keterangan |
|---|---|---|---|---|---|
| qwen3.5:4b | 0.602 | 0.659 | **0.711** | **0.93** | muat penuh GPU |
| qwen3.5:9b | 0.553 | 0.634 | 0.687 | 2.87 | lebih buruk |
| ornith:9b  | 0.596 | **0.685** | 0.696 | 1.64 | terbaik di kelas peradilan/pemerintah |

**Keputusan.** Silver dilabeli **ornith:9b**. Alasan: akurasi sikap tertinggi (0.685)
dan F1 tertinggi pada dua kelas paling penting & paling mudah tertukar di wacana ini
(`kritik_peradilan` 0.86, `kritik_pemerintah` 0.67). Selisih macro-F1 vs qwen 4b
(0.596 vs 0.602) berada dalam derau (n=92). Masalah teknis diperbaiki lebih dulu:
(a) ollama CPU-only karena `CUDA_VISIBLE_DEVICES` kosong → di-restart dengan GPU;
(b) ornith kadang menulis label emosi mendekati ("dukacita"/"duk") → ditambah
ekstraksi JSON robust + normalisasi label prefix → tingkat gagal 14% turun ke 0%.

**Kesehatan proses:** pada run penuh, laju ~1,67 dtk/komentar, gagal-parse < 1%.

---

## D9 — Verifikasi pipeline end-to-end di CPU sebelum run GPU

Sebelum melepas pipeline latih→eval→skor tanpa pengawasan, seluruh tahap diuji di CPU
dengan data gold kecil (1 epoch). Ini menemukan & memperbaiki tiga bug yang akan
menggagalkan run semalam: (1) `to_numpy()` read-only pada `rng.shuffle` di split;
(2) kolom `post` hilang di gold/silver (diturunkan dari `id`); (3) temperature scaling
& ambang abstain degenerate (T→0,05, selalu abstain) → dibatasi T∈[0,5; 5,0] dan ambang
≤ median keyakinan. Baseline TF-IDF terukur kuat (sikap macro-F1 0,507) — menjadi
patokan yang harus dikalahkan fine-tune agar klaim bermakna.
