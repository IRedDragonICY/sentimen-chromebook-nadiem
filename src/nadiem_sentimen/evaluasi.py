"""Metrik evaluasi jujur untuk kelas timpang (lihat skills/model-eval).

Fokus: macro-F1 sebagai metrik utama, F1 per-kelas + support, confusion matrix,
dan selang kepercayaan bootstrap. Accuracy dilaporkan tetapi tidak pernah
berdiri sendiri.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score


@dataclass
class LaporanEval:
    macro_f1: float
    accuracy: float
    f1_per_kelas: dict[str, float]
    support: dict[str, int]
    ci_macro_f1: tuple[float, float]
    kelas: list[str] = field(default_factory=list)
    confusion: list[list[int]] = field(default_factory=list)

    def ringkas(self) -> str:
        lo, hi = self.ci_macro_f1
        baris = [
            f"macro-F1 = {self.macro_f1:.3f}  (95% CI {lo:.3f}–{hi:.3f})",
            f"accuracy = {self.accuracy:.3f}",
            "F1 per kelas:",
        ]
        for k in self.kelas:
            tanda = "  ⚠ support kecil" if self.support[k] < 20 else ""
            baris.append(f"  {k:24s} F1={self.f1_per_kelas[k]:.3f}  n={self.support[k]}{tanda}")
        return "\n".join(baris)


def _bootstrap_macro_f1(y_true, y_pred, kelas, n=2000, seed=42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    idx = np.arange(len(yt))
    skor = np.empty(n)
    for i in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        skor[i] = f1_score(yt[s], yp[s], labels=kelas, average="macro", zero_division=0)
    return float(np.percentile(skor, 2.5)), float(np.percentile(skor, 97.5))


def evaluasi(y_true, y_pred, kelas: list[str] | None = None) -> LaporanEval:
    yt, yp = list(y_true), list(y_pred)
    if kelas is None:
        kelas = sorted(set(yt) | set(yp))
    f1_makro = f1_score(yt, yp, labels=kelas, average="macro", zero_division=0)
    f1_kelas = f1_score(yt, yp, labels=kelas, average=None, zero_division=0)
    acc = float(np.mean([a == b for a, b in zip(yt, yp)]))
    support = {k: int(sum(1 for v in yt if v == k)) for k in kelas}
    cm = confusion_matrix(yt, yp, labels=kelas)
    return LaporanEval(
        macro_f1=float(f1_makro),
        accuracy=acc,
        f1_per_kelas={k: float(f) for k, f in zip(kelas, f1_kelas)},
        support=support,
        ci_macro_f1=_bootstrap_macro_f1(yt, yp, kelas),
        kelas=list(kelas),
        confusion=cm.tolist(),
    )
