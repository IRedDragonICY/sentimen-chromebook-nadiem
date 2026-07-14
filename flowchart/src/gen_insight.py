"""Papan insight bergaya post-it (latar transparan, untuk Canva)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from flowlib import SVG, esc

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)
FONT = "Noto Sans"
INK = "#2A211B"
BODY = "#574C42"

# fill, accent, darker (untuk sudut terlipat)
WARNA = {
    "amber":  ("#FBE7A8", "#93650A", "#E9D083"),
    "peach":  ("#FBDCC0", "#A2551F", "#E9C6A4"),
    "pink":   ("#F8CEDA", "#A3385A", "#E7B5C5"),
    "coral":  ("#F8CBC2", "#B03A2E", "#E9B1A6"),
    "teal":   ("#BFE8D8", "#0E6B5E", "#A2D6C2"),
    "blue":   ("#C6DBF4", "#295F9E", "#AAC6E8"),
    "green":  ("#D2E9B0", "#4E7A1E", "#BBD892"),
    "lilac":  ("#DED4F1", "#5B49A8", "#C7B9E6"),
    "cyan":   ("#C3E7EC", "#1E7C86", "#A6D6DD"),
}


def sticky(x, y, w, h, angle, kicker, title, body, stat, warna):
    fill, accent, dark = WARNA[warna]
    cx, cy = x + w / 2, y + h / 2
    pad = 22
    p = [f'<g transform="rotate({angle} {cx} {cy})">']
    # bayangan
    p.append(f'<rect x="{x+5}" y="{y+8}" width="{w}" height="{h}" rx="14" fill="#1a140f" opacity="0.13"/>')
    # badan
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}"/>')
    # sudut terlipat kecil (kanan bawah)
    p.append(f'<path d="M{x+w-26} {y+h} L{x+w} {y+h-26} L{x+w} {y+h} Z" fill="{dark}" opacity="0.8"/>')
    # selotip di atas tengah
    tcx, tcy = cx, y - 6
    p.append(f'<g transform="rotate(-5 {tcx} {tcy})">'
             f'<rect x="{tcx-52}" y="{tcy-13}" width="104" height="26" rx="3" '
             f'fill="#FFFFFF" opacity="0.42" stroke="#FFFFFF" stroke-opacity="0.6" stroke-width="1"/></g>')
    # kicker (kategori)
    p.append(f'<circle cx="{x+pad+4}" cy="{y+pad+6}" r="4.5" fill="{accent}"/>')
    p.append(f'<text x="{x+pad+16}" y="{y+pad+10}" font-family="{FONT}" font-size="11.5" '
             f'font-weight="700" fill="{accent}" letter-spacing="1.5">{esc(kicker.upper())}</text>')
    # angka sorotan (kanan atas)
    if stat:
        ss = 34 if len(stat) <= 6 else 20
        p.append(f'<text x="{x+w-pad}" y="{y+pad+ss*0.9}" font-family="{FONT}" font-size="{ss}" '
                 f'font-weight="800" fill="{accent}" text-anchor="end">{esc(stat)}</text>')
    # judul
    ty = y + 66
    p.append(f'<text x="{x+pad}" y="{ty}" font-family="{FONT}" font-size="20.5" '
             f'font-weight="800" fill="{INK}">{esc(title)}</text>')
    # isi
    by = ty + 28
    for i, ln in enumerate(body):
        p.append(f'<text x="{x+pad}" y="{by+i*21}" font-family="{FONT}" font-size="14.5" '
                 f'font-weight="400" fill="{BODY}">{esc(ln)}</text>')
    p.append('</g>')
    return "".join(p)


def d_insight():
    W = 1880
    s = SVG(W, 1010)
    # intro + legenda
    s.text(60, 52, "Sembilan temuan: empat dari data, lima dari proses membangun sistem.",
           size=16, weight=600, fill=BODY)
    # legenda kategori
    s.add(f'<rect x="60" y="74" width="15" height="15" rx="4" fill="#FBE7A8"/>')
    s.text(84, 87, "Temuan data", size=12.5, weight=700, fill="#7a6a52")
    s.add(f'<rect x="230" y="74" width="15" height="15" rx="4" fill="#BFE8D8"/>')
    s.text(254, 87, "Pelajaran teknis", size=12.5, weight=700, fill="#7a6a52")

    cards = [
        # kicker, judul, body[], stat, warna, angle
        ("Temuan data", "Sorotan tertuju ke sistem hukum",
         ["Kritik peradilan mencapai 22,8% dari seluruh komentar",
          "dan memuncak 27,3% pada fase vonis, melampaui yang",
          "menyalahkan Nadiem secara langsung (kontra 17%)."], "27,3%", "amber", -1.5),
        ("Temuan data", "Wacana bernada duka dan marah",
         ["Duka 30,1% dan marah 29,6% mengisi hampir enam dari",
          "sepuluh komentar, sedangkan harapan hanya 8,2%.",
          "Emosi negatif jelas mendominasi percakapan."], "60%", "peach", 1.1),
        ("Temuan data", 'Kelas terbesar justru "tak jelas"',
         ['Sebanyak 26,5% komentar tergolong ambigu atau',
          "sarkastik, melebihi yang pro (25,1%) dan kontra (17%).",
          "Sarkasme dan campur bahasa menyulitkan pelabelan."], "26,5%", "pink", -0.8),
        ("Temuan data", "Perhatian meledak di titik vonis",
         ["Dari 38.845 komentar, 76% muncul pada rentang Juni",
          "sampai Juli 2026. Percakapan terpusat pada momen",
          "peristiwa, bukan menyebar merata sepanjang kasus."], "76%", "coral", 1.4),
        ("Pelajaran teknis", "Data mentah kotor secara sistemik",
         ['Timestamp seperti "30/6/2026, 21.43.41" berkoma tanpa',
          "kutip membuat tiap baris punya satu field ekstra.",
          "Pengurai wajib memeriksa bentuk baris, bukan header."], "", "teal", -1.2),
        ("Pelajaran teknis", "Model canggih tak otomatis menang",
         ["Penyetelan halus IndoBERT (macro-F1 0,544) hanya",
          "sedikit di atas TF-IDF dengan regresi logistik (0,534).",
          "Baseline sederhana harus dikalahkan agar klaim sahih."], "0,544 vs 0,534", "blue", 0.9),
        ("Pelajaran teknis", "Evaluasi jujur menuntut anti-kebocoran",
         ["Terdapat 8.474 baris near-duplikat. Membaginya per",
          "klaster, bukan per baris, mencegah komentar kembar",
          "bocor antara data latih dan data uji."], "8.474", "green", -1.6),
        ("Pelajaran teknis", "Popularitas bukan proporsi",
         ["Pada 1.000 komentar terpopuler, sikap pro naik ke",
          "30,2% dari 25,1% keseluruhan. Suara paling disukai",
          "tidak mewakili keseluruhan percakapan."], "30,2%", "lilac", 1.2),
        ("Pelajaran teknis", "Emoji adalah sinyal, bukan derau",
         ["Sebanyak 11% komentar hanya berisi emoji. Alih-alih",
          "dibuang, emoji dipertahankan dan ditangani aturan",
          "emosi tersendiri agar afeksinya tidak hilang."], "11%", "cyan", -0.6),
    ]
    cw, ch = 560, 186
    gx, gy = 40, 48
    x0, y0 = 60, 128
    for i, (kick, title, body, stat, warna, ang) in enumerate(cards):
        col, row = i % 3, i // 3
        x = x0 + col * (cw + gx)
        y = y0 + row * (ch + gy)
        s.add(sticky(x, y, cw, ch, ang, kick, title, body, stat, warna))

    # spanduk catatan etis
    by = y0 + 3 * (ch + gy) + 6
    bw = W - 120
    s.add(f'<rect x="{63}" y="{by+6}" width="{bw}" height="104" rx="14" fill="#1a140f" opacity="0.10"/>')
    s.add(f'<rect x="60" y="{by}" width="{bw}" height="104" rx="14" fill="#FFF7E6" stroke="#E3CE96" stroke-width="1.8"/>')
    s.add(f'<rect x="60" y="{by}" width="7" height="104" rx="3.5" fill="#C89A22"/>')
    s.text(88, by + 34, "CATATAN ETIS DAN KETERBATASAN", size=13, weight=700, fill="#9A7414", spacing="1.5")
    s.text(88, by + 62,
           "Data berasal dari 11 unggahan Instagram, bukan survei yang mewakili opini publik Indonesia, sehingga hasilnya tidak boleh digeneralisasi.",
           size=14.5, weight=400, fill=BODY)
    s.text(88, by + 86,
           "Sistem mengukur sentimen komentar, bukan menilai bersalah atau tidaknya siapa pun, dan menjunjung asas praduga tak bersalah.",
           size=14.5, weight=400, fill=BODY)

    (OUT / "08_insight.svg").write_text(s.render(), encoding="utf-8")
    print("wrote 08_insight")


if __name__ == "__main__":
    d_insight()
