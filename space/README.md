---
title: Sentimen Chromebook Nadiem API
emoji: 🪞
colorFrom: indigo
colorTo: gray
sdk: gradio
app_file: app.py
pinned: false
license: cc-by-nc-sa-4.0
short_description: API inferensi IndoBERT (spam/sikap/emosi) untuk Streamlit
---

# Sentimen Chromebook-Nadiem - API inferensi

Backend inferensi untuk dashboard [Cermin Publik](https://sentimen-nadiem.streamlit.app/).
Memuat model IndoBERT multi-task (satu encoder, tiga kepala: spam / sikap / emosi)
dari repo model [IRedDragonICY/indobert-sentimen-chromebook](https://huggingface.co/IRedDragonICY/indobert-sentimen-chromebook)
dan mengekspos endpoint `/analisis`.

Streamlit memanggil Space ini via `gradio_client`, jadi app Streamlit tetap ringan
(tanpa PyTorch) dan inferensi berjalan di sisi HuggingFace.

## Endpoint

```python
from gradio_client import Client

client = Client("IRedDragonICY/sentimen-chromebook-api")
hasil = client.predict("Bukti korupsinya mana sih?", api_name="/analisis")
# -> {"hasil": [{"teks": ..., "spam": false, "sikap": "kritik_peradilan",
#                "emosi": "sinis", "keyakinan": {...}, "abstain": {...}, "prob": {...}}]}
```

Input: teks, satu komentar per baris. Output: JSON `{"hasil": [...]}`, satu objek per baris.

## Konfigurasi (Settings > Variables and secrets)

| Variable | Default | Keterangan |
|---|---|---|
| `REPO_MODEL` | `IRedDragonICY/indobert-sentimen-chromebook` | Repo model HF atau path folder lokal. |

## GPU

GPU dideteksi otomatis. Pada hardware **ZeroGPU** paket `spaces` tersedia dan
fungsi inferensi dijalankan lewat `@spaces.GPU`. Pada **CPU basic** (atau lokal)
fungsi yang sama berjalan di CPU tanpa perubahan kode; untuk komentar tunggal CPU
pun menjawab dalam waktu di bawah satu detik.

Model dilatih hanya untuk komentar seputar kasus ini dan tidak untuk menilai
individu maupun moderasi otomatis. Lisensi CC BY-NC-SA 4.0.
