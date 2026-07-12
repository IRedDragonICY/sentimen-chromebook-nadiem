"""Menghasilkan temuan utama dari data terskor → reports/temuan.json.

Setiap temuan disandingkan dengan angka + contoh komentar nyata (agar bisa
diverifikasi pembaca), sesuai brief §7.3. Dipakai untuk mengisi README dan
sebagai bahan narasi app. Semua statistik mengecualikan spam kecuali disebut.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .topik import TOPIK_LABEL, topik_komentar


def _contoh(df: pd.DataFrame, kondisi, k=3) -> list[str]:
    sub = df[kondisi].nlargest(k, "likes")
    return [t[:140] for t in sub["teks_bersih"].tolist()]


def hitung(df: pd.DataFrame) -> dict:
    total = len(df)
    n_spam = int(df["spam"].sum())
    non = df[~df["spam"]].copy()

    komposisi = (non["sikap"].value_counts(normalize=True) * 100).round(1).to_dict()
    emosi = (non["emosi"].value_counts(normalize=True) * 100).round(1).to_dict()

    # Pergeseran sikap antar fase.
    fase_tab = (pd.crosstab(non["fase"], non["sikap"], normalize="index") * 100).round(1)

    # Sentimen per target utama (peradilan vs pemerintah vs Nadiem).
    target_neg = {
        "peradilan": int((non["sikap"] == "kritik_peradilan").sum()),
        "pemerintah": int((non["sikap"] == "kritik_pemerintah").sum()),
        "kontra_nadiem": int((non["sikap"] == "kontra_nadiem").sum()),
        "pro_nadiem": int((non["sikap"] == "pro_nadiem").sum()),
    }

    # Bias engagement: apakah komentar ber-likes tinggi condong ke sikap tertentu?
    top1000 = non.nlargest(1000, "likes")
    bias_engagement = (top1000["sikap"].value_counts(normalize=True) * 100).round(1).to_dict()

    # Topik teramai + sikap dominannya.
    non["topik"] = non["teks_bersih"].map(topik_komentar)
    baris = non.explode("topik").dropna(subset=["topik"]).reset_index(drop=True)
    vol_topik = baris["topik"].value_counts().to_dict()
    sikap_topik = {}
    for t in vol_topik:
        sub = baris[baris["topik"] == t]
        sikap_topik[TOPIK_LABEL.get(t, t)] = {
            "n": int(len(sub)),
            "sikap_dominan": sub["sikap"].value_counts().idxmax(),
        }

    return {
        "total": total,
        "spam": {"n": n_spam, "persen": round(100 * n_spam / total, 1)},
        "komposisi_sikap_persen": komposisi,
        "emosi_persen": emosi,
        "pergeseran_fase": fase_tab.to_dict("index"),
        "target": target_neg,
        "bias_engagement_top1000": bias_engagement,
        "topik": sikap_topik,
        "contoh": {
            "pro_nadiem": _contoh(non, non["sikap"] == "pro_nadiem"),
            "kritik_peradilan": _contoh(non, non["sikap"] == "kritik_peradilan"),
            "kritik_pemerintah": _contoh(non, non["sikap"] == "kritik_pemerintah"),
        },
    }


def main():
    root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(root / "data" / "processed" / "skor.parquet")
    temuan = hitung(df)
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "temuan.json").write_text(json.dumps(temuan, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in temuan.items() if k != "contoh"},
                     ensure_ascii=False, indent=1)[:1500])
    print("\n→ reports/temuan.json")


if __name__ == "__main__":
    main()
