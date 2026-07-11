"""Model klasifikasi multi-task berbasis encoder Indonesia.

Satu encoder (IndoBERT) dengan tiga kepala klasifikasi: spam (2), sikap (6),
emosi (5). Berbagi encoder membuat model kecil, cepat, dan saling menguatkan
(sinyal emosi membantu sikap, dan sebaliknya) dibanding tiga model terpisah.

Kelas & urutannya didefinisikan sekali di sini agar konsisten di training,
inferensi, dan UI.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig

KELAS_SIKAP = [
    "pro_nadiem", "kontra_nadiem", "kritik_peradilan",
    "kritik_pemerintah", "netral_informasional", "tak_jelas",
]
KELAS_EMOSI = ["marah", "duka", "sinis", "harapan", "netral"]
KELAS_SPAM = ["bukan_spam", "spam"]

TUGAS = {"spam": KELAS_SPAM, "sikap": KELAS_SIKAP, "emosi": KELAS_EMOSI}


class KlasifikatorMultiTask(nn.Module):
    def __init__(self, nama_encoder: str, dropout: float = 0.1):
        super().__init__()
        self.nama_encoder = nama_encoder
        self.encoder = AutoModel.from_pretrained(nama_encoder)
        dim = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.kepala = nn.ModuleDict(
            {tugas: nn.Linear(dim, len(kelas)) for tugas, kelas in TUGAS.items()}
        )

    def forward(self, input_ids, attention_mask):
        keluaran = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # Mean-pooling atas token yang valid — lebih stabil daripada [CLS] mentah
        # untuk encoder yang tidak dilatih dengan objektif NSP yang kuat.
        mask = attention_mask.unsqueeze(-1).float()
        rerata = (keluaran.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        rerata = self.dropout(rerata)
        return {tugas: kepala(rerata) for tugas, kepala in self.kepala.items()}

    @property
    def config(self) -> AutoConfig:
        return self.encoder.config
