"""HuggingFace Space: backend inferensi model sentimen kasus Chromebook-Nadiem.

Memuat KlasifikatorMultiTask (IndoBERT + tiga kepala: spam/sikap/emosi) dari repo
model HF, lalu mengekspos satu fungsi Gradio `analisis` yang mengembalikan
kontrak penuh: sikap, emosi, spam, keyakinan terkalibrasi, dan tanda abstain.

Dashboard Streamlit memanggil Space ini lewat gradio_client, sehingga app
Streamlit tetap ringan (tanpa torch) dan inferensi berjalan di sisi HuggingFace.

GPU dideteksi otomatis: pada hardware ZeroGPU paket `spaces` tersedia, dan fungsi
inferensi didekorasi @spaces.GPU (wajib agar terdeteksi saat startup). Di luar
ZeroGPU (mis. CPU basic atau lokal) fungsi jalan apa adanya di CPU.

Konfigurasi lewat environment variable (Settings > Variables and secrets):
- REPO_MODEL   : id repo model HF (default IRedDragonICY/indobert-sentimen-chromebook),
                 atau path folder lokal saat pengembangan.
"""

from __future__ import annotations

import os

import gradio as gr

from nadiem_sentimen.inference import MesinSentimen

# Pada hardware ZeroGPU, `spaces` sudah tersedia dan fungsi ber-@spaces.GPU wajib
# ada saat startup. Di lingkungan tanpa ZeroGPU (CPU/lokal), impor ini gagal dan
# inferensi jalan di CPU.
try:
    import spaces
except ImportError:
    spaces = None

REPO_MODEL = os.environ.get("REPO_MODEL", "IRedDragonICY/indobert-sentimen-chromebook")

CONTOH = (
    "Allah bersama bapak Nadiem, semangat pak\n"
    "Inilah fungsi menaikkan gaji hakim 280%\n"
    "Bukti korupsinya mana sih?"
)


def _muat_folder_model() -> str:
    """Kembalikan folder lokal berisi bobot model. Unduh dari HF bila perlu."""
    if os.path.isdir(REPO_MODEL):
        return REPO_MODEL
    from huggingface_hub import snapshot_download

    return snapshot_download(REPO_MODEL)


# Model dimuat sekali di CPU saat Space start. Pada ZeroGPU, GPU hanya tersedia
# di dalam fungsi ber-dekorator @spaces.GPU, jadi pemindahan ke cuda dilakukan
# per-permintaan di _prediksi_gpu.
mesin = MesinSentimen.muat(_muat_folder_model(), device="cpu")


def _prediksi(baris: list[str]) -> list[dict]:
    keluar = []
    for h in mesin.predict(baris):
        keluar.append(
            {
                "teks": h.teks,
                "spam": h.spam,
                "sikap": h.sikap,
                "emosi": h.emosi,
                "keyakinan": h.keyakinan,
                "abstain": h.abstain,
                "prob": h.prob,
            }
        )
    return keluar


if spaces is not None:

    @spaces.GPU(duration=30)
    def _jalankan(baris: list[str]) -> list[dict]:
        # Di dalam konteks ZeroGPU, GPU baru tersedia di sini. Pindahkan model
        # sekali lalu jalankan; proses fork ZeroGPU bersifat sekali-pakai.
        import torch

        if torch.cuda.is_available():
            mesin.model.to("cuda")
            mesin.device = "cuda"
        return _prediksi(baris)

else:
    _jalankan = _prediksi


def analisis(teks: str) -> dict:
    """Terima teks multi-baris, kembalikan {'hasil': [prediksi per baris]}."""
    baris = [b for b in (teks or "").splitlines() if b.strip()]
    if not baris:
        return {"hasil": []}
    return {"hasil": _jalankan(baris)}


with gr.Blocks(title="Sentimen Chromebook-Nadiem - API inferensi") as demo:
    gr.Markdown(
        "# Sentimen Chromebook-Nadiem - API inferensi\n"
        "Backend model IndoBERT multi-task (spam / sikap / emosi) yang dipanggil "
        "oleh dashboard Streamlit. Model dilatih pada komentar kasus ini; di luar "
        "domain tersebut hasilnya kurang bermakna.\n\n"
        "Endpoint terprogram: `/analisis` (dipakai via gradio_client)."
    )
    inp = gr.Textbox(lines=6, label="Komentar (satu per baris)", value=CONTOH)
    btn = gr.Button("Analisis", variant="primary")
    out = gr.JSON(label="Prediksi")
    btn.click(analisis, inputs=inp, outputs=out, api_name="analisis")
    inp.submit(analisis, inputs=inp, outputs=out, api_name=False)


if __name__ == "__main__":
    demo.launch()
