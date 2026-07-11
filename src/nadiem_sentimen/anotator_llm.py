"""Anotator LLM via Ollama lokal.

Dipakai untuk dua hal: (1) baseline zero-shot yang diukur terhadap gold, dan
(2) pelabelan silver untuk data latih. Guideline pelabelan (system prompt)
diturunkan verbatim dari skills/sentiment-labeling-id/SKILL.md sehingga
anotator manusia dan anotator LLM memakai aturan yang sama.

Thinking-mode dimatikan (``think=False``) dan ``format=json`` dipakai agar
keluaran deterministik, cepat, dan langsung ter-parse.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

SIKAP = {
    "pro_nadiem", "kontra_nadiem", "kritik_peradilan",
    "kritik_pemerintah", "netral_informasional", "tak_jelas",
}
EMOSI = {"marah", "duka", "sinis", "harapan", "netral"}

SYSTEM_PROMPT = """Kamu anotator ahli sentimen komentar Instagram berbahasa Indonesia tentang kasus hukum Nadiem Makarim (dugaan korupsi pengadaan Chromebook untuk sekolah). Bahasa komentar informal, penuh slang, sarkasme, emoji, dan campur Inggris.

Untuk setiap komentar, keluarkan JSON persis: {"spam": <bool>, "sikap": "<kelas>", "emosi": "<kelas>"}

ATURAN INTI: kodekan target yang EKSPLISIT tertulis, jangan menebak posisi politik penulis. Jika ragu antara dua kelas sikap, pilih tak_jelas.

spam=true HANYA untuk judi online (slot/gacor/maxwin/testimoni menang/nama situs), promosi jualan, jasa (bor sumur), giveaway, atau promosi link/akun. Gibberish biasa BUKAN spam.

sikap (pilih SATU):
- pro_nadiem: simpati/bela Nadiem, doa untuknya, framing dizolimi/dikorbankan/tumbal, bela kebijakan atau manfaat Chromebook, duka verbal yang menyebut peristiwa yang menimpanya
- kontra_nadiem: anggap Nadiem bersalah/pantas dihukum, dukung penuntutan, kritik kebijakan/pribadinya (kurikulum, "urus gojek aja"), ejek pembelanya
- kritik_peradilan: marah/sinis ke hakim/jaksa/vonis/proses hukum; sindiran "gaji hakim naik 280%"; "yang mulia" yang mengejek; keluhan hukum tidak adil/selektif ("kok kasus lain gak diadili")
- kritik_pemerintah: sasar presiden/Jokowi(="Mulyono")/Prabowo/Gibran/pemerintah/DPR/program politik, tanpa kontras eksplisit ke perlakuan kasus ini
- netral_informasional: berbagi info, pertanyaan tulus, atau diskusi teknis tanpa keberpihakan
- tak_jelas: emoji saja, terlalu pendek, gibberish, atau tak ada posisi yang terbaca dari teksnya sendiri

emosi (pilih SATU):
- marah: kecaman, makian, ancaman pertanggungjawaban/azab, huruf kapital penuh
- duka: sedih, simpati, kehilangan (banyak 😭😢💔🥀), "heartbroken"
- sinis: sarkasme, ejekan, tawa pahit (😂🤣 pada konteks serius), pujian semu, ironi
- harapan: dukungan, semangat, doa optimis, ajakan solidaritas (🙏🤲💪)
- netral: tanpa muatan afektif menonjol

Jika sarkasme, label makna yang DIMAKSUD (bukan harfiah), dan emosi=sinis. Jawab HANYA JSON."""

# Contoh few-shot kanonik (bukan diambil dari gold test) untuk menstabilkan
# penerapan aturan tersulit: sarkasme, multi-target, whataboutism, emoji, spam.
FEW_SHOT: list[tuple[str, dict]] = [
    ("Inilah fungsi dari menaikkan gaji para hakim 280%.",
     {"spam": False, "sikap": "kritik_peradilan", "emosi": "sinis"}),
    ("Allah bersama bapak Nadiem, semangat pak",
     {"spam": False, "sikap": "pro_nadiem", "emosi": "harapan"}),
    ("Kurikulum mu yang merusak generasi muda, mending urus gojek aja",
     {"spam": False, "sikap": "kontra_nadiem", "emosi": "marah"}),
    ("Ikn merugikan negara kok Jokowi GK di adili",
     {"spam": False, "sikap": "kritik_peradilan", "emosi": "sinis"}),
    ("Masih menunggu Mulyono untuk segera diadili",
     {"spam": False, "sikap": "kritik_pemerintah", "emosi": "sinis"}),
    ("😭😭😭💔",
     {"spam": False, "sikap": "tak_jelas", "emosi": "duka"}),
    ("e-katalog operatornya manusia bukan?",
     {"spam": False, "sikap": "netral_informasional", "emosi": "netral"}),
    ("Alhamdulillah dikasih menang lagi 12,6jt di KOLEMAX",
     {"spam": True, "sikap": "tak_jelas", "emosi": "netral"}),
    ("Sedih banget liat berita pak Nadiem dipenjara",
     {"spam": False, "sikap": "pro_nadiem", "emosi": "duka"}),
    ("Hakim anjing, tandai mukanya, tuntut di akhirat",
     {"spam": False, "sikap": "kritik_peradilan", "emosi": "marah"}),
]


@dataclass
class Prediksi:
    spam: bool
    sikap: str
    emosi: str


def _valid(obj: dict) -> Prediksi | None:
    try:
        sikap = str(obj["sikap"]).strip()
        emosi = str(obj["emosi"]).strip()
        spam = bool(obj["spam"])
    except (KeyError, TypeError):
        return None
    if sikap not in SIKAP or emosi not in EMOSI:
        return None
    # Konsistensi minimal: spam selalu tak_jelas + netral.
    if spam:
        sikap, emosi = "tak_jelas", "netral"
    return Prediksi(spam, sikap, emosi)


def _pesan(teks: str, few_shot: bool) -> list[dict]:
    pesan = [{"role": "system", "content": SYSTEM_PROMPT}]
    if few_shot:
        for contoh, jwb in FEW_SHOT:
            pesan.append({"role": "user", "content": contoh})
            pesan.append({"role": "assistant", "content": json.dumps(jwb, ensure_ascii=False)})
    pesan.append({"role": "user", "content": teks[:1500]})
    return pesan


def labeli_satu(teks: str, model: str, few_shot: bool = False, timeout: int = 120) -> Prediksi | None:
    body = json.dumps({
        "model": model,
        "messages": _pesan(teks, few_shot),
        "stream": False,
        "think": False,
        "format": "json",
        "keep_alive": "30m",
        "options": {"temperature": 0, "num_predict": 80, "num_ctx": 4096},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, body, {"Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=timeout))
        return _valid(json.loads(resp["message"]["content"]))
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        return None


def labeli_banyak(teks: list[str], model: str, few_shot: bool = True,
                  jeda_progress=None) -> list[Prediksi | None]:
    hasil = []
    for i, t in enumerate(teks):
        hasil.append(labeli_satu(t, model, few_shot=few_shot))
        if jeda_progress and (i + 1) % jeda_progress == 0:
            print(f"  ...{i + 1}/{len(teks)}", flush=True)
    return hasil
