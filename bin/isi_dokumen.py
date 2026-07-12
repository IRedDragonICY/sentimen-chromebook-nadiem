"""Isi metrik & temuan nyata ke MODEL_CARD.md dan README.md.

Dijalankan setelah pipeline evaluasi + skoring + temuan.py selesai. Mengganti
blok placeholder di antara penanda komentar HTML, sehingga aman dijalankan ulang.

Jalankan:  python bin/isi_dokumen.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMA_MODEL = {
    "majority": "Majority (lantai)",
    "tfidf_logreg": "TF-IDF + LogReg",
    "finetune": "IndoBERT fine-tune",
}


def tabel_eval(ev: dict) -> str:
    baris = ["| Model | sikap macro-F1 | sikap acc | emosi macro-F1 | spam macro-F1 |",
             "|---|---|---|---|---|"]
    urut = ["majority", "tfidf_logreg", "finetune"]
    urut += [k for k in ev["model"] if k.startswith("llm_")]
    for nama in urut:
        if nama not in ev["model"]:
            continue
        h = ev["model"][nama]
        label = NAMA_MODEL.get(nama, nama.replace("llm_", "LLM zero-shot: "))
        def sel(tugas):
            m = h[tugas]
            lo, hi = m["ci95"]
            return f"{m['macro_f1']:.3f} <sub>[{lo:.2f}–{hi:.2f}]</sub>"
        baris.append(f"| {label} | {sel('sikap')} | {h['sikap']['accuracy']:.3f} | "
                     f"{sel('emosi')} | {sel('spam')} |")
    return "\n".join(baris)


def blok_ganti(teks: str, penanda: str, isi: str) -> str:
    awal, akhir = f"<!-- {penanda}:mulai -->", f"<!-- {penanda}:akhir -->"
    if awal in teks and akhir in teks:
        pre = teks.split(awal)[0]
        post = teks.split(akhir)[1]
        return f"{pre}{awal}\n{isi}\n{akhir}{post}"
    return teks  # penanda tak ada → biarkan


def isi_model_card(ev: dict):
    path = ROOT / "MODEL_CARD.md"
    teks = path.read_text()
    tabel = tabel_eval(ev)
    catatan = (f"\n_Gold test n={ev['n_test']}. Metrik utama macro-F1; angka dalam "
               "kurung adalah selang kepercayaan bootstrap 95%._\n")
    if "<!-- hasil:mulai -->" not in teks:
        teks = teks.replace(
            "_(placeholder — lihat `reports/evaluasi.json` dan bagian ini akan diperbarui.)_",
            "<!-- hasil:mulai -->\n<!-- hasil:akhir -->")
    path.write_text(blok_ganti(teks, "hasil", tabel + "\n" + catatan))
    print("MODEL_CARD.md diperbarui")


def isi_readme(temuan: dict):
    path = ROOT / "README.md"
    teks = path.read_text()
    komp = temuan["komposisi_sikap_persen"]
    top = sorted(komp.items(), key=lambda x: -x[1])[:3]
    baris = [
        f"- Dari {temuan['total']:,} komentar, {temuan['spam']['persen']}% terdeteksi "
        "spam/promosi dan dikecualikan dari statistik.",
        "- Sikap terbanyak: " + ", ".join(f"**{k}** {v}%" for k, v in top) + ".",
        f"- Sub-isu teramai beserta sikap dominannya: " +
        ", ".join(f"{d['sikap_dominan']} pada _{t}_" for t, d in list(temuan["topik"].items())[:3]) + ".",
    ]
    isi = "\n".join(baris) + "\n\n_Rincian + contoh komentar: `reports/temuan.json` dan aplikasi._"
    if "<!-- temuan:mulai -->" not in teks:
        teks = teks.replace(
            "_Diisi setelah pipeline evaluasi & skoring dijalankan (lihat `reports/`)._",
            "<!-- temuan:mulai -->\n<!-- temuan:akhir -->")
    path.write_text(blok_ganti(teks, "temuan", isi))
    print("README.md diperbarui")


def main():
    ev_path = ROOT / "reports" / "evaluasi.json"
    tm_path = ROOT / "reports" / "temuan.json"
    if ev_path.exists():
        isi_model_card(json.loads(ev_path.read_text()))
    else:
        print("reports/evaluasi.json belum ada — lewati MODEL_CARD")
    if tm_path.exists():
        isi_readme(json.loads(tm_path.read_text()))
    else:
        print("reports/temuan.json belum ada — lewati README")


if __name__ == "__main__":
    main()
