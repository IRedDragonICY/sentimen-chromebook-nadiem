"""Evaluasi jujur semua model pada GOLD TEST → reports/evaluasi.json + ringkasan.

Membandingkan (lihat skills/model-eval):
- majority baseline (lantai)
- TF-IDF + LogReg
- LLM zero-shot (qwen/ornith, bila server hidup)
- model fine-tune (bila artefak ada)

Untuk tiap model & tiap tugas: macro-F1 + CI bootstrap, F1 per-kelas, confusion
matrix, dan contoh kesalahan nyata. Semua diukur pada gold test yang tak pernah
dilihat model saat training.

Jalankan:  python -m nadiem_sentimen.evaluate [--llm qwen3.5:4b]
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import pandas as pd

from .evaluasi import evaluasi
from .model import TUGAS


def _kolom_benar(df, tugas):
    return df["spam"].astype(int).astype(str) if tugas == "spam" else df[tugas]


def _eval_prediksi(y_true, y_pred, kelas):
    lap = evaluasi(list(y_true), list(y_pred), kelas)
    return {
        "macro_f1": lap.macro_f1,
        "accuracy": lap.accuracy,
        "ci95": lap.ci_macro_f1,
        "f1_per_kelas": lap.f1_per_kelas,
        "support": lap.support,
        "confusion": lap.confusion,
        "kelas": lap.kelas,
    }


def eval_baseline(test_df, path):
    with open(path, "rb") as f:
        model = pickle.load(f)
    hasil = {}
    for tugas in TUGAS:
        kelas = ["0", "1"] if tugas == "spam" else TUGAS[tugas]
        pred = model[tugas].predict(test_df["teks_bersih"])
        pred = [str(p) for p in pred]
        y = _kolom_benar(test_df, tugas)
        hasil[tugas] = _eval_prediksi(y, pred, kelas)
    return hasil


def eval_finetune(test_df, folder):
    from .inference import MesinSentimen
    mesin = MesinSentimen.muat(folder)
    pred = mesin.predict(test_df["teks_bersih"].tolist())
    hasil, salah = {}, []
    for tugas in TUGAS:
        kelas = ["0", "1"] if tugas == "spam" else TUGAS[tugas]
        if tugas == "spam":
            yp = [str(int(p.spam)) for p in pred]
        else:
            yp = [getattr(p, tugas) for p in pred]
        y = _kolom_benar(test_df, tugas)
        hasil[tugas] = _eval_prediksi(y, yp, kelas)
    for r, p in zip(test_df.itertuples(), pred):
        if p.sikap != r.sikap:
            salah.append({"teks": r.teks_bersih[:120], "gold": r.sikap,
                          "prediksi": p.sikap, "keyakinan": round(p.keyakinan["sikap"], 2)})
    return hasil, salah[:12]


def eval_llm(test_df, model_llm):
    from .anotator_llm import labeli_banyak
    pred = labeli_banyak(test_df["teks_bersih"].tolist(), model_llm, few_shot=False)
    ok = [(r, p) for r, p in zip(test_df.itertuples(), pred) if p is not None]
    hasil = {}
    for tugas in TUGAS:
        kelas = ["0", "1"] if tugas == "spam" else TUGAS[tugas]
        if tugas == "spam":
            yp = [str(int(p.spam)) for _, p in ok]
        else:
            yp = [getattr(p, tugas) for _, p in ok]
        y = [(_kolom_benar(pd.DataFrame([r._asdict()]), tugas)).iloc[0] for r, _ in ok]
        hasil[tugas] = _eval_prediksi(y, yp, kelas)
    hasil["_n_terlabel"] = len(ok)
    return hasil


def eval_majority(train_df, test_df):
    hasil = {}
    for tugas in TUGAS:
        kelas = ["0", "1"] if tugas == "spam" else TUGAS[tugas]
        mayor = str(_kolom_benar(train_df, tugas).mode().iloc[0])
        y = _kolom_benar(test_df, tugas)
        hasil[tugas] = _eval_prediksi(y, [mayor] * len(test_df), kelas)
    return hasil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", default=None, help="model ollama untuk baseline zero-shot")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    folder = root / "data" / "labels"
    train_df = pd.read_parquet(folder / "train.parquet")
    test_df = pd.read_parquet(folder / "test.parquet")

    lap = {"n_test": len(test_df), "model": {}}
    lap["model"]["majority"] = eval_majority(train_df, test_df)

    base = root / "models" / "baseline_tfidf.pkl"
    if base.exists():
        lap["model"]["tfidf_logreg"] = eval_baseline(test_df, base)

    ft = root / "models" / "sentimen-id"
    if (ft / "meta.json").exists():
        h, salah = eval_finetune(test_df, ft)
        lap["model"]["finetune"] = h
        lap["error_sikap_finetune"] = salah

    if args.llm:
        lap["model"][f"llm_{args.llm}"] = eval_llm(test_df, args.llm)

    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "evaluasi.json").write_text(json.dumps(lap, ensure_ascii=False, indent=2))

    print(f"GOLD TEST n={len(test_df)}\n" + "=" * 60)
    for nama, h in lap["model"].items():
        print(f"\n### {nama}")
        for tugas in TUGAS:
            m = h[tugas]
            lo, hi = m["ci95"]
            print(f"  {tugas:6s} macroF1={m['macro_f1']:.3f} [{lo:.3f}-{hi:.3f}] acc={m['accuracy']:.3f}")
    print(f"\n→ reports/evaluasi.json")


if __name__ == "__main__":
    main()
