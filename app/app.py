"""Cermin Publik — analisis sentimen wacana kasus Chromebook (Nadiem Makarim).

Aplikasi Streamlit. Seluruh teks Bahasa Indonesia. Menyajikan hasil analisis
atas ~38.845 komentar Instagram dan inferensi langsung atas teks baru.

Jalankan:  streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import data as D
from app import grafik as G
from app.komponen import (
    disclaimer, hero, judul_bagian, kartu_komentar, kpi_grid,
    pill_emosi, pill_sikap, state_kosong,
)
from app.tema import (
    CSS, EMOSI_LABEL, FASE_LABEL, FASE_URUT, SIKAP_LABEL,
)

st.set_page_config(page_title="Cermin Publik — Sentimen Kasus Chromebook",
                   page_icon="🪧", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

DISCLAIMER_INTI = (
    "Data ini berupa komentar dari 11 unggahan Instagram — <b>bukan</b> survei yang "
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
def hal_ringkasan(df_all, d):
    hero("Analisis Sentimen Wacana Publik",
         "Cermin Publik: Kasus Pengadaan Chromebook",
         "Bagaimana warganet Instagram bereaksi terhadap kasus hukum yang menjerat "
         "Nadiem Makarim — dari penyelidikan hingga vonis. Setiap komentar dinilai "
         "sikap dan emosinya oleh model bahasa Indonesia yang dilatih khusus.")

    total = len(d)
    n_spam = int(df_all["spam"].sum())
    dom = d["sikap"].value_counts()
    dom_emosi = d["emosi"].value_counts()
    kpi_grid([
        {"label": "Komentar dianalisis", "value": f"{total:,}",
         "sub": f"{n_spam:,} spam dikecualikan"},
        {"label": "Sikap terbanyak", "value": SIKAP_LABEL[dom.index[0]] if len(dom) else "–",
         "sub": f"{dom.iloc[0] / total:.0%} dari komentar" if len(dom) else ""},
        {"label": "Emosi dominan", "value": EMOSI_LABEL[dom_emosi.index[0]] if len(dom_emosi) else "–",
         "sub": f"{dom_emosi.iloc[0] / total:.0%} dari komentar" if len(dom_emosi) else ""},
        {"label": "Rentang waktu", "value": "Sep 2025 – Jul 2026",
         "sub": "empat gelombang peristiwa"},
    ])

    disclaimer(DISCLAIMER_INTI)

    c1, c2 = st.columns([1.05, 1])
    with c1:
        judul_bagian("Komposisi sikap", "Wacana ini terarah ke banyak pihak — bukan "
                     "sekadar pro atau kontra Nadiem.")
        if total:
            st.plotly_chart(G.komposisi_sikap(d), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            state_kosong("Longgarkan filter di samping.")
    with c2:
        judul_bagian("Emosi yang mengemuka", "Nada afektif komentar secara keseluruhan.")
        if total:
            st.plotly_chart(G.emosi_bar(d), use_container_width=True,
                            config={"displayModeBar": False})

    judul_bagian("Denyut percakapan", "Volume komentar harian; lonjakan menandai "
                 "peristiwa besar dalam kasus.")
    if total:
        st.plotly_chart(G.volume_harian(d), use_container_width=True,
                        config={"displayModeBar": False})


def hal_eksplorasi(df_all, d):
    judul_bagian("Eksplorasi komentar",
                 "Telusuri komentar per sikap, emosi, dan fase. Identitas akun tidak "
                 "ditampilkan demi privasi.")
    cari = st.text_input("Cari kata dalam komentar", "")
    dd = d[d["teks_bersih"].str.contains(cari, case=False, na=False)] if cari else d
    st.caption(f"{len(dd):,} komentar cocok.")

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
        st.dataframe(tampil, use_container_width=True, height=420, hide_index=True)


def hal_tren(df_all, d):
    judul_bagian("Pergeseran sikap antar peristiwa",
                 "Membandingkan komposisi sikap pada empat gelombang: penyelidikan awal, "
                 "babak KPK, penahanan, lalu tuntutan dan vonis.")
    if len(d):
        st.plotly_chart(G.tren_sikap_fase(d), use_container_width=True,
                        config={"displayModeBar": False})
        disclaimer("Perhatikan pergeseran fokus kemarahan dari waktu ke waktu. "
                   "Proporsi dibaca per fase (setiap kolom berjumlah 100%).")
    else:
        state_kosong("Pilih minimal satu fase.")


def hal_topik(df_all, d):
    from nadiem_sentimen.topik import TOPIK_LABEL, topik_komentar
    judul_bagian("Sub-isu & arah sentimen",
                 "Isu apa yang paling ramai, dan bagaimana sikap berbeda antar isu.")
    if not len(d):
        state_kosong("Longgarkan filter.")
        return
    dd = d.copy()
    dd["topik"] = dd["teks_bersih"].map(topik_komentar)
    baris = dd.explode("topik").dropna(subset=["topik"])
    if not len(baris):
        state_kosong("Tak ada sub-isu terdeteksi.")
        return
    vol = baris["topik"].value_counts()
    pivot = (pd.crosstab(baris["topik"], baris["sikap"], normalize="index") * 100)
    pivot.index = [TOPIK_LABEL.get(t, t) for t in pivot.index]
    pivot = pivot.loc[[TOPIK_LABEL[t] for t in vol.index if t in TOPIK_LABEL]]
    st.plotly_chart(G.sikap_per_target_topik(pivot), use_container_width=True,
                    config={"displayModeBar": False})
    disclaimer("Satu komentar dapat menyinggung lebih dari satu isu. Sub-isu ditandai "
               "dengan leksikon terkurasi yang dapat diaudit, bukan model kotak-hitam.")


def hal_coba(df_all, d):
    judul_bagian("Coba model",
                 "Tempel komentar (satu per baris) untuk melihat prediksi sikap, emosi, "
                 "dan keyakinan model. Model ini dilatih pada data kasus ini — di luar "
                 "domain tersebut hasilnya kurang bermakna.")
    contoh = "Allah bersama bapak Nadiem, semangat pak\nInilah fungsi menaikkan gaji hakim 280%\nBukti korupsinya mana sih?"
    teks = st.text_area("Komentar", contoh, height=140)
    if st.button("Analisis", type="primary"):
        try:
            from nadiem_sentimen.inference import MesinSentimen
            mesin = muat_mesin()
            baris = [t for t in teks.splitlines() if t.strip()]
            for h in mesin.predict(baris):
                st.markdown(
                    f'<div class="komentar">{h.teks}<div class="meta">'
                    f'{pill_sikap(h.sikap)} {pill_emosi(h.emosi)}'
                    f' · keyakinan sikap {h.keyakinan["sikap"]:.0%}'
                    + (" · <b>model ragu</b>" if h.abstain["sikap"] else "")
                    + "</div></div>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("Model belum tersedia. Latih dulu dengan `python -m nadiem_sentimen.train`.")


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


@st.cache_resource(show_spinner="Memuat model…")
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
