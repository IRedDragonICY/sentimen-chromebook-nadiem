"""Fine-tune encoder Indonesia multi-task + kalibrasi + ambang abstain.

Menghasilkan artefak lengkap di ``models/sentimen-id/``:
- bobot model (``pytorch_model.bin``), tokenizer, konfig encoder
- ``meta.json``: label maps, suhu kalibrasi per tugas, ambang abstain,
  hash data latih, hyperparameter, metrik validasi

Penanganan ketimpangan kelas: cross-entropy berbobot invers-frekuensi.
Silver label diberi bobot contoh lebih rendah dari gold (silver lebih berisik).
Seleksi model & kalibrasi memakai set VAL (gold), bukan test.

Jalankan:  python -m nadiem_sentimen.train --encoder indobenchmark/indobert-base-p1
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from .evaluasi import evaluasi
from .model import TUGAS, KlasifikatorMultiTask

SEED = 42
BOBOT_SILVER = 0.4  # kepercayaan relatif label silver vs gold


def _set_seed(s=SEED):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


class DataKomentar(Dataset):
    def __init__(self, df: pd.DataFrame, tok, max_len=160):
        self.teks = df["teks_bersih"].tolist()
        self.tok = tok
        self.max_len = max_len
        self.y = {t: df[t if t != "spam" else "spam"].map(self._peta(t)).tolist() for t in TUGAS}
        self.bobot = (df["sumber"] == "gold").map({True: 1.0, False: BOBOT_SILVER}).tolist()

    @staticmethod
    def _peta(tugas):
        if tugas == "spam":
            return lambda v: int(v)
        return {k: i for i, k in enumerate(TUGAS[tugas])}

    def __len__(self):
        return len(self.teks)

    def __getitem__(self, i):
        enc = self.tok(self.teks[i], truncation=True, max_length=self.max_len,
                       padding="max_length", return_tensors="pt")
        item = {k: v.squeeze(0) for k, v in enc.items()}
        for t in TUGAS:
            item[f"y_{t}"] = torch.tensor(self.y[t][i])
        item["bobot"] = torch.tensor(self.bobot[i], dtype=torch.float)
        return item


def _bobot_kelas(df, tugas, device):
    kelas = TUGAS[tugas]
    if tugas == "spam":
        y = df["spam"].astype(int).tolist()
        idx = y
    else:
        peta = {k: i for i, k in enumerate(kelas)}
        idx = df[tugas].map(peta).tolist()
    hitung = np.bincount(idx, minlength=len(kelas)).astype(float)
    hitung[hitung == 0] = 1.0
    w = hitung.sum() / (len(kelas) * hitung)          # invers frekuensi
    w = np.clip(w, 0.3, 4.0)                            # jangan terlalu ekstrem
    return torch.tensor(w, dtype=torch.float, device=device)


@torch.no_grad()
def _logits_val(model, loader, device):
    model.eval()
    kumpul = {t: [] for t in TUGAS}
    label = {t: [] for t in TUGAS}
    for b in loader:
        out = model(b["input_ids"].to(device), b["attention_mask"].to(device))
        for t in TUGAS:
            kumpul[t].append(out[t].cpu())
            label[t].append(b[f"y_{t}"])
    return ({t: torch.cat(v) for t, v in kumpul.items()},
            {t: torch.cat(v) for t, v in label.items()})


def _suhu_optimal(logits, y, lo=0.5, hi=5.0):
    """Temperature scaling: cari T yang meminimalkan NLL pada val.

    Dibatasi [0.5, 5.0]: di luar rentang ini fit biasanya degenerate (model
    sangat under/over-confident pada val kecil) dan justru merusak kalibrasi.
    """
    T = torch.ones(1, requires_grad=True)
    opt = torch.optim.LBFGS([T], lr=0.05, max_iter=60)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / T.clamp(lo, hi), y)
        loss.backward()
        return loss

    opt.step(closure)
    return float(T.detach().clamp(lo, hi).item())


def _ambang_abstain(prob, y_idx, target_akurasi=0.80):
    """Ambang keyakinan minimal agar akurasi bagian terjawab ≥ target.

    Dibatasi cakupan: ambang tak boleh melebihi median keyakinan, sehingga
    minimal separuh prediksi tetap dijawab (fitur abstain harus berguna, bukan
    membungkam segalanya bila target tak tercapai).
    """
    conf, pred = prob.max(1)
    cap = float(conf.median().item())
    order = torch.argsort(conf, descending=True)
    benar = (pred == y_idx).float()[order]
    conf_sorted = conf[order]
    kumulatif = torch.cumsum(benar, 0) / torch.arange(1, len(benar) + 1)
    ok = kumulatif >= target_akurasi
    ambang = float(conf_sorted[torch.where(ok)[0].max()].item()) if ok.any() else cap
    return min(ambang, cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", default="indobenchmark/indobert-base-p1")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max_len", type=int, default=160)
    ap.add_argument("--keluaran", type=Path, default=None)
    args = ap.parse_args()

    _set_seed()
    root = Path(__file__).resolve().parents[2]
    folder = root / "data" / "labels"
    keluaran = args.keluaran or (root / "models" / "sentimen-id")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    train_df = pd.read_parquet(folder / "train.parquet")
    val_df = pd.read_parquet(folder / "val.parquet")

    tok = AutoTokenizer.from_pretrained(args.encoder)
    dl_train = DataLoader(DataKomentar(train_df, tok, args.max_len),
                          batch_size=args.batch, shuffle=True, num_workers=2)
    dl_val = DataLoader(DataKomentar(val_df, tok, args.max_len),
                        batch_size=32, num_workers=2)

    model = KlasifikatorMultiTask(args.encoder).to(device)
    bobot_kelas = {t: _bobot_kelas(train_df, t, device) for t in TUGAS}

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total = len(dl_train) * args.epochs
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total), total)
    scaler = torch.cuda.amp.GradScaler(enabled=(device == "cuda"))

    y_val_sikap = [TUGAS["sikap"][i] for i in DataKomentar(val_df, tok).y["sikap"]]
    terbaik = {"f1": -1.0, "epoch": -1}

    for epoch in range(args.epochs):
        model.train()
        for b in dl_train:
            opt.zero_grad()
            with torch.cuda.amp.autocast(enabled=(device == "cuda")):
                out = model(b["input_ids"].to(device), b["attention_mask"].to(device))
                bw = b["bobot"].to(device)
                loss = 0.0
                for t in TUGAS:
                    per = F.cross_entropy(out[t], b[f"y_{t}"].to(device),
                                          weight=bobot_kelas[t], reduction="none")
                    loss = loss + (per * bw).mean()
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            sched.step()

        logits, labels = _logits_val(model, dl_val, device)
        pred_sikap = [TUGAS["sikap"][i] for i in logits["sikap"].argmax(1).tolist()]
        lap = evaluasi(y_val_sikap, pred_sikap, TUGAS["sikap"])
        print(f"epoch {epoch}: val sikap macro-F1 = {lap.macro_f1:.3f}", flush=True)
        if lap.macro_f1 > terbaik["f1"]:
            terbaik.update(f1=lap.macro_f1, epoch=epoch)
            keluaran.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), keluaran / "pytorch_model.bin")

    # Muat model terbaik untuk kalibrasi.
    model.load_state_dict(torch.load(keluaran / "pytorch_model.bin", map_location=device))
    logits, labels = _logits_val(model, dl_val, device)
    suhu, ambang = {}, {}
    for t in TUGAS:
        suhu[t] = _suhu_optimal(logits[t], labels[t])
        prob = F.softmax(logits[t] / suhu[t], dim=1)
        ambang[t] = _ambang_abstain(prob, labels[t])

    tok.save_pretrained(keluaran)
    model.encoder.config.save_pretrained(keluaran)
    hash_data = hashlib.sha256(
        pd.util.hash_pandas_object(train_df["id"], index=False).values.tobytes()
    ).hexdigest()[:16]
    meta = {
        "encoder": args.encoder,
        "tugas": TUGAS,
        "suhu_kalibrasi": suhu,
        "ambang_abstain": ambang,
        "epoch_terbaik": terbaik["epoch"],
        "val_macro_f1_sikap": terbaik["f1"],
        "max_len": args.max_len,
        "n_train": len(train_df),
        "n_train_gold": int((train_df["sumber"] == "gold").sum()),
        "n_train_silver": int((train_df["sumber"] == "silver").sum()),
        "hash_id_train": hash_data,
        "hyperparam": {"epochs": args.epochs, "batch": args.batch, "lr": args.lr,
                       "bobot_silver": BOBOT_SILVER, "seed": SEED},
    }
    (keluaran / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\nArtefak → {keluaran}")
    print(json.dumps({"suhu": suhu, "ambang": ambang}, indent=1))


if __name__ == "__main__":
    main()
