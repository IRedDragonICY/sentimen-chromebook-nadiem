"""Awan kata (word cloud) tanpa dependensi berat.

Menghitung frekuensi kata sendiri (buang stopword Indonesia + noise slang),
lalu merender HTML/CSS mandiri, bukan gambar dari paket `wordcloud` (yang butuh
kompilasi C dan tak tersedia di lingkungan offline ini).

Dua sinyal dikodekan sekaligus, jadi ini bukan sekadar hiasan:
- **Ukuran huruf** = seberapa sering kata muncul.
- **Warna** = sikap yang paling *dicirikan* kata itu, dihitung dari laju
  kemunculan kata di tiap kelas sikap (dinormalkan ukuran kelas), bukan sekadar
  kelas mayoritas. Palet = SIKAP_WARNA yang sudah divalidasi colorblind-safe.

Privasi: token @sebutan/URL sudah disamarkan di hulu; di sini pun kata berpola
hash (heks 12) dan token sapa pun yang mengandung angka dibuang, sehingga sisa
identitas tak mungkin menonjol di awan.
"""

from __future__ import annotations

import html
import random
import re
from collections import Counter, defaultdict

import pandas as pd

from tema import SIKAP_LABEL, SIKAP_WARNA

# Stopword Indonesia (fungsi kata) + noise slang/chat. Kata *isi* yang menjadi
# inti wacana (nadiem, hakim, korupsi, chromebook, keadilan, vonis...) sengaja
# DIBIARKAN, justru itu yang ingin dilihat.
_STOP = {
    # partikel & fungsi
    "yang", "yg", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "utk", "pada",
    "dengan", "dgn", "atau", "juga", "sudah", "udah", "akan", "agar", "saja", "aja",
    "adalah", "ada", "tidak", "tak", "tdk", "gak", "ga", "nggak", "enggak", "bukan",
    "karena", "krn", "kalau", "kalo", "klo", "jika", "bila", "maka", "supaya",
    "sebagai", "oleh", "dalam", "tentang", "hingga", "sampai", "sejak", "setelah",
    "sebelum", "saat", "ketika", "namun", "tetapi", "tapi", "walau", "meski",
    # pronomina & sapaan
    "aku", "saya", "gue", "gua", "gw", "kamu", "kau", "kalian", "kita", "kami",
    "dia", "mereka", "nya", "ku", "mu", "anda", "kamu", "bang", "kak", "mas",
    "mbak", "bu", "pak", "om", "tante", "guys", "gaes",
    # penegas / interjeksi chat
    "sih", "dong", "deh", "kok", "kan", "tuh", "nih", "loh", "lah", "ya", "yah",
    "kek", "kayak", "kaya", "gitu", "gini", "begitu", "begini", "banget", "bgt",
    "amat", "sekali", "emang", "memang", "mah", "lagi", "lg", "udh", "blm", "belum",
    "masih", "mesti", "harus", "biar", "buat", "punya", "jadi", "jd", "bikin",
    "ah", "eh", "oh", "wah", "wkwk", "wkwkwk", "haha", "hahaha", "hehe", "hmm",
    "si", "para", "pun", "per", "bisa", "boleh", "mau", "ingin", "pengen", "pengin",
    "semua", "sama", "sm", "lebih", "paling", "sangat", "cuma", "hanya", "doang",
    "kenapa", "gimana", "gmn", "bagaimana", "apa", "apakah", "siapa", "mana",
    "kapan", "dimana", "kemana", "berapa", "yaa", "yg", "orang", "org",
}
_TOKEN = re.compile(r"[a-zA-Z]{3,}")
_HEKS = re.compile(r"^[0-9a-f]{12}$")  # sisa hash penyamaran identitas


def _token(teks: str):
    for kata in _TOKEN.findall(teks.lower()):
        if kata not in _STOP and not _HEKS.match(kata):
            yield kata


def hitung(df: pd.DataFrame, n: int = 60) -> list[dict]:
    """Kembalikan maksimal n kata teratas: {kata, jumlah, sikap} (sikap = pencirian).

    ``sikap`` dipilih dari laju kemunculan kata per kelas (count/ukuran_kelas),
    sehingga kelas kecil pun bisa "memiliki" kata khasnya. Bila kolom sikap tak
    ada (mis. data belum diskor), warna jatuh ke netral.
    """
    total = Counter()
    per_sikap = defaultdict(Counter)
    ada_sikap = "sikap" in df.columns
    ukuran = df["sikap"].value_counts().to_dict() if ada_sikap else {}

    for row in df.itertuples():
        s = getattr(row, "sikap", None) if ada_sikap else None
        for kata in set(_token(row.teks_bersih or "")):  # set: 1 komentar = 1 suara/kata
            total[kata] += 1
            if s:
                per_sikap[kata][s] += 1

    hasil = []
    for kata, jml in total.most_common(n):
        sikap = "tak_jelas"
        if ada_sikap and per_sikap[kata]:
            sikap = max(per_sikap[kata],
                        key=lambda s: per_sikap[kata][s] / max(ukuran.get(s, 1), 1))
        hasil.append({"kata": kata, "jumlah": jml, "sikap": sikap})
    return hasil


def _skala(jml: int, lo: int, hi: int, px_lo=13.0, px_hi=48.0) -> float:
    if hi <= lo:
        return (px_lo + px_hi) / 2
    # akar: redam dominasi kata paling sering agar ekor tetap terbaca
    f = ((jml - lo) / (hi - lo)) ** 0.5
    return round(px_lo + f * (px_hi - px_lo), 1)


def _css() -> str:
    baris = []
    for k, (terang, gelap) in SIKAP_WARNA.items():
        baris.append(f".wc-{k}{{color:{terang};}}")
        baris.append(f"@media (prefers-color-scheme:dark){{.wc-{k}{{color:{gelap};}}}}")
    return (
        "<style>"
        ".awan{display:flex;flex-wrap:wrap;gap:.1rem .75rem;align-items:center;"
        "justify-content:center;line-height:1.3;padding:1.1rem .6rem;}"
        ".awan span{font-weight:700;letter-spacing:-.01em;transition:transform .12s;"
        "cursor:default;}"
        ".awan span:hover{transform:scale(1.12);}"
        ".awan-legend{display:flex;flex-wrap:wrap;gap:.35rem .8rem;"
        "justify-content:center;margin-top:.4rem;font-size:.76rem;}"
        ".awan-legend .it{display:inline-flex;align-items:center;gap:.32rem;color:var(--ink-2);}"
        ".awan-legend .dot{width:.6rem;height:.6rem;border-radius:50%;}"
        + "".join(baris) + "</style>"
    )


def _legend() -> str:
    it = []
    for k, label in SIKAP_LABEL.items():
        it.append(
            f'<span class="it"><span class="dot" style="background:{SIKAP_WARNA[k][0]}"></span>'
            f'{html.escape(label)}</span>'
        )
    return f'<div class="awan-legend">{"".join(it)}</div>'


def awan_html(kata: list[dict], seed: int = 42, tampil_legend: bool = True) -> str:
    """HTML mandiri untuk awan kata; aman disisipkan via st.markdown."""
    if not kata:
        return '<div class="awan"><span style="color:var(--ink-3)">Tak ada kata.</span></div>'
    jmls = [k["jumlah"] for k in kata]
    lo, hi = min(jmls), max(jmls)
    acak = random.Random(seed)
    urut = kata[:]
    acak.shuffle(urut)  # sebar kata besar agar tak menggumpal, terasa "awan"
    span = []
    for k in urut:
        px = _skala(k["jumlah"], lo, hi)
        op = round(0.6 + 0.4 * ((k["jumlah"] - lo) / (hi - lo) if hi > lo else 1), 2)
        span.append(
            f'<span class="wc-{k["sikap"]}" style="font-size:{px}px;opacity:{op}" '
            f'title="{k["kata"]}: {k["jumlah"]} komentar">{html.escape(k["kata"])}</span>'
        )
    legend = _legend() if tampil_legend else ""
    return _css() + f'<div class="awan">{"".join(span)}</div>{legend}'
