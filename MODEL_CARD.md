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

<!-- hasil:mulai -->
| Model | sikap macro-F1 | sikap acc | emosi macro-F1 | spam macro-F1 |
|---|---|---|---|---|
| Majority (lantai) | 0.066 <sub>[0.06–0.08]</sub> | 0.247 | 0.072 <sub>[0.06–0.08]</sub> | 0.487 <sub>[0.48–0.49]</sub> |
| TF-IDF + LogReg | 0.534 <sub>[0.46–0.61]</sub> | 0.629 | 0.616 <sub>[0.55–0.67]</sub> | 1.000 <sub>[1.00–1.00]</sub> |
| IndoBERT fine-tune | 0.544 <sub>[0.47–0.61]</sub> | 0.650 | 0.624 <sub>[0.56–0.68]</sub> | 1.000 <sub>[1.00–1.00]</sub> |
| LLM zero-shot: ornith:9b | 0.548 <sub>[0.48–0.62]</sub> | 0.644 | 0.638 <sub>[0.57–0.69]</sub> | 0.982 <sub>[0.93–1.00]</sub> |

_Gold test n=283. Metrik utama macro-F1; angka dalam kurung adalah selang kepercayaan bootstrap 95%._

<!-- hasil:akhir -->

### Bacaan hasil (jujur)

- **Fine-tune ≈ TF-IDF ≈ LLM 9B.** Sikap macro-F1 keempat model non-trivial
  berhimpit: TF-IDF 0,534, fine-tune 0,544, dan ornith-9B zero-shot 0,548 —
  selisihnya jauh lebih kecil daripada lebar selang kepercayaan (semua ~[0,47–0,62]).
  Artinya angka ~0,54 / akurasi ~65% ini adalah **plafon tugas**, bukan kelemahan
  satu model: bahkan LLM 50× lebih besar tak menembusnya. Kami **tidak** mengklaim
  fine-tune "mengalahkan" baseline secara bermakna.
- **Lalu kenapa memakai fine-tune?** Bukan karena F1-nya lebih tinggi, melainkan
  karena ia ~100 MB, jalan offline & cepat untuk 38.845 komentar + inferensi
  interaktif, deterministik/reproducible, terkalibrasi, dan bisa **abstain** —
  hal yang tak dimiliki LLM zero-shot yang lambat dan bergantung server.
- **Akurasi vs cakupan.** Angka 65% adalah "dipaksa menjawab semua komentar".
  Dengan ambang abstain, pada **56% komentar** yang keyakinannya tinggi akurasi
  sikap **≈79%**; sisanya ditandai "ragu", bukan ditebak. Untuk keputusan penting,
  pakai mode ini atau statistik agregat — bukan label mentah per komentar ambigu.
- **Metrik sengaja kejam.** macro-F1 menimbang kelas langka (`netral_informasional`
  n=7, `kontra_nadiem` n=18 di test) sama berat dengan kelas umum; itu menyeret
  rata-rata turun. Kelas bersinyal cukup sudah kuat (`kritik_peradilan` F1=0,81).

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
