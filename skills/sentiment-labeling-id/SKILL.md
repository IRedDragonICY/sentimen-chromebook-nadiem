---
name: sentiment-labeling-id
description: Pedoman dan prosedur pelabelan sikap/emosi komentar media sosial berbahasa Indonesia untuk wacana terpolarisasi multi-target (kasus hukum, isu politik). Pakai saat merancang taksonomi label, melabeli gold/silver set, menulis prompt LLM-annotator, atau mengukur kesepakatan anotasi pada teks informal Indonesia (slang, emoji, sarkasme, code-mixing).
---

# Pelabelan Sikap & Emosi — Komentar Media Sosial Indonesia

Prosedur ini lahir dari pelabelan ±38 ribu komentar Instagram tentang kasus
pengadaan Chromebook (2025–2026), tetapi kaidahnya berlaku untuk wacana
Indonesia terpolarisasi mana pun yang sentimennya terarah ke banyak target.

## Prinsip yang tidak boleh dilanggar

1. **Kodekan yang terlihat, bukan yang ditebak.** Label menyatakan siapa yang
   dikritik/didukung *di dalam teks* — bukan posisi politik laten penulisnya.
   Komentar "Inilah fungsi dari menaikkan gaji para hakim 280%" menyerang
   hakim secara eksplisit dan *mungkin* tersirat membela terdakwa; yang
   dikodekan hanya yang eksplisit: `kritik_peradilan`.
2. **Jangan melabel stance dari konteks postingan.** Classifier belajar dari
   teks. Bila label bisa ditentukan hanya karena kita tahu komentar itu ada di
   bawah post tertentu, model tidak belajar apa-apa dari teksnya — itu noise
   yang menyamar sebagai sinyal. Konteks post boleh dipakai untuk memahami
   *makna kata* (mis. "Mulia?" mengejek sebutan "Yang Mulia" untuk hakim),
   bukan untuk mengisi target yang tidak ada di teks.
3. **Abstain adalah label yang sah.** `tak_jelas` bukan kegagalan anotator;
   memaksakan tebakan itulah kegagalan.
4. **Netralitas kasus.** Anotator tidak menilai siapa yang benar. Tuduhan
   dikodekan sebagai tuduhan.

## Taksonomi tiga lapis

Setiap komentar mendapat tiga field independen:

### Lapis 1 — `spam` (biner)
Konten komersial non-substantif: judi online (varian huruf mewah
"𝗞𝗢𝗟𝗘𝗠𝗔𝗫", testimoni menang), jasa (bor sumur, sedot WC), olshop,
giveaway, promosi akun/link. Spam **dikecualikan** dari statistik sikap/emosi
tetapi proporsinya selalu dilaporkan. Gibberish non-komersial ("rpy. 4r r.")
BUKAN spam — itu `tak_jelas`.

### Lapis 2 — `sikap` (label tunggal, 6 kelas)

| Kode | Definisi | Contoh nyata |
|---|---|---|
| `pro_nadiem` | Simpati, pembelaan, doa untuknya, framing dizolimi/dikorbankan, pembelaan substantif atas kebijakan/pengadaan, duka verbal atas peristiwa yang menimpanya | "Allah bersama bapak Nadiem" · "Trs bukti bukti korupsinya mana ?" · "Dan plot twistnya, ternyata Chromebooknya bisa dipake dan mempermudah guru2 di area 3T" · "Sedih bgt lihat berita ini" |
| `kontra_nadiem` | Menganggap bersalah/pantas dihukum, dukungan pada penuntutan, kritik kebijakan/pribadinya, ejekan padanya | "Kurikulum mu yang merusak generasi muda" · "mending si Nadiem fokus ngurus go jek aja" · "Semangat kerja terus bapak 2 jaksa" |
| `kritik_peradilan` | Kemarahan/sinisme pada hakim, vonis, proses hukum, aparat penegak hukum sebagai pelaku proses; termasuk keluhan selektivitas hukum yang mengontraskan kasus ini dengan kasus lain | "Lucu Hukum di Negeri ini 😂😂" · "Inilah fungsi dari menaikkan gaji para hakim 280%." · "Mulia ?" · "Ikn merugikan negara kok Jokowi GK di adili" |
| `kritik_pemerintah` | Menyasar presiden/pemerintah/tokoh/partai/program politik nasional tanpa kontras eksplisit ke perlakuan kasus ini | "TURUNKAN PRABOWO" · "Pemerintah hancur semenjak ada jokowi" · "Masih menunggu Mulyono untuk segera diadili😌" |
| `netral_informasional` | Informasi, pertanyaan tulus, diskusi teknis/analitis tanpa keberpihakan yang terbaca | "e-katalog operatornya manusia bukan ?" · "Sebagai referensi boleh dengar podcast Helmy Yahya dan Prof. Mahfud MD" |
| `tak_jelas` | Tidak ada posisi yang bisa dibaca dari teksnya sendiri: emoji-only, sangat pendek, gibberish, off-topic | "😭😭😭😭" · "Pada kaget ini teh?" · "rpy. 4r r." |

### Lapis 3 — `emosi` (label tunggal, 5 kelas)

| Kode | Cakupan | Penanda khas |
|---|---|---|
| `marah` | Kemarahan, kecaman, ancaman pertanggungjawaban, makian | "AZAB YG PEDIH🔥", 😡🤬, huruf kapital penuh |
| `duka` | Sedih, simpati, kehilangan, keprihatinan | 😭😢💔🥀🥺, "sedih banget", "heartbroken" |
| `sinis` | Sarkasme, ejekan, tawa pahit, ironi | 😂🤣 pada konteks serius, "Lucu hukum di negeri ini", pujian semu |
| `harapan` | Dukungan, semangat, doa optimis, ajakan solidaritas | "Ayo guys kita harus berisik terus demi keadilan", 🙏🤲💪, "insyaallah kebenaran terungkap" |
| `netral` | Tanpa muatan afektif yang menonjol | pertanyaan datar, informasi |

## Aturan preseden (multi-target dalam satu komentar)

1. Label target yang **paling eksplisit** dikritik/didukung dalam teks.
2. Bila dua target sama eksplisit, prioritas kedekatan dengan kasus:
   `pro/kontra_nadiem` → `kritik_peradilan` → `kritik_pemerintah`.
3. Whataboutism: tuntutan mengadili tokoh lain **dengan** kontras eksplisit ke
   kasus ini ("kok X gak diadili") = `kritik_peradilan` (keluhan selektivitas);
   **tanpa** kontras = `kritik_pemerintah`.
4. Emosi: pilih yang dominan; bila sarkasme membungkus kemarahan, pilih
   `sinis` (bentuk penyampaian menang atas muatan).

## Aturan batas-kasus

- **Sarkasme** — label makna yang dimaksud, bukan literal. "Petantang
  petenteng nya dapet banget 😅👍🏻" = ejekan → sikap mengikuti target ejekan,
  emosi `sinis`.
- **Emoji-only** — sikap SELALU `tak_jelas` (target tak terbaca dari teks;
  lihat Prinsip 2). Emosi dipetakan deterministik dari emoji dominan pertama:
  😭😢💔🥀🥺🥹🥲 → `duka`; 😂🤣 → `sinis`; 😡🤬💢 → `marah`;
  🙏🤲💪✊❤🔥 → `harapan`; lainnya → `netral`. Agregat "gelombang duka"
  boleh dinarasikan di produk, tetapi sebagai ekspresi emosi, bukan klaim
  stance per komentar.
- **Pertanyaan** — retoris yang menyiratkan posisi ("bukti korupsinya mana?")
  = posisi itu; pertanyaan informasi tulus = `netral_informasional`.
- **Doa** — doa kebaikan untuk terdakwa = `pro_nadiem`/`harapan`; doa
  azab/karma untuk hakim = `kritik_peradilan`/`marah` (bentuk doa tidak
  menetralkan muatan).
- **Code-mixing / bahasa asing** — label berdasarkan makna, bahasa tidak
  relevan. "I am so heartbroken and sorry." = duka verbal atas peristiwa →
  `pro_nadiem`/`duka`.
- **Duka verbal vs duka emoji** — duka *verbal* yang merujuk peristiwa/orang
  ("sedih lihat berita ini") cukup untuk `pro_nadiem`; duka tanpa rujukan
  tekstual apa pun (emoji saja) tidak.
- **Ujaran kebencian/rasis** terhadap tokoh = sikap sesuai target (mis.
  `kontra_nadiem`) + emosi `marah`; JANGAN buat kelas khusus dadakan, tapi
  tandai di kolom `catatan` untuk kurasi tampilan produk.
- **Kosong/gibberish** — `tak_jelas`/`netral`, bukan spam.

## Prosedur gold set

1. **Stratifikasi** sampel pada dimensi yang menggerakkan kesulitan: fase
   peristiwa × tipe teks (emoji-only / ≤25 karakter / normal / panjang) ×
   tier likes (0, 1–99, ≥100) × indikasi spam. Sampel dari **wakil klaster
   near-duplikat**, bukan baris mentah, agar gold tidak bocor ke train.
2. **Pass ganda**: labeli seluruh gold, jeda, labeli ulang subsampel ≥20%
   secara buta (tanpa melihat pass pertama). Laporkan kesepakatan test–retest
   (persen setuju + Cohen's κ) per lapis label.
3. **Adjudikasi**: ketidaksepakatan dibaca ulang dengan guideline; bila
   guideline tidak menjawab, guideline yang direvisi (dan seluruh label kelas
   terdampak diperiksa ulang) — bukan kasusnya yang dipaksa masuk.
4. **Jujur soal anotator**: bila anotasi dikerjakan satu pihak (manusia
   tunggal atau LLM), tulis itu di model card sebagai keterbatasan terukur —
   jangan menyamarkannya sebagai konsensus panel.

## Template prompt LLM-annotator (untuk pelabelan terprogram)

Gunakan guideline di atas verbatim sebagai system prompt, lalu per batch:

```
Labeli komentar berikut sesuai pedoman. Jawab HANYA dengan JSONL:
{"id": "...", "spam": bool, "sikap": "...", "emosi": "...", "catatan": "..."}
Kolom catatan hanya diisi untuk kasus batas (sarkasme yang kamu tafsirkan,
ujaran kebencian, keraguan). Bila ragu antara dua kelas sikap, pilih
tak_jelas — jangan menebak.

[id] teks
...
```

Sisipkan 2–5% **duplikat tersembunyi** antar batch untuk mengukur konsistensi;
buang batch yang konsistensinya < 90% dan labeli ulang setelah memperbaiki
prompt/guideline.

## Anti-pola

- Melabel polaritas pos/neg/netral polos pada wacana multi-target — agregatnya
  menyesatkan (marah pada hakim ≠ negatif pada terdakwa).
- Menyimpulkan stance dari emoji atau dari post tempat komentar menempel.
- Membuang komentar emoji-only sebagai noise — 11% data ini emoji-only dan
  itulah pembawa sinyal duka terbesar.
- Deteksi spam dengan exact-match keyword — pelaku memakai huruf Unicode
  mewah, spasi sisipan, dan homoglyph; normalisasi NFKC dulu.
- Mengklaim akurasi dari kesepakatan dengan silver label sendiri.
