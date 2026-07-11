"""Sampling terstratifikasi untuk gold set dan silver set.

Prinsip anti-bocor: unit sampling adalah WAKIL KLASTER near-duplikat (anggota
ber-likes tertinggi), bukan baris mentah. Klaster yang wakilnya masuk gold
tidak akan pernah dipakai untuk training — pemisahan ditegakkan lewat
``klaster_dup``, bukan lewat id baris.

Strata gold: fase peristiwa × tipe teks (emoji/pendek/normal/panjang) × tier
likes, dengan kuota khusus untuk komentar paling disukai (wajah wacana),
indikasi spam, dan emoji-only. Alokasi proporsional terhadap massa baris yang
diwakili tiap stratum (sisa terbesar), dengan lantai per fase agar fase kecil
(Sep 2025, n=114) tetap terwakili.

Jalankan:
  python -m nadiem_sentimen.sampling gold    → data/labels/gold_todo.csv
  python -m nadiem_sentimen.sampling silver  → data/labels/silver_todo.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .heuristik import indikasi_spam

SEED = 42
LANTAI_FASE = {"f1_sep2025": 30, "f2_awal2026": 60, "f3_mei2026": 120, "f4_jul2026": 200}


def _tipe_teks(hanya_emoji: bool, n: int) -> str:
    if hanya_emoji:
        return "emoji"
    return "pendek" if n <= 25 else ("normal" if n <= 200 else "panjang")


def _tier_likes(likes: int) -> str:
    return "0" if likes == 0 else ("1-99" if likes < 100 else "100+")


def wakil_klaster(df: pd.DataFrame) -> pd.DataFrame:
    """Satu wakil per klaster duplikat (anggota paling disukai), plus strata."""
    rep = df.loc[df.groupby("klaster_dup")["likes"].idxmax()].copy()
    rep = rep[rep["n_karakter"] > 0]
    rep["tipe"] = [_tipe_teks(h, n) for h, n in zip(rep["hanya_emoji"], rep["n_karakter"])]
    rep["tier"] = rep["likes"].map(_tier_likes)
    rep["spam_ind"] = rep["teks_bersih"].map(indikasi_spam)
    return rep


def _alokasi_proporsional(bobot: pd.Series, total: int) -> dict:
    """Alokasi kuota metode sisa terbesar; setiap stratum berbobot dapat ≥1."""
    if bobot.empty or total <= 0:
        return {}
    pecahan = bobot / bobot.sum() * total
    dasar = pecahan.astype(int).clip(lower=1)
    sisa = total - dasar.sum()
    if sisa > 0:
        urutan = (pecahan - pecahan.astype(int)).sort_values(ascending=False)
        for k in urutan.index[:sisa]:
            dasar[k] += 1
    return dasar.to_dict()


def sampel_gold(df: pd.DataFrame, n_target: int = 600) -> pd.DataFrame:
    rep = wakil_klaster(df)
    bagian = []

    # Komentar paling disukai wajib masuk: merekalah wajah wacana di produk,
    # dan kesalahan model pada komentar viral paling mahal harganya.
    top = rep.nlargest(30, "likes")
    bagian.append(top)
    sisa = rep.drop(top.index)

    for kolom, nilai, kuota in (("spam_ind", True, 40), ("tipe", "emoji", 60)):
        kandidat = sisa[sisa[kolom] == nilai]
        ambil = kandidat.sample(min(kuota, len(kandidat)), random_state=SEED)
        bagian.append(ambil)
        sisa = sisa.drop(ambil.index)

    # Sisanya proporsional terhadap massa baris yang diwakili tiap stratum.
    n_sisa = n_target - sum(len(b) for b in bagian)
    sisa_nonemoji = sisa[sisa["tipe"] != "emoji"]
    for fase, grup in sisa_nonemoji.groupby("fase"):
        jatah_fase = max(
            LANTAI_FASE.get(fase, 0),
            int(n_sisa * grup["ukuran_klaster"].sum() / sisa_nonemoji["ukuran_klaster"].sum()),
        )
        bobot = grup.groupby(["tipe", "tier"])["ukuran_klaster"].sum()
        for strata, kuota in _alokasi_proporsional(bobot, jatah_fase).items():
            kandidat = grup[(grup["tipe"] == strata[0]) & (grup["tier"] == strata[1])]
            bagian.append(kandidat.sample(min(kuota, len(kandidat)), random_state=SEED))

    gold = pd.concat(bagian).drop_duplicates("id")
    # Urutan acak: pass pelabelan tidak boleh berjalan stratum demi stratum,
    # supaya drift kelelahan/adaptasi anotator tidak menumpuk di satu kelas.
    return gold.sample(frac=1, random_state=SEED)


def sampel_silver(df: pd.DataFrame, gold: pd.DataFrame, n_target: int = 3000) -> pd.DataFrame:
    rep = wakil_klaster(df)
    rep = rep[~rep["klaster_dup"].isin(gold["klaster_dup"])]
    # Emoji-only tidak perlu label manual (aturan deterministik menanganinya);
    # spam-indikasi tetap disertakan agar detektor belajar dari label, bukan regex.
    rep = rep[rep["tipe"] != "emoji"]
    bobot = rep.groupby(["fase", "tipe", "tier"])["ukuran_klaster"].sum()
    bagian = []
    for strata, kuota in _alokasi_proporsional(bobot, n_target).items():
        kandidat = rep[
            (rep["fase"] == strata[0]) & (rep["tipe"] == strata[1]) & (rep["tier"] == strata[2])
        ]
        bagian.append(kandidat.sample(min(kuota, len(kandidat)), random_state=SEED))
    silver = pd.concat(bagian).drop_duplicates("id")
    return silver.sample(frac=1, random_state=SEED)


KOLOM_TODO = ["id", "klaster_dup", "fase", "likes", "ukuran_klaster", "teks_bersih"]


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["gold", "silver"])
    ap.add_argument("--n", type=int, default=None)
    args = ap.parse_args()

    df = pd.read_parquet(root / "data" / "processed" / "komentar.parquet")
    keluaran = root / "data" / "labels"
    keluaran.mkdir(parents=True, exist_ok=True)

    if args.mode == "gold":
        hasil = sampel_gold(df, args.n or 600)
    else:
        gold = pd.read_csv(keluaran / "gold_todo.csv")
        hasil = sampel_silver(df, gold, args.n or 3000)

    path = keluaran / f"{args.mode}_todo.csv"
    hasil[KOLOM_TODO].to_csv(path, index=False)
    print(f"OK: {len(hasil)} kandidat → {path}")
    print(hasil.groupby(["fase"]).size().to_string())


if __name__ == "__main__":
    main()
