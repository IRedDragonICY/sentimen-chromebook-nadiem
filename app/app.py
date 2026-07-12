"""Cermin Publik, analisis sentimen wacana kasus Chromebook (Nadiem Makarim).

Aplikasi Streamlit. Seluruh teks Bahasa Indonesia. Menyajikan hasil analisis
atas ~38.845 komentar Instagram dan inferensi langsung atas teks baru.

Jalankan:  streamlit run app/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# Streamlit menjalankan berkas ini dengan foldernya di sys.path, jadi modul
# saudara diimpor sebagai top-level (bukan paket "app", nama itu bentrok dengan
# skrip utama ini sendiri dan memicu circular import).
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import data as D
import grafik as G
from awan_kata import awan_html, hitung
from komponen import (
    disclaimer, hero, judul_bagian, kartu_komentar, kpi_grid,
    pill_emosi, pill_sikap, state_kosong,
)
from tema import (
    CSS, EMOSI_LABEL, FASE_LABEL, FASE_URUT, SIKAP_LABEL,
)

st.set_page_config(page_title="Cermin Publik: Sentimen Kasus Chromebook",
                   page_icon="🪧", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

DISCLAIMER_INTI = (
    "Data ini berupa komentar dari 11 unggahan Instagram, <b>bukan</b> survei yang "
    "mewakili opini publik Indonesia. Hasil tidak boleh digeneralisasi. Analisis "
    "bersifat netral: sistem mengukur sentimen komentar, tidak menilai bersalah atau "
    "tidaknya siapa pun, dan menjunjung asas praduga tak bersalah."
)


# ---------------------------------------------------------------- sidebar & filter
def bilah_filter(df: pd.DataFrame):
    with st.sidebar:
        st.markdown("### Filter")
        post = st.selectbox("Unggahan", ["Semua"] + sorted(df["post"].unique()))
        fase_pilih = st.multiselect(
            "Fase peristiwa", FASE_URUT, default=FASE_URUT,
            format_func=lambda f: FASE_LABEL[f])
        sikap_pilih = st.multiselect(
            "Sikap", list(SIKAP_LABEL), default=list(SIKAP_LABEL),
            format_func=lambda s: SIKAP_LABEL[s])
        sertakan_spam = st.toggle("Sertakan spam/promosi", value=False,
                                  help="Komentar judi/jualan dikecualikan dari statistik secara default.")
    return D.filter_data(df, post, fase_pilih, sikap_pilih, sertakan_spam)


# ---------------------------------------------------------------- halaman
def insight_utama(t: dict) -> list[tuple[str, str, list]]:
    """Bangun 2-3 insight naratif dari temuan.json (angka + contoh nyata)."""
    out = []
    komp = t["komposisi_sikap_persen"]

    # 1. Fokus kemarahan: peradilan vs pemerintah vs Nadiem.
    tgt = t["target"]
    if tgt.get("peradilan", 0) or tgt.get("pemerintah", 0):
        dom = max(("peradilan", "pemerintah", "kontra_nadiem"), key=lambda k: tgt.get(k, 0))
        peta = {"peradilan": "lembaga peradilan (hakim/jaksa/vonis)",
                "pemerintah": "pemerintah dan tokoh politik",
                "kontra_nadiem": "Nadiem sendiri"}
        out.append((
            f"Kemarahan paling banyak diarahkan ke {peta[dom]}.",
            f"Dari komentar non-spam, {SIKAP_LABEL['kritik_peradilan']} muncul "
            f"{komp.get('kritik_peradilan', 0)}% dan {SIKAP_LABEL['kritik_pemerintah']} "
            f"{komp.get('kritik_pemerintah', 0)}%, sementara {SIKAP_LABEL['pro_nadiem']} "
            f"{komp.get('pro_nadiem', 0)}%. Wacana ini lebih banyak menyoal keadilan proses "
            f"hukum ketimbang sekadar pro atau kontra terhadap satu orang.",
            t["contoh"].get("kritik_peradilan", []),
        ))

    # 2. Pergeseran antar fase (penahanan ke vonis).
    fase = t.get("pergeseran_fase", {})
    if "f3_mei2026" in fase and "f4_jul2026" in fase:
        pro_mei = fase["f3_mei2026"].get("pro_nadiem", 0)
        krit_jul = fase["f4_jul2026"].get("kritik_peradilan", 0)
        out.append((
            "Fokus percakapan bergeser dari simpati ke kemarahan pada peradilan.",
            f"Saat penahanan (Mei 2026), dukungan untuk Nadiem menonjol "
            f"({pro_mei}% komentar fase itu). Saat tuntutan dan vonis (Jun-Jul 2026), "
            f"kritik terhadap peradilan menguat menjadi {krit_jul}%, mencerminkan reaksi "
            f"atas berat/janggalnya vonis dan isu kenaikan gaji hakim.",
            t["contoh"].get("kritik_pemerintah", []),
        ))

    # 3. Spam & keterwakilan.
    out.append((
        "Angka sudah dibersihkan dari spam, tapi tetap bukan potret opini nasional.",
        f"{t['spam']['persen']}% komentar terdeteksi spam/promosi (mis. judi online) dan "
        f"dikecualikan dari statistik. Sisanya pun berasal dari 11 unggahan Instagram, "
        f"bukan sampel acak penduduk Indonesia, sehingga tak bisa digeneralisasi.",
        [],
    ))
    return out[:3]


def hal_ringkasan(df_all, d):
    hero("Analisis Sentimen Wacana Publik",
         "Cermin Publik: Kasus Pengadaan Chromebook",
         "Bagaimana warganet Instagram bereaksi terhadap kasus hukum yang menjerat "
         "Nadiem Makarim, dari penyelidikan hingga vonis. Setiap komentar dinilai "
         "sikap dan emosinya oleh model bahasa Indonesia yang dilatih khusus.")

    total = len(d)
    n_spam = int(df_all["spam"].sum())
    dom = d["sikap"].value_counts()
    dom_emosi = d["emosi"].value_counts()
    kpi_grid([
        {"label": "Komentar dianalisis", "value": f"{total:,}",
         "sub": f"{n_spam:,} spam dikecualikan"},
        {"label": "Sikap terbanyak", "value": SIKAP_LABEL[dom.index[0]] if len(dom) else "-",
         "sub": f"{dom.iloc[0] / total:.0%} dari komentar" if len(dom) else ""},
        {"label": "Emosi dominan", "value": EMOSI_LABEL[dom_emosi.index[0]] if len(dom_emosi) else "-",
         "sub": f"{dom_emosi.iloc[0] / total:.0%} dari komentar" if len(dom_emosi) else ""},
        {"label": "Rentang waktu", "value": "Sep 2025 - Jul 2026",
         "sub": "empat gelombang peristiwa"},
    ])

    disclaimer(DISCLAIMER_INTI)

    temuan = D.muat_temuan()
    if temuan:
        judul_bagian("Yang menonjol dari data", "Tiga pembacaan utama, disandingkan "
                     "dengan angka dan contoh komentar nyata agar bisa Anda periksa sendiri.")
        for judul, teks, contoh in insight_utama(temuan):
            st.markdown(f'<div class="card"><b>{judul}</b><br>'
                        f'<span style="color:var(--ink-2)">{teks}</span></div>',
                        unsafe_allow_html=True)
            if contoh:
                st.caption("Contoh: " + " · ".join(f'"{c[:90]}"' for c in contoh[:2]))

    c1, c2 = st.columns([1.05, 1])
    with c1:
        judul_bagian("Komposisi sikap", "Wacana ini terarah ke banyak pihak, bukan "
                     "sekadar pro atau kontra Nadiem.")
        if total:
            st.plotly_chart(G.komposisi_sikap(d), width="stretch",
                            config={"displayModeBar": False})
        else:
            state_kosong("Longgarkan filter di samping.")
    with c2:
        judul_bagian("Emosi yang mengemuka", "Nada afektif komentar secara keseluruhan.")
        if total:
            st.plotly_chart(G.emosi_bar(d), width="stretch",
                            config={"displayModeBar": False})

    judul_bagian("Denyut percakapan", "Volume komentar harian; lonjakan menandai "
                 "peristiwa besar dalam kasus.")
    if total:
        st.plotly_chart(G.volume_harian(d), width="stretch",
                        config={"displayModeBar": False})


def hal_eksplorasi(df_all, d):
    judul_bagian("Eksplorasi komentar",
                 "Telusuri komentar per sikap, emosi, dan fase. Identitas akun tidak "
                 "ditampilkan demi privasi.")
    cari = st.text_input("Cari kata dalam komentar", "")
    dd = d[d["teks_bersih"].str.contains(cari, case=False, na=False)] if cari else d
    st.caption(f"{len(dd):,} komentar cocok.")

    st.markdown(
        '<div class="section-title">Awan kata</div>'
        '<div class="section-sub">Kata yang paling sering muncul pada komentar terpilih. '
        'Ukuran huruf = frekuensi; warna = sikap yang paling dicirikan kata itu '
        '(lihat legenda). Spam dikecualikan kecuali diaktifkan di filter.</div>',
        unsafe_allow_html=True)
    n_kata = st.slider("Jumlah kata", 30, 120, 70, step=10, key="n_awan",
                       label_visibility="collapsed")
    if len(dd):
        st.markdown(awan_html(hitung(dd, n=n_kata)), unsafe_allow_html=True)
    else:
        state_kosong("Tak ada komentar pada filter ini.")

    st.markdown('<div class="section-title">Komentar teratas</div>', unsafe_allow_html=True)
    kol = st.columns(2)
    for i, (_, r) in enumerate(dd.nlargest(12, "likes").iterrows()):
        with kol[i % 2]:
            kartu_komentar(r["teks_bersih"], r["sikap"], r["emosi"], int(r["likes"]),
                           FASE_LABEL[r["fase"]], r.get("keyakinan_sikap"))

    with st.expander("Lihat sebagai tabel"):
        tampil = dd[["teks_bersih", "sikap", "emosi", "likes", "fase"]].copy()
        tampil["sikap"] = tampil["sikap"].map(SIKAP_LABEL)
        tampil["emosi"] = tampil["emosi"].map(EMOSI_LABEL)
        tampil["fase"] = tampil["fase"].map(FASE_LABEL)
        tampil.columns = ["Komentar", "Sikap", "Emosi", "Suka", "Fase"]
        st.dataframe(tampil, width="stretch", height=420, hide_index=True)


def hal_tren(df_all, d):
    judul_bagian("Pergeseran sikap antar peristiwa",
                 "Membandingkan komposisi sikap pada empat gelombang: penyelidikan awal, "
                 "babak KPK, penahanan, lalu tuntutan dan vonis.")
    if len(d):
        st.plotly_chart(G.tren_sikap_fase(d), width="stretch",
                        config={"displayModeBar": False})
        disclaimer("Perhatikan pergeseran fokus kemarahan dari waktu ke waktu. "
                   "Proporsi dibaca per fase (setiap kolom berjumlah 100%).")
    else:
        state_kosong("Pilih minimal satu fase.")


def hal_topik(df_all, d):
    try:
        from nadiem_sentimen.topik import TOPIK_LABEL, topik_komentar
    except ImportError:
        judul_bagian("Sub-isu & arah sentimen", "")
        st.info("Fitur ini memerlukan dependensi tambahan (`pip install -e .`). "
                "Lihat `requirements-dev.txt`.")
        return
    judul_bagian("Sub-isu & arah sentimen",
                 "Isu apa yang paling ramai, dan bagaimana sikap berbeda antar isu.")
    if not len(d):
        state_kosong("Longgarkan filter.")
        return
    dd = d.copy()
    dd["topik"] = dd["teks_bersih"].map(topik_komentar)
    # reset_index: explode menduplikasi label index sehingga crosstab gagal tanpa ini.
    baris = dd.explode("topik").dropna(subset=["topik"]).reset_index(drop=True)
    if not len(baris):
        state_kosong("Tak ada sub-isu terdeteksi.")
        return
    vol = baris["topik"].value_counts()
    pivot = (pd.crosstab(baris["topik"], baris["sikap"], normalize="index") * 100)
    pivot.index = [TOPIK_LABEL.get(t, t) for t in pivot.index]
    pivot = pivot.loc[[TOPIK_LABEL[t] for t in vol.index if t in TOPIK_LABEL]]
    st.plotly_chart(G.sikap_per_target_topik(pivot), width="stretch",
                    config={"displayModeBar": False})
    disclaimer("Satu komentar dapat menyinggung lebih dari satu isu. Sub-isu ditandai "
               "dengan leksikon terkurasi yang dapat diaudit, bukan model kotak-hitam.")


def _kartu_prediksi(teks, sikap, emosi, keyakinan_sikap, ragu):
    st.markdown(
        f'<div class="komentar">{teks}<div class="meta">'
        f'{pill_sikap(sikap)} {pill_emosi(emosi)}'
        f' · keyakinan sikap {keyakinan_sikap:.0%}'
        + (" · <b>model ragu</b>" if ragu else "")
        + "</div></div>", unsafe_allow_html=True)


def hal_coba(df_all, d):
    judul_bagian("Coba model",
                 "Tempel komentar (satu per baris) untuk melihat prediksi sikap, emosi, "
                 "dan keyakinan model. Inferensi berjalan di HuggingFace. Model dilatih "
                 "pada data kasus ini, di luar domain tersebut hasilnya kurang bermakna.")
    contoh = "Allah bersama bapak Nadiem, semangat pak\nInilah fungsi menaikkan gaji hakim 280%\nBukti korupsinya mana sih?"
    teks = st.text_area("Komentar", contoh, height=140)
    if not st.button("Analisis", type="primary"):
        return
    baris = [t for t in teks.splitlines() if t.strip()]
    if not baris:
        st.info("Tulis minimal satu komentar.")
        return
    try:
        with st.spinner("Menghubungi model di HuggingFace... "
                        "(bila Space baru bangun dari tidur, tunggu sekitar 30 detik)"):
            hasil = _panggil_hf(teks)
        for h in hasil:
            _kartu_prediksi(h["teks"], h["sikap"], h["emosi"],
                            h["keyakinan"]["sikap"], h["abstain"]["sikap"])
    except Exception:
        # Fallback: model lokal (mode pengembangan dengan PyTorch + bobot terpasang).
        try:
            for h in muat_mesin().predict(baris):
                _kartu_prediksi(h.teks, h.sikap, h.emosi,
                                h.keyakinan["sikap"], h.abstain["sikap"])
        except (FileNotFoundError, ImportError, OSError):
            st.warning(
                "Model di HuggingFace sedang tidak dapat dihubungi. Coba lagi "
                "sebentar, Space mungkin sedang bangun dari tidur. Model tersedia di "
                "[HuggingFace](https://huggingface.co/IRedDragonICY/indobert-sentimen-chromebook).")


def hal_metodologi(df_all, d):
    judul_bagian("Metodologi & etika", "Bagaimana data dikumpulkan, dibersihkan, dan dinilai.")
    st.markdown("""
**Data.** 38.845 komentar dari 11 unggahan Instagram tentang kasus dugaan korupsi
pengadaan Chromebook. Timestamp bermasalah (koma tak-terkutip) dan skema kolom
campur telah dinormalkan; komentar duplikat/near-duplikat dikelompokkan untuk
mencegah kebocoran evaluasi.

**Skema label.** Tiga lapis: **spam** (judi/promosi, dikecualikan dari statistik),
**sikap** (enam kelas: mendukung/menentang Nadiem, kritik peradilan, kritik
pemerintah, netral/informasi, tak jelas), dan **emosi** (marah, duka, sinis,
harapan, netral). Prinsip: mengodekan target yang tertulis eksplisit, bukan
menebak posisi politik penulis.

**Model.** Encoder bahasa Indonesia (IndoBERT) yang di-*fine-tune* multi-task,
dievaluasi jujur terhadap **gold set berlabel manusia** dengan metrik macro-F1
(bukan sekadar akurasi). Keyakinan model dikalibrasi; komentar yang membuat model
ragu ditandai, bukan dipaksa ditebak.

**Keterbatasan.** Sarkasme dan sindiran halus tetap sulit. Data bukan sampel acak
populasi. Model tidak untuk moderasi otomatis tanpa manusia, tidak untuk menilai
individu, dan tidak untuk klaim ilmiah tanpa validasi lanjutan.
    """)
    disclaimer(DISCLAIMER_INTI)


# URL Space inferensi HuggingFace. Dipanggil lewat HTTP API Gradio memakai
# `requests` saja (tanpa gradio_client) supaya dependensi Streamlit Cloud tetap
# minim dan bebas konflik. Bisa dioverride via st.secrets['hf_space_url'].
RUANG_HF = "https://ireddragonicy-sentimen-chromebook-api.hf.space"


def _panggil_hf(teks: str, timeout: int = 120) -> list[dict]:
    """Panggil endpoint /analisis Space (protokol dua langkah Gradio: POST untuk
    dapat event_id, lalu GET stream SSE untuk hasil). Kembalikan list prediksi."""
    base = RUANG_HF
    try:
        base = st.secrets.get("hf_space_url", RUANG_HF)
    except Exception:
        pass
    base = base.rstrip("/")
    r = requests.post(f"{base}/gradio_api/call/analisis",
                      json={"data": [teks]}, timeout=timeout)
    r.raise_for_status()
    eid = r.json()["event_id"]
    with requests.get(f"{base}/gradio_api/call/analisis/{eid}",
                      stream=True, timeout=timeout) as s:
        s.raise_for_status()
        ev = None
        for raw in s.iter_lines(decode_unicode=True):
            if not raw:
                continue
            if raw.startswith("event:"):
                ev = raw[6:].strip()
            elif raw.startswith("data:") and ev == "complete":
                keluar = json.loads(raw[5:].strip())
                res = keluar[0] if isinstance(keluar, list) else keluar
                return res.get("hasil", [])
    return []


@st.cache_resource(show_spinner="Memuat model...")
def muat_mesin():
    from nadiem_sentimen.inference import MesinSentimen
    return MesinSentimen.muat()


HALAMAN = {
    "Ringkasan": hal_ringkasan,
    "Eksplorasi": hal_eksplorasi,
    "Tren & Peristiwa": hal_tren,
    "Sub-isu & Target": hal_topik,
    "Coba Model": hal_coba,
    "Metodologi & Etika": hal_metodologi,
}


def main():
    if not D.tersedia():
        hero("Analisis Sentimen Wacana Publik",
             "Cermin Publik: Kasus Pengadaan Chromebook",
             "Data hasil analisis belum tersedia.")
        st.info("Jalankan pipeline terlebih dahulu: `python -m nadiem_sentimen.build_dataset`, "
                "latih model, lalu `python -m nadiem_sentimen.skor_penuh`.")
        return

    df_all = D.muat_skor()
    with st.sidebar:
        st.markdown("## Cermin Publik")
        pilihan = st.radio("Halaman", list(HALAMAN), label_visibility="collapsed")
    d = bilah_filter(df_all)
    HALAMAN[pilihan](df_all, d)


if __name__ == "__main__":
    main()
