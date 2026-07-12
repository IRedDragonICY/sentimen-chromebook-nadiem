"""Pelabelan silver set via anotator LLM lokal (Ollama).

Melabeli kandidat silver terstratifikasi untuk data latih. Emoji-only sudah
disaring saat sampling (ditangani aturan deterministik), jadi di sini fokus
pada komentar bertekst. Hasil yang gagal di-parse dibuang (tidak ditebak).

Jalankan:  python -m nadiem_sentimen.label_silver --model qwen3.5:4b
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from .anotator_llm import labeli_satu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--maks", type=int, default=None, help="batasi jumlah (uji cepat)")
    ap.add_argument("--few_shot", action="store_true", help="pakai exemplar few-shot (default zero-shot)")
    ap.add_argument("--keluaran", default="silver.parquet")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    folder = root / "data" / "labels"
    todo = pd.read_csv(folder / "silver_todo.csv")
    if args.maks:
        todo = todo.head(args.maks)

    baris, gagal, t0 = [], 0, time.time()
    for i, r in enumerate(todo.itertuples(), 1):
        pred = labeli_satu(r.teks_bersih, args.model, few_shot=args.few_shot)
        if pred is None:
            gagal += 1
            continue
        baris.append({
            "id": r.id, "klaster_dup": r.klaster_dup,
            "post": r.id.split("#")[0], "fase": r.fase,
            "likes": r.likes, "teks_bersih": r.teks_bersih,
            "spam": int(pred.spam), "sikap": pred.sikap, "emosi": pred.emosi,
        })
        if i % 100 == 0:
            laju = i / (time.time() - t0)
            print(f"  {i}/{len(todo)}  ({laju:.1f}/dtk, gagal={gagal})", flush=True)

    df = pd.DataFrame(baris)
    df.to_parquet(folder / args.keluaran, index=False)
    print(f"\nSilver: {len(df)} berlabel, {gagal} gagal-parse dibuang")
    print(df["sikap"].value_counts().to_string())


if __name__ == "__main__":
    main()
