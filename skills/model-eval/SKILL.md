---
name: model-eval
description: Protokol evaluasi jujur untuk classifier teks berkelas timpang (macro-F1 & per-kelas, confusion matrix, error analysis, kalibrasi/ketidakpastian, ambang abstain). Pakai saat menilai model klasifikasi, membandingkan baseline vs fine-tune, melaporkan keterbatasan, atau memutuskan ambang keyakinan/abstain untuk produk.
---

# Evaluasi Model yang Jujur (kelas timpang)

Tujuan skill ini: mencegah dua dosa evaluasi — **angka indah yang rapuh**
(accuracy tinggi karena menebak kelas mayoritas) dan **klaim tanpa dasar**
(metrik dari silver label sendiri, atau tanpa error analysis).

## 1. Ukur terhadap gold, bukan silver

Klaim performa HANYA sah bila diukur pada **gold set berlabel manusia** yang
tidak pernah dilihat model saat training. Silver label (dari LLM/heuristik)
boleh untuk training, tidak pernah untuk klaim akurasi. Bila gold dan train
berbagi sumber, pastikan tak ada kebocoran: split **per klaster near-duplikat**,
bukan per baris (komentar identik/near-identik tak boleh ada di dua sisi).

## 2. Metrik yang benar

- **Accuracy dilarang jadi metrik utama** pada kelas timpang. Jika 60% komentar
  satu kelas, model "selalu tebak kelas itu" sudah 60% akurat tapi tak berguna.
- **Metrik utama: macro-F1** (rata-rata F1 tiap kelas, bobot sama) — memaksa
  model peduli kelas minoritas.
- Laporkan **F1 per kelas + support** (jumlah contoh). Kelas dengan support < 20
  ditandai "estimasi tak stabil"; jangan menonjolkan angkanya.
- **Confusion matrix** wajib: menunjukkan kelas mana tertukar dengan mana
  (mis. sinis↔marah, kritik_peradilan↔kritik_pemerintah) — ini yang berguna,
  bukan skor tunggal.
- Sertakan **selang kepercayaan** via bootstrap (resample gold, ≥1000 iterasi)
  untuk macro-F1. Beda dua model yang selang-nya tumpang tindih = tidak konklusif.

## 3. Baseline wajib

Fine-tune baru bermakna bila mengalahkan baseline yang jujur:
1. **Majority / stratified random** — lantai teoretis.
2. **TF-IDF + linear (LogReg/SVM)** — baseline klasik yang sering mengejutkan.
3. **LLM zero-shot** (bila ada) — plafon "tanpa training".
Laporkan keempatnya berdampingan. Bila fine-tune kalah dari TF-IDF, katakan itu.

## 4. Error analysis (bagian tersulit dan terpenting)

Untuk tiap model, ambil **semua kesalahan pada gold** dan kelompokkan by pola:
- Kelas apa paling sering tertukar? (baca confusion matrix + contoh nyata)
- Apakah salah terkonsentrasi pada segmen tertentu? (teks pendek, sarkasme,
  code-mixing, emoji-only, satu fase/post)
- Tunjukkan **5–10 contoh salah beserta teksnya** — pembaca harus bisa menilai
  apakah "salah model" atau "gold-nya memang ambigu".
- Hasil error analysis → tulis di model card sebagai keterbatasan konkret.

## 5. Kalibrasi & ketidakpastian

Skor softmax mentah biasanya **overconfident**. Sebelum dipakai di produk:
- **Temperature scaling**: fit satu skalar T pada set validasi (minimkan NLL),
  bagi logit dengan T. Murah, tak mengubah prediksi, memperbaiki keandalan skor.
- **Reliability diagram + ECE** (Expected Calibration Error): bandingkan
  keyakinan rata-rata vs akurasi aktual per bin. Laporkan ECE sebelum/sesudah.
- **Ambang abstain**: pilih ambang keyakinan di mana model berkata "tidak yakin"
  alih-alih menebak. Pilih dari kurva akurasi-vs-cakupan pada validasi
  (mis. ambang yang memberi ≥85% akurasi pada bagian yang dijawab), lalu
  laporkan berapa persen data yang di-abstain. Teruskan sinyal ini ke UI.

## 6. Pelaporan keterbatasan (non-negosiabel)

Model card harus memuat, tanpa dihaluskan:
- Kelas yang lemah (macro-F1 rendah / support kecil) dan mengapa.
- Segmen input yang rawan salah (sarkasme, sindiran halus, target ganda).
- Sumber & bias data latih; ketidakterwakilan (bukan sampel acak populasi).
- Penggunaan yang dilarang (menilai individu, moderasi otomatis tanpa manusia,
  klaim opini publik).

## Anti-pola

- Melaporkan satu angka accuracy dan berhenti.
- Menyetel ambang/temperature di test set (kebocoran) alih-alih validasi.
- Menyembunyikan kelas lemah dengan hanya menampilkan macro-average.
- Menyamakan "keyakinan model tinggi" dengan "pasti benar" tanpa uji kalibrasi.
- Membandingkan model tanpa selang kepercayaan lalu mengklaim "lebih baik".
