#!/usr/bin/env python3
"""Panel pemantau live untuk pelabelan silver (ornith via Ollama).

Menyatukan tiga sumber sinyal menjadi satu tampilan:
- ``silver.log``        → counter progres (dicetak tiap 100 komentar).
- ``ollama.log``        → satu baris ``POST /api/chat`` per komentar; dipakai
                          untuk throughput 10 detik terakhir & estimasi indeks
                          terkini (lebih halus daripada counter per-100).
- ``silver_todo.csv``   → teks komentar; indeks terkini dipetakan ke barisnya
                          sehingga terlihat komentar apa yang sedang dilabeli.

Pakai:  python bin/pantau_silver.py           # sekali (snapshot)
        python bin/pantau_silver.py --loop    # refresh tiap 3 dtk (Ctrl-C berhenti)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "data" / "labels" / "silver_todo.csv"
HASIL = ROOT / "data" / "labels" / "silver.parquet"
SCRATCH = Path(
    "/tmp/claude-1000/-home-ireddragonicy-Data-projects-corruption-nadiem"
    "/3e61293b-fd6a-4fac-bc6a-92375e12d60c/scratchpad"
)
SILVER_LOG = SCRATCH / "silver.log"
OLLAMA_LOG = SCRATCH / "ollama.log"
TOTAL = 5975

_GIN = re.compile(r"\[GIN\] (\d{4}/\d{2}/\d{2} - \d{2}:\d{2}:\d{2}).*POST\s+\"/api/chat\"")
_PROG = re.compile(r"(\d+)/\d+\s+\(([\d.]+)/dtk, gagal=(\d+)\)")


def _ekor(path: Path, n_byte=200_000) -> str:
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - n_byte))
        return f.read().decode("utf-8", "ignore")


def _progres() -> tuple[int, float, int]:
    """(jumlah, laju/dtk, gagal) dari baris progres terakhir; nol bila belum ada."""
    cocok = _PROG.findall(_ekor(SILVER_LOG))
    if not cocok:
        return 0, 0.0, 0
    n, laju, gagal = cocok[-1]
    return int(n), float(laju), int(gagal)


def _throughput_ollama(jendela=10) -> tuple[int, int]:
    """(POST dalam `jendela` detik terakhir, total POST) dari ollama.log."""
    stempel = _GIN.findall(_ekor(OLLAMA_LOG))
    if not stempel:
        return 0, 0
    now = datetime.now()
    baru = 0
    for s in stempel:
        try:
            t = datetime.strptime(s, "%Y/%m/%d - %H:%M:%S")
        except ValueError:
            continue
        if 0 <= (now - t).total_seconds() <= jendela:
            baru += 1
    return baru, len(stempel)


def _gpu() -> str:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        pakai, total, util = [x.strip() for x in out.split(",")]
        return f"{pakai} / {total} MiB  ·  util {util}%"
    except Exception:
        return "tak terbaca"


def _proc_hidup() -> str:
    out = subprocess.run(["pgrep", "-af", "label_silver"], capture_output=True, text=True).stdout
    return "HIDUP" if "label_silver" in out else "MATI"


def _bar(frac: float, lebar=42) -> str:
    isi = int(frac * lebar)
    return "█" * isi + "░" * (lebar - isi)


def _fmt_dtk(d: float) -> str:
    d = int(d)
    j, sisa = divmod(d, 3600)
    m, s = divmod(sisa, 60)
    return f"{j}j {m:02d}m" if j else f"{m}m {s:02d}d"


def _komentar_sekitar(idx: int, todo_teks: list[str], n=5) -> list[tuple[int, str]]:
    """Teks pada indeks 1-based `idx` dan beberapa sesudahnya."""
    hasil = []
    for k in range(idx, min(idx + n, len(todo_teks) + 1)):
        if 1 <= k <= len(todo_teks):
            t = todo_teks[k - 1].replace("\n", " ")
            hasil.append((k, t[:96] + ("…" if len(t) > 96 else "")))
    return hasil


def render(todo_teks: list[str]) -> str:
    if HASIL.exists():
        return "✅ SELESAI — silver.parquet sudah ditulis. Pipeline lanjut jalan.\n"

    n, laju, gagal = _progres()
    baru10, total_post = _throughput_ollama()
    # Indeks terkini: pakai yang lebih maju antara counter-log & jumlah POST ollama.
    idx = max(n, total_post) if total_post else n
    idx = min(max(idx, 1), TOTAL)
    frac = idx / TOTAL
    sisa = TOTAL - idx
    eta = _fmt_dtk(sisa / laju) if laju > 0 else "—"
    laju_menit = f"{laju*60:.0f}/mnt" if laju else "—"
    fail_pct = f"{gagal/idx*100:.1f}%" if idx else "0%"

    L = []
    L.append("┌─ PELABELAN SILVER · ornith:9b ───────────────────────────────────┐")
    L.append(f"  {_bar(frac)}  {frac*100:5.1f}%")
    L.append(f"  {idx:>4}/{TOTAL} komentar   sisa {sisa}   ETA ~{eta}")
    L.append(f"  laju {laju_menit}   ·   throughput 10dtk: {baru10} komentar   ·   proses {_proc_hidup()}")
    L.append(f"  gagal-parse {gagal} ({fail_pct})   ·   GPU {_gpu()}")
    L.append("├─ sedang dilabeli sekarang ───────────────────────────────────────┤")
    for k, t in _komentar_sekitar(idx, todo_teks):
        tanda = "▶" if k == idx else " "
        L.append(f"  {tanda} #{k:<4} {t}")
    L.append("└──────────────────────────────────────────────────────────────────┘")
    L.append(f"  {datetime.now():%H:%M:%S}  ·  label ditulis ke disk hanya saat semua selesai")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="refresh tiap 3 detik")
    ap.add_argument("--jeda", type=float, default=3.0)
    args = ap.parse_args()

    import pandas as pd
    todo_teks = pd.read_csv(TODO)["teks_bersih"].fillna("").astype(str).tolist()

    if not args.loop:
        print(render(todo_teks))
        return
    try:
        while True:
            print("\033[2J\033[H", end="")  # bersihkan layar
            print(render(todo_teks))
            if HASIL.exists():
                break
            time.sleep(args.jeda)
    except KeyboardInterrupt:
        print("\n(pemantauan dihentikan; proses labeling tetap jalan)")


if __name__ == "__main__":
    main()
