# Model Card — Cermin Publik (analisis sentimen komentar kasus Chromebook)

Klasifikasi multi-task komentar media sosial berbahasa Indonesia: **spam**,
**sikap** (6 kelas), dan **emosi** (5 kelas), dari satu encoder IndoBERT yang
di-*fine-tune*.

## Untuk apa model ini

Menganalisis sentimen *agregat* komentar publik pada wacana kasus dugaan korupsi
pengadaan Chromebook — untuk jurnalisme data, riset opini, dan eksplorasi. Ia
memberi label per komentar beserta keyakinan, dan menandai saat ia ragu.

## Bukan untuk apa (larangan penggunaan)

- **Bukan** untuk menilai atau menghukum individu, atau menyimpulkan bersalah/tidak.
- **Bukan** untuk moderasi konten otomatis tanpa peninjauan manusia.
- **Bukan** untuk mengklaim "opini publik Indonesia" — data tidak representatif.
- **Bukan** untuk memprofilkan akun; identitas pengguna sengaja tidak dipakai.

## Data latih

- **Sumber:** 38.845 komentar dari 11 unggahan Instagram (Sep 2025 – Jul 2026).
- **Gold set:** 710 komentar berlabel manusia (anotator ahli tunggal mengikuti
  `skills/sentiment-labeling-id`), dipakai untuk evaluasi & sebagian training.
- **Silver set:** ~5.900 komentar berlabel LLM lokal (ornith-1.0-9B, zero-shot),
  di-*down-weight* (0,4) saat training karena lebih berisik.
- **Anti-kebocoran:** split train/val/test per klaster near-duplikat, bukan per
  baris — komentar identik/near-identik tak melintasi split.

## Skema label

- **spam** (biner): judi/promosi/jasa, dikecualikan dari statistik sentimen.
- **sikap:** `pro_nadiem`, `kontra_nadiem`, `kritik_peradilan`,
  `kritik_pemerintah`, `netral_informasional`, `tak_jelas`. Prinsip: mengodekan
  target yang eksplisit tertulis, bukan menebak posisi politik penulis.
- **emosi:** `marah`, `duka`, `sinis`, `harapan`, `netral`.

## Arsitektur & pelatihan

Encoder `indobenchmark/indobert-base-p1` dengan mean-pooling + tiga kepala linier.
Cross-entropy berbobot invers-frekuensi (menangani ketimpangan kelas), fp16,
early-stopping pada macro-F1 sikap (set val). Keyakinan dikalibrasi dengan
*temperature scaling*; ambang abstain dipilih pada val untuk menjaga akurasi
bagian terjawab. Seed tetap; hyperparameter & hash data latih tercatat di
`models/sentimen-id/meta.json`.

## Hasil evaluasi (gold test)

> Diisi otomatis dari `reports/evaluasi.json` setelah pipeline evaluasi selesai.
> Metrik utama **macro-F1** (bukan accuracy) karena kelas timpang; dilaporkan
> per-kelas + selang kepercayaan bootstrap, dibandingkan dengan baseline
> majority, TF-IDF+LogReg, dan LLM zero-shot.

_(placeholder — lihat `reports/evaluasi.json` dan bagian ini akan diperbarui.)_

## Keterbatasan yang diketahui

- **Sarkasme & sindiran halus** tetap sulit; ini genre dominan di data (mis.
  "yang mulia", pujian semu) sehingga sebagian kesalahan tak terhindarkan.
- **Kelas langka** (`netral_informasional`, `kontra_nadiem`) bersupport kecil di
  gold → F1-nya kurang stabil; jangan menonjolkan angkanya sebagai presisi tinggi.
- **Anotator tunggal.** Gold dilabeli satu anotator ahli (bukan panel independen),
  sehingga bias sistematis mungkin tak tertangkap oleh ukuran konsistensi diri.
  Guideline & label dipublikasikan agar dapat diaudit.
- **Silver dari LLM** membawa bias model tersebut; dimitigasi dengan bobot rendah
  dan evaluasi hanya pada gold manusia.
- **Domain sempit.** Dilatih pada wacana kasus ini; pada teks di luar domain,
  prediksi kurang bermakna dan sebaiknya diabaikan.
- **Ketidakterwakilan.** Komentar dari 11 unggahan IG — bukan sampel acak; bias
  platform, algoritma engagement, dan kemungkinan koordinasi/bot.

## Etika

Netral secara politik; menjunjung praduga tak bersalah; tidak menyajikan opini
komentator sebagai fakta. Username tidak ditampilkan di antarmuka mana pun.
