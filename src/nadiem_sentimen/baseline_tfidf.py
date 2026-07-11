"""Baseline TF-IDF + Regresi Logistik (satu model per tugas).

Baseline klasik yang wajib dikalahkan fine-tune agar klaim "SOTA" bermakna
(lihat skills/model-eval). Cepat, transparan, tanpa GPU. Fitur karakter n-gram
membantu pada slang/typo/emoji yang kaya di data ini.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .model import TUGAS


def _pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 5), min_df=2, max_features=50000,
            sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)),
    ])


def latih(train_df: pd.DataFrame) -> dict[str, Pipeline]:
    model = {}
    for tugas in TUGAS:
        y = train_df["spam"].astype(int) if tugas == "spam" else train_df[tugas]
        pipe = _pipeline().fit(train_df["teks_bersih"], y)
        model[tugas] = pipe
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keluaran", type=Path, default=None)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    folder = root / "data" / "labels"
    keluaran = args.keluaran or (root / "models" / "baseline_tfidf.pkl")

    train_df = pd.read_parquet(folder / "train.parquet")
    model = latih(train_df)
    keluaran.parent.mkdir(parents=True, exist_ok=True)
    with open(keluaran, "wb") as f:
        pickle.dump(model, f)
    print(f"Baseline TF-IDF → {keluaran} (dilatih pada {len(train_df)} contoh)")


if __name__ == "__main__":
    main()
