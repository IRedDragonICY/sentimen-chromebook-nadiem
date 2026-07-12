"""API inferensi produksi — dipakai bersama oleh app Streamlit & skrip batch.

Kontrak sederhana::

    dari nadiem_sentimen.inference import MesinSentimen
    mesin = MesinSentimen.muat()               # dari models/sentimen-id/
    hasil = mesin.predict(["komentar 1", "..."])
    hasil[0].sikap          # -> "kritik_peradilan"
    hasil[0].keyakinan      # -> {"spam": .., "sikap": .., "emosi": ..}
    hasil[0].abstain        # -> {"sikap": bool, "emosi": bool}

Preprocessing (``bersihkan``) identik dengan saat training → tak ada train/serve
skew. Aman untuk teks kotor: emoji, campur bahasa, string kosong. Suhu kalibrasi
& ambang abstain dari ``meta.json`` diterapkan otomatis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F

from .heuristik import emosi_dari_emoji
from .model import TUGAS, KlasifikatorMultiTask
from .normalisasi import bersihkan, hanya_emoji

_MODEL_DEFAULT = Path(__file__).resolve().parents[2] / "models" / "sentimen-id"


@dataclass
class Prediksi:
    teks: str
    spam: bool
    sikap: str
    emosi: str
    keyakinan: dict[str, float]
    abstain: dict[str, bool]
    prob: dict[str, dict[str, float]]  # distribusi penuh per tugas (untuk UI)


class MesinSentimen:
    def __init__(self, model, tokenizer, meta, device):
        self.model = model
        self.tok = tokenizer
        self.meta = meta
        self.device = device
        self.suhu = meta["suhu_kalibrasi"]
        self.ambang = meta["ambang_abstain"]
        self.max_len = meta.get("max_len", 160)

    @classmethod
    def muat(cls, folder: str | Path = _MODEL_DEFAULT, device: str | None = None):
        folder = Path(folder)
        meta = json.loads((folder / "meta.json").read_text())
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(folder)
        model = KlasifikatorMultiTask(meta["encoder"])
        model.load_state_dict(torch.load(folder / "pytorch_model.bin", map_location=device))
        model.to(device).eval()
        return cls(model, tok, meta, device)

    @torch.no_grad()
    def _logits(self, teks: list[str]) -> dict[str, torch.Tensor]:
        enc = self.tok(teks, truncation=True, max_length=self.max_len,
                       padding=True, return_tensors="pt").to(self.device)
        return self.model(enc["input_ids"], enc["attention_mask"])

    def predict(self, teks: list[str], batch: int = 64) -> list[Prediksi]:
        if isinstance(teks, str):
            teks = [teks]
        bersih = [bersihkan(t) for t in teks]
        hasil: list[Prediksi] = []
        for i in range(0, len(bersih), batch):
            potong = bersih[i:i + batch]
            # String kosong tidak boleh masuk tokenizer sebagai batch kosong.
            aman = [t if t else "​" for t in potong]
            logits = self._logits(aman)
            prob = {t: F.softmax(logits[t] / self.suhu[t], dim=1).cpu() for t in TUGAS}
            for j, teks_asli in enumerate(teks[i:i + batch]):
                hasil.append(self._rakit(teks_asli, potong[j], {t: prob[t][j] for t in TUGAS}))
        return hasil

    def _rakit(self, teks_asli: str, teks_bersih: str, prob: dict[str, torch.Tensor]) -> Prediksi:
        pilih, keyakinan, abstain, dist = {}, {}, {}, {}
        for t in TUGAS:
            kelas = TUGAS[t]
            p = prob[t]
            idx = int(p.argmax())
            pilih[t] = kelas[idx]
            keyakinan[t] = float(p[idx])
            abstain[t] = keyakinan[t] < self.ambang[t]
            dist[t] = {k: float(v) for k, v in zip(kelas, p.tolist())}

        spam = pilih["spam"] == "spam"
        sikap = "tak_jelas" if spam else pilih["sikap"]
        emosi = pilih["emosi"]
        # Untuk komentar emoji-only, aturan deterministik emosi lebih andal daripada
        # model (teksnya minim) — selaras dengan guideline pelabelan.
        if not spam and hanya_emoji(teks_asli):
            sikap = "tak_jelas"
            emosi = emosi_dari_emoji(teks_asli)
            abstain["emosi"] = False
        return Prediksi(
            teks=teks_asli, spam=spam, sikap=sikap, emosi=emosi,
            keyakinan=keyakinan, abstain=abstain, prob=dist,
        )


def muat_mesin(folder: str | Path = _MODEL_DEFAULT) -> MesinSentimen:
    return MesinSentimen.muat(folder)
