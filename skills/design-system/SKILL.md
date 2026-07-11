---
name: design-system
description: Sistem desain "top agency" untuk aplikasi Streamlit — design tokens (warna terang/gelap, tipografi, spacing, radius, shadow), komponen (KPI card, chart wrapper, filter bar, empty/loading/error state), aturan aksesibilitas & warna sentimen. Pakai saat membangun/menyeragamkan UI Streamlit yang harus terlihat digarap studio, bukan default Streamlit.
---

# Sistem Desain untuk Streamlit Kelas Agensi

Tujuan: UI yang terlihat **dirancang**, konsisten terang/gelap, aksesibel, dan
bebas kesan "dashboard default". Prinsip: sedikit token, dipakai di mana-mana.

## 1. Design tokens (satu sumber kebenaran)

Definisikan sebagai variabel CSS di satu blok `st.markdown(<style>)`, jangan
sebar warna hex di seluruh kode. Dukung terang & gelap via `@media
(prefers-color-scheme)` **dan** atribut tema Streamlit.

**Palet netral** (basis) — skala abu 50→900. Latar app bukan putih/hitam murni;
pakai off-white (`#FBFAF9`) / near-black hangat (`#14110F`) agar tak menyilaukan.

**Aksen merek**: satu warna primer + satu sekunder. Pakai untuk aksi & highlight,
bukan untuk data kategorikal.

**Warna sentimen/sikap** (kategorikal, konsisten di seluruh app, aman buta warna
— hindari merah/hijau semata; bedakan juga terang-gelap & posisi):
- pro/positif → teal-hijau `#0E9E8F`
- kontra/negatif → merah-oranye `#E8663D`
- kritik-peradilan → ungu `#8B5CF6`
- kritik-pemerintah → biru `#3B82F6`
- netral-informasional → abu-biru `#64748B`
- tak-jelas/lainnya → abu `#94A3B8`
Emosi pakai skala terpisah (marah=merah bata, duka=indigo, sinis=amber,
harapan=teal, netral=abu) agar tak bertabrakan makna dengan sikap.

**Tipografi**: satu typeface (stack sistem: `-apple-system, "Segoe UI", Roboto,
Inter, sans-serif`). Skala modular ~1.25: caption 12 · body 15 · h3 18 · h2 24 ·
h1 32 · display 44. Angka KPI besar (36–48) dengan `font-variant-numeric:
tabular-nums`. Line-height 1.5 body, 1.2 heading. Judul boleh `letter-spacing:
-0.01em`.

**Spacing**: skala 4/8 (4,8,12,16,24,32,48,64). Jarak antar-section ≥ 32.
**Radius**: 8 (kontrol), 14 (kartu), 999 (pil). **Shadow**: halus & berlapis,
mis. `0 1px 2px rgba(0,0,0,.04), 0 4px 16px rgba(0,0,0,.06)`; di gelap pakai
border tipis + shadow lebih dalam.

## 2. Menaklukkan default Streamlit

- Sembunyikan chrome bawaan bila mengganggu (menu, footer "Made with Streamlit");
  atur `.block-container` (max-width ~1100–1200px, padding-top lega).
- **Jangan** tumpuk `st.metric` polos berjejer — bungkus KPI dalam kartu ber-token
  (angka besar, label kecil, delta berwarna, ikon opsional).
- Gunakan `st.container(border=...)`/kolom untuk grid; hormati skala spacing.
- Bar filter: satu baris rapi (post, rentang tanggal, sikap), sticky bila perlu,
  dengan state tersimpan di `st.session_state`.

## 3. Komponen wajib (dan state-nya)

Setiap tampilan data harus menangani **empat state**, jangan hanya "happy path":
- **loading**: skeleton/spinner ber-teks, bukan layar kosong.
- **empty**: pesan ramah + saran aksi ("Tak ada komentar untuk filter ini —
  longgarkan rentang tanggal").
- **error**: bahasa manusiawi, tanpa traceback mentah; sarankan langkah.
- **data**: konten sesungguhnya.
KPI card, chart wrapper (judul + subjudul + catatan sumber), tabel (search,
sticky header), pill/badge sikap berwarna token.

## 4. Data-viz (selaras skill `dataviz`)

- Satu chart = satu pertanyaan; beri judul yang menyatakan temuan, bukan "Grafik 1".
- Label langsung > legenda berlebih. Sumbu jujur (mulai 0 untuk bar).
- Palet sentimen konsisten dengan token di §1; sama persis di terang & gelap.
- Angka besar (KPI) diberi konteks (perbandingan/tren), bukan telanjang.
- Grid halus, hilangkan chartjunk; anotasi peristiwa penting pada sumbu waktu.

## 5. Aksesibilitas

- Kontras teks ≥ 4.5:1 (WCAG AA); jangan sampaikan makna lewat warna saja
  (tambah label/ikon/bentuk). Uji palet sentimen pada mode terang & gelap.
- Ukuran klik ≥ 40px; fokus keyboard terlihat; alt/aria pada elemen kustom.
- Jangan pakai warna sentimen sebagai satu-satunya pembeda pada grafik.

## 6. Copywriting (Bahasa Indonesia natural)

Nada cerdas, ringkas, tepercaya, sedikit hangat. Tanpa kalimat pengisi
("Selamat datang di aplikasi kami…"), tanpa superlatif kosong, tanpa emoji
bertabur. Istilah konsisten (Sentimen, Sikap, Emosi, Target, Keyakinan). Judul
menyampaikan temuan; caption memberi konteks & disclaimer.

## Anti-pola

- Warna hex tersebar; tema gelap "belakangan" (retak & kontras jelek).
- Deretan `st.metric` default sebagai "dashboard".
- Chart tanpa pertanyaan; legenda panjang alih-alih label langsung.
- Merah/hijau sebagai satu-satunya pembeda (buta warna).
- Teks Inggris/terjemahan kaku di UI berbahasa Indonesia.
