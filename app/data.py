"""Pemuatan data untuk app — di-cache, dan meng-anonimkan identitas.

Privasi (lihat brief §10): username adalah PII. Data yang dipakai UI membuang
kolom username sepenuhnya; tak ada fitur yang menonjolkan/meng-agregasi akun
per individu. Komentar tetap ditampilkan (itu wacana publik) tetapi tidak
ditautkan ke akun.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SKOR = ROOT / "data" / "processed" / "skor.parquet"
PROFIL = ROOT / "data" / "processed" / "profil.json"
TEMUAN = ROOT / "reports" / "temuan.json"


@st.cache_data(show_spinner=False)
def muat_temuan() -> dict | None:
    import json
    return json.loads(TEMUAN.read_text()) if TEMUAN.exists() else None

# Kolom yang boleh masuk UI — username sengaja TIDAK disertakan.
KOLOM_UI = ["id", "post", "waktu", "fase", "likes", "is_reply", "teks_bersih",
            "n_karakter", "hanya_emoji", "emoji", "spam", "sikap", "emosi",
            "keyakinan_sikap", "keyakinan_emosi", "abstain_sikap"]


@st.cache_data(show_spinner=False)
def muat_skor() -> pd.DataFrame:
    df = pd.read_parquet(SKOR)
    df = df[[k for k in KOLOM_UI if k in df.columns]].copy()
    df["waktu"] = pd.to_datetime(df["waktu"])
    df["tanggal"] = df["waktu"].dt.date
    return df


def tersedia() -> bool:
    return SKOR.exists()


def filter_data(df: pd.DataFrame, post=None, fase=None, sikap=None,
                sertakan_spam=False) -> pd.DataFrame:
    d = df
    if not sertakan_spam:
        d = d[~d["spam"]]
    if post and post != "Semua":
        d = d[d["post"] == post]
    if fase:
        d = d[d["fase"].isin(fase)]
    if sikap:
        d = d[d["sikap"].isin(sikap)]
    return d
