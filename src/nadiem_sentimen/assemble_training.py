"""Menyusun set train/val/test dari gold (+ silver bila ada).

Prinsip:
- **Test & val hanya dari GOLD** (berlabel manusia) — klaim performa & kalibrasi
  harus bertumpu pada label tepercaya.
- **Train = sisa gold + seluruh silver**.
- **Group-aware**: pembagian gold dilakukan per ``klaster_dup`` sehingga komentar
  near-duplikat tak pernah melintasi split. Klaster silver dijamin lepas dari
  klaster gold oleh proses sampling, jadi tak ada kebocoran silver→test.
- Stratifikasi split gold berdasarkan ``sikap`` agar tiap split mewakili semua
  kelas sebisanya.

Jalankan:  python -m nadiem_sentimen.assemble_training
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
FRAKSI = {"test": 0.40, "val": 0.15}  # sisanya → train


def _bagi_gold(gold: pd.DataFrame) -> pd.DataFrame:
    """Tetapkan kolom ``split`` pada gold, stratified-by-sikap, group-by-klaster."""
    rng = np.random.default_rng(SEED)
    gold = gold.copy()
    gold["split"] = "train"
    # Satu keputusan per klaster (ambil sikap wakil pertama), lalu sebar ke anggota.
    per_klaster = gold.groupby("klaster_dup").agg(sikap=("sikap", "first")).reset_index()
    for sikap, grup in per_klaster.groupby("sikap"):
        klaster = grup["klaster_dup"].to_numpy().copy()
        rng.shuffle(klaster)
        n_test = int(round(len(klaster) * FRAKSI["test"]))
        n_val = int(round(len(klaster) * FRAKSI["val"]))
        tugas = {k: "test" for k in klaster[:n_test]}
        tugas.update({k: "val" for k in klaster[n_test:n_test + n_val]})
        for k, s in tugas.items():
            gold.loc[gold["klaster_dup"] == k, "split"] = s
    return gold


def susun(folder: Path) -> dict[str, pd.DataFrame]:
    gold = pd.read_parquet(folder / "gold.parquet")
    gold = _bagi_gold(gold)
    gold["sumber"] = "gold"
    if "post" not in gold.columns:
        gold["post"] = gold["id"].str.split("#").str[0]

    kolom = ["id", "klaster_dup", "post", "fase", "likes", "teks_bersih",
             "spam", "sikap", "emosi", "sumber"]

    train = [gold[gold["split"] == "train"][kolom]]
    val = gold[gold["split"] == "val"][kolom]
    test = gold[gold["split"] == "test"][kolom]

    silver_path = folder / "silver.parquet"
    if silver_path.exists():
        silver = pd.read_parquet(silver_path)
        silver["sumber"] = "silver"
        bocor = set(silver["klaster_dup"]) & set(gold["klaster_dup"])
        assert not bocor, f"klaster silver bocor ke gold: {list(bocor)[:5]}"
        train.append(silver[kolom])

    train_df = pd.concat(train, ignore_index=True)
    return {"train": train_df, "val": val, "test": test}


def main() -> None:
    folder = Path(__file__).resolve().parents[2] / "data" / "labels"
    sets = susun(folder)
    for nama, df in sets.items():
        df.to_parquet(folder / f"{nama}.parquet", index=False)
        dist = df["sikap"].value_counts().to_dict()
        print(f"{nama:5s}: {len(df):5d} baris | sumber={df['sumber'].value_counts().to_dict()}")
        print(f"       sikap={dist}")


if __name__ == "__main__":
    main()
