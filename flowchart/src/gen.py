"""Bangun semua flowchart SVG (latar transparan, untuk papan tulis Canva)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from flowlib import SVG, CAT, INK, MUTED, MUTED2, BG

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)


def save(name, svg):
    (OUT / f"{name}.svg").write_text(svg.render(), encoding="utf-8")
    print("wrote", name)


# =====================================================================
# 1. PETA ALUR SISTEM
# =====================================================================
def d1():
    W = 1240
    s = SVG(W, 1180)
    s.header("Peta alur sistem", "Analisis Sentimen: dari Data Mentah ke Aplikasi",
             "Delapan tahap yang terdokumentasi dan dapat diproduksi ulang atas 38.845 komentar Instagram",
             "Ikhtisar")
    cx = 70
    cw = 560
    chx = 700
    chw = 470
    spine = cx + cw / 2
    stages = [
        ("1   Membaca dan membangun dataset",
         ["Membaca 11 berkas CSV, memvalidasi setiap baris,",
          "menggabungkan timestamp, menghitung kolom turunan"], "prep",
         "komentar.parquet", "38.845 komentar beserta profil.json (sha256)", "artifact"),
        ("2   Sampling terstratifikasi",
         ["Unit sampel berupa wakil klaster agar tidak bocor;",
          "strata menurut fase, tipe teks, dan tingkat likes"], "prep",
         "gold_todo.csv dan silver_todo.csv", "kandidat untuk pelabelan", "artifact"),
        ("3   Pelabelan tiga lapis",
         ["Gold 710 komentar dilabeli manusia sebagai acuan uji,",
          "silver 5.912 komentar dilabeli LLM lokal untuk melatih"], "label",
         "skema label: spam (2), sikap (6), emosi (5)", "satu komentar, tiga label", "artifact"),
        ("4   Menyusun train, val, dan test",
         ["Pembagian berbasis klaster dan distratifikasi sikap;",
          "val dan test hanya dari gold berlabel manusia"], "split",
         "train 6.233, val 106, test 283", "pembagian tanpa kebocoran", "artifact"),
        ("5   Melatih model",
         ["Model dasar TF-IDF dan penyetelan halus IndoBERT",
          "multitugas (satu encoder, tiga kepala) berbobot kelas"], "model",
         "bobot model terbaik", "dipilih berdasarkan macro-F1 validasi", "artifact"),
        ("6   Kalibrasi dan ambang abstain",
         ["Penskalaan suhu tiap tugas serta ambang keyakinan",
          "agar akurasi bagian terjawab minimal 80 persen"], "cal",
         "models/sentimen-id", "pytorch_model.bin dan meta.json", "artifact"),
        ("7   Evaluasi yang jujur pada gold test",
         ["macro-F1, F1 tiap kelas, dan selang kepercayaan;",
          "penyetelan halus: sikap 0,544  emosi 0,624  spam 1,00"], "eval",
         "reports/evaluasi.json", "empat model dibandingkan setara", "artifact"),
        ("8   Menyekor penuh dan menyajikan aplikasi",
         ["Menyekor 38.845 komentar sekali jalan, lalu disajikan",
          "di Streamlit dan Space HuggingFace (Coba Model)"], "serve",
         "skor.parquet menuju aplikasi", "sumber data tunggal antarmuka", "serve"),
    ]
    y = 168
    prev_bottom = None
    for title, lines, cat, atitle, asub, acat in stages:
        x, yy, w, h = s.node(cx, y, cw, title, lines, cat)
        if prev_bottom is not None:
            s.arrow([(spine, prev_bottom), (spine, y)])
        ch_y = y + h / 2 - 21
        s.chip(chx, ch_y, chw, atitle, asub, acat, h=44)
        s.arrow([(cx + cw, y + h / 2), (chx, ch_y + 22)], width=1.7)
        prev_bottom = y + h
        y = y + h + 34
    save("01_peta_pipeline", s)


# =====================================================================
# 2. PRAPEMROSESAN (ingest -> build_dataset)
# =====================================================================
def d2():
    W = 1300
    col = 300
    cw = 520
    ccx = col + cw / 2
    s = SVG(W, 1200)
    s.header("Tahap 1 . Prapemrosesan", "11 Berkas CSV Mentah menjadi Satu Dataset Bersih",
             "Data mentah tidak pernah diubah; pengurai memeriksa bentuk setiap baris secara eksplisit",
             "build_dataset.py")
    y = 168

    def down(node_ret, gap=30):
        return node_ret[1] + node_ret[3] + gap

    n1 = s.node(col, y, cw, "11 berkas CSV mentah",
                ["Dua skema header (sepuluh berkas biasa dan satu berthread),",
                 "hasil crawling komentar Instagram apa adanya"], "raw")
    y = down(n1)
    n2 = s.node(col, y, cw, "Membaca baris demi baris (csv.reader)",
                ["Tidak ada tebakan; setiap baris diperiksa secara eksplisit"], "prep")
    s.arrow([(ccx, n1[1] + n1[3]), (ccx, n2[1])])
    y = down(n2, 26)

    dcy = y + 62
    s.diamond(ccx, dcy, 360, 124,
              ["Bentuk baris valid?", "jumlah field, pola tanggal", "(dd/mm/yyyy), pola jam (hh.mm.ss)"], "decision")
    s.arrow([(ccx, n2[1] + n2[3]), (ccx, dcy - 62)])
    dgx = 960
    dg = s.node(dgx, dcy - 45, 300, "Anomali dicatat, proses berhenti",
                ["Program dihentikan (SystemExit) bila format",
                 "berubah, sebab lebih baik gagal daripada cacat"], "danger", ts=14, ss=11.5)
    s.arrow([(ccx + 180, dcy), (dgx, dcy)], color="#D65A59", marker="arwR",
            label="tidak", label_xy=((ccx + 180 + dgx) / 2, dcy - 14))

    y = dcy + 62 + 24
    n4 = s.node(col, y, cw, "Menggabungkan dua field timestamp",
                ['Nilai "30/6/2026, 21.43.41" mengandung koma tanpa',
                 "kutip, sehingga tiap baris memiliki satu field ekstra"], "prep")
    s.arrow([(ccx, dcy + 62), (ccx, n4[1])], label="ya", label_xy=(ccx, (dcy + 62 + n4[1]) / 2))
    y = down(n4)
    n5 = s.node(col, y, cw, "Objek Komentar yang terstruktur",
                ["id, post, username, waktu, likes, teks, is_reply"], "prep")
    s.arrow([(ccx, n4[1] + n4[3]), (ccx, n5[1])])
    y = down(n5)
    n6 = s.node(col, y, cw, "DataFrame terpadu (38.845 baris)",
                ["Urutan deterministik sehingga hash Parquet menjadi versi data"], "prep")
    s.arrow([(ccx, n5[1] + n5[3]), (ccx, n6[1])])
    y = down(n6, 22)

    hd = s.node(col, y, cw, "Menambahkan kolom turunan", [], "norm", h=40, ts=14.5)
    s.arrow([(ccx, n6[1] + n6[3]), (ccx, hd[1])])
    y = hd[1] + hd[3] + 20
    chips = [
        ("teks_bersih", "bersihkan(): NFKC, buang kontrol, emoji tetap"),
        ("fase", "fase_peristiwa(): empat fase peristiwa"),
        ("hanya_emoji dan emoji", "11 persen komentar hanya emoji, tetap sinyal"),
        ("klaster_dup", "kunci_duplikat menghasilkan 31.405 klaster"),
        ("n_karakter dan ukuran_klaster", "metadata untuk sampling dan tampilan"),
    ]
    chw = 250
    cxs = [col, col + cw - chw]
    ry = y
    for i, (t, sub) in enumerate(chips):
        cxx = cxs[i % 2]
        if i % 2 == 0 and i > 0:
            ry += 60
        if i == len(chips) - 1 and len(chips) % 2 == 1:
            cxx = ccx - chw / 2
        s.chip(cxx, ry, chw, t, sub, "artifact", h=52, ts=12.5, ss=10.4)
    y = ry + 52 + 26
    n8 = s.node(col, y, cw, "komentar.parquet dan profil.json",
                ["38.845 baris siap pakai; profil.json menyimpan sha256",
                 "setiap berkas mentah sebagai jejak asal-usul data"], "artifact")
    s.arrow([(ccx, hd[1] + hd[3]), (ccx, ry - 8)], width=1.6)
    s.arrow([(ccx, ry + 52 + 60), (ccx, n8[1])])

    s.chip(960, y - 150, 300, "Jebakan utama", "timestamp berkoma tanpa tanda kutip", "note", h=52, ts=13, ss=11)
    save("02_prapemrosesan", s)


# =====================================================================
# 3. NORMALISASI (tiga representasi)
# =====================================================================
def d3():
    W = 1220
    s = SVG(W, 740)
    s.header("Prapemrosesan . Teks", "Normalisasi Teks: Tiga Representasi dari Satu Sumber",
             "Teks mentah tidak pernah dibuang; tiap fungsi menurunkan bentuk untuk keperluan yang berbeda",
             "normalisasi.py")
    top = s.node(W / 2 - 210, 168, 420, "Teks komentar mentah",
                 ['contoh: "Gaji hakim naik 280%?? (emoji sedih) kacau"'], "raw")
    tcx = W / 2
    tby = top[1] + top[3]
    cols = [
        (95, "bersihkan( )", "prep",
         ["Normalisasi ringan untuk masukan model.",
          "Menerapkan NFKC (melipat huruf mewah),",
          "membuang karakter kontrol, merapikan spasi.",
          "Huruf besar dan emoji tetap dipertahankan."],
         "Dipakai sama saat latih dan inferensi",
         "sehingga tidak ada beda perlakuan"),
        (485, "kunci_duplikat( )", "split",
         ["Kunci agresif untuk klaster near-duplikat.",
          "casefold, membuang angka, tanda baca, spasi,",
          "dan huruf mewah. Komentar beremoji saja",
          "diwakili himpunan emojinya."],
         "Mencegah kebocoran latih dan uji",
         "serta mendeteksi spam berulang"),
        (875, "daftar_emoji( )", "cal",
         ["Ekstraksi emoji untuk analisis afeksi.",
          "Mencakup rentang Unicode yang luas beserta",
          "penyerta seperti ZWJ dan variation selector",
          "agar tidak ada emoji yang terlewat."],
         "Menjadi dasar aturan emosi",
         "untuk komentar berisi emoji saja"),
    ]
    for x, fn, cat, body, u1, u2 in cols:
        fnn = s.node(x, 300, 300, fn, body, cat, ts=16, ss=11.8)
        midx = x + 150
        s.arrow([(tcx, tby), (tcx, 268), (midx, 268), (midx, 300)])
        s.chip(x + 20, fnn[1] + fnn[3] + 24, 260, u1, u2, "note", h=50, ts=12, ss=11)
    s.text(W / 2, 706, "Prinsip: fungsi yang sama dipakai saat pelatihan dan inferensi; emoji dianggap sinyal, bukan derau.",
           size=13, weight=600, fill=MUTED, anchor="middle")
    save("03_normalisasi", s)


# =====================================================================
# 4. PELABELAN DAN PENYUSUNAN DATA
# =====================================================================
def d4():
    W = 1300
    s = SVG(W, 970)
    s.header("Tahap 2 dan 3 . Data Latih", "Pelabelan dan Penyusunan Data yang Bebas Kebocoran",
             "Unit sampel adalah wakil klaster, bukan baris, sehingga klaster gold tidak pernah masuk pelatihan",
             "sampling.py . assemble_training.py")
    midx = W / 2
    n0 = s.node(midx - 200, 168, 400, "komentar.parquet (38.845)", [], "artifact", h=46, ts=15)
    n1 = s.node(midx - 260, n0[1] + n0[3] + 26, 520, "Klaster near-duplikat (31.405 klaster)",
                ["unit sampel adalah wakil klaster dengan likes tertinggi"], "split")
    s.arrow([(midx, n0[1] + n0[3]), (midx, n1[1])])
    n2 = s.node(midx - 300, n1[1] + n1[3] + 26, 600, "Sampling terstratifikasi",
                ["Strata menurut fase, tipe teks, dan tingkat likes; ada kuota khusus untuk",
                 "komentar paling disukai, indikasi spam, dan emoji, dengan kuota minimum tiap fase"], "prep")
    s.arrow([(midx, n1[1] + n1[3]), (midx, n2[1])])

    by = n2[1] + n2[3] + 34
    gx, sx, bw = 150, 720, 430
    g1 = s.node(gx, by, bw, "gold_todo.csv", [], "gold", h=42, ts=14)
    sv1 = s.node(sx, by, bw, "silver_todo.csv", [], "silver", h=42, ts=14)
    s.arrow([(midx, n2[1] + n2[3]), (midx, by - 18), (gx + bw / 2, by - 18), (gx + bw / 2, by)])
    s.arrow([(midx, n2[1] + n2[3]), (midx, by - 18), (sx + bw / 2, by - 18), (sx + bw / 2, by)])

    gy = by + 42 + 22
    g2 = s.node(gx, gy, bw, "Gold: 710 komentar",
                ["Dilabeli manusia mengikuti pedoman",
                 "pelabelan proyek. Menjadi acuan",
                 "untuk evaluasi dan kalibrasi."], "gold")
    s.arrow([(gx + bw / 2, by + 42), (gx + bw / 2, gy)])
    sv2 = s.node(sx, gy, bw, "Silver: 5.912 komentar",
                 ["Dilabeli LLM lokal via Ollama (keluaran",
                  "JSON, pedoman sama). Emoji ditangani",
                  "aturan pasti. Menjadi tambahan data latih."], "silver")
    s.arrow([(sx + bw / 2, by + 42), (sx + bw / 2, gy)])

    ay = gy + g2[3] + 30
    asm = s.node(midx - 320, ay, 640, "Menyusun pembagian berbasis klaster dan stratifikasi sikap",
                 ["Pembagian dilakukan per klaster sehingga near-duplikat tidak melintasi batas;",
                  "val dan test hanya diambil dari gold yang labelnya tepercaya"], "split")
    s.arrow([(gx + bw / 2, gy + g2[3]), (gx + bw / 2, ay - 16), (midx, ay - 16), (midx, ay)])
    s.arrow([(sx + bw / 2, gy + sv2[3]), (sx + bw / 2, ay - 16), (midx, ay - 16), (midx, ay)])

    oy = ay + asm[3] + 30
    outs = [
        ("TRAIN . 6.233", "321 gold dan 5.912 silver", "split"),
        ("VAL . 106", "hanya gold", "gold"),
        ("TEST . 283", "hanya gold", "gold"),
    ]
    ow = 360
    ox0 = midx - (3 * ow + 2 * 30) / 2
    for i, (t, sub, c) in enumerate(outs):
        oxx = ox0 + i * (ow + 30)
        s.chip(oxx, oy, ow, t, sub, c, h=52, ts=15, ss=12)
        s.arrow([(midx, asm[1] + asm[3]), (midx, oy - 15), (oxx + ow / 2, oy - 15), (oxx + ow / 2, oy)])

    s.chip(56, ay - 4, 250, "Tanpa kebocoran", "silver dijamin lepas dari klaster gold", "note", h=52, ts=13, ss=10.8)
    save("04_pelabelan_split", s)


# =====================================================================
# 5. MODEL, PELATIHAN, KALIBRASI
# =====================================================================
def d5():
    W = 1320
    s = SVG(W, 900)
    s.header("Tahap 4 . Model", "Model Multitugas IndoBERT: Arsitektur, Pelatihan, Kalibrasi",
             "Satu encoder berbagi tiga kepala sehingga model ringkas, cepat, dan saling menguatkan",
             "model.py . train.py")

    def band(y, label):
        s.add(f'<rect x="40" y="{y}" width="{W-80}" height="1.5" fill="#E7E1D8"/>')
        s.text(56, y + 22, label.upper(), size=12.5, weight=700, fill="#1F9E72", spacing="1.5")

    band(150, "Arsitektur")
    ay = 188
    a1 = s.node(60, ay, 250, "Tokenizer IndoBERT", ["truncation, max_len 128, padding"], "model", ts=14, ss=11)
    a2 = s.node(360, ay, 250, "Encoder IndoBERT", ["indobert-base-p1 (BertModel)"], "model", ts=14, ss=11)
    a3 = s.node(660, ay, 250, "Mean-pooling", ["rata-rata token valid, bukan token [CLS]"], "model", ts=14, ss=11)
    s.arrow([(a1[0] + a1[2], ay + a1[3] / 2), (a2[0], ay + a1[3] / 2)])
    s.arrow([(a2[0] + a2[2], ay + a1[3] / 2), (a3[0], ay + a1[3] / 2)])
    heads = [("Kepala spam (2)", "bukan_spam, spam", "cal"),
             ("Kepala sikap (6)", "pro, kontra, dua kritik, netral, tak_jelas", "split"),
             ("Kepala emosi (5)", "marah, duka, sinis, harapan, netral", "eval")]
    hx = 980
    for i, (t, sub, c) in enumerate(heads):
        hy = ay - 6 + i * 44
        s.chip(hx, hy, 300, t, sub, c, h=40, ts=13, ss=10.4)
        s.arrow([(a3[0] + a3[2], ay + a3[3] / 2), (hx - 10, ay + a3[3] / 2), (hx - 10, hy + 20), (hx, hy + 20)], width=1.6)

    band(320, "Pelatihan")
    ty = 358
    t1 = s.node(60, ty, 268, "Data latih (6.233)", ["gold dan silver, kolom teks_bersih"], "split", ts=14, ss=11)
    t2 = s.node(360, ty, 320, "Loss cross-entropy berbobot",
                ["bobot invers frekuensi kelas; contoh", "silver diberi bobot 0,4 karena lebih berisik"], "model", ts=14, ss=11)
    t3 = s.node(712, ty, 250, "AdamW, warmup, dan AMP", ["6 epoch, lr 0,00002, klip gradien"], "model", ts=14, ss=11)
    t4 = s.node(994, ty, 286, "Memilih epoch terbaik", ["berdasarkan macro-F1 sikap pada validasi"], "eval", ts=14, ss=11)
    cyt = ty + t2[3] / 2
    for a, b in [(t1, t2), (t2, t3), (t3, t4)]:
        s.arrow([(a[0] + a[2], cyt), (b[0], cyt)])

    band(500, "Kalibrasi, abstain, dan artefak")
    cy = 542
    c1 = s.node(60, cy, 400, "Penskalaan suhu tiap tugas",
                ["mencari suhu T yang meminimalkan NLL",
                 "pada validasi (LBFGS, dibatasi 0,5 sampai 5,0)"], "cal", ts=14.5, ss=11.5)
    c2 = s.node(500, cy, 400, "Ambang abstain tiap tugas",
                ["ambang keyakinan agar akurasi bagian",
                 "terjawab minimal 80 persen"], "cal", ts=14.5, ss=11.5)
    s.arrow([(c1[0] + c1[2], cy + c1[3] / 2), (c2[0], cy + c1[3] / 2)])
    art = s.node(940, cy - 4, 340, "Artefak models/sentimen-id",
                 ["pytorch_model.bin, tokenizer, config,",
                  "meta.json berisi peta label, suhu, ambang,",
                  "hash data, hiperparameter, dan macro-F1"], "artifact", ts=14.5, ss=11.5)
    s.arrow([(c2[0] + c2[2], cy + c1[3] / 2), (art[0], cy + c1[3] / 2)])

    ny = 720
    s.text(56, ny, "Angka kunci", size=12.5, weight=700, fill="#1F9E72", spacing="1.5")
    facts = [
        ("suhu sikap", "1,52"), ("suhu emosi", "1,18"), ("suhu spam", "0,50"),
        ("ambang sikap", "0,62"), ("ambang emosi", "0,64"),
        ("epoch terbaik", "1"), ("val macro-F1", "0,51"),
    ]
    fw = 168
    for i, (k, v) in enumerate(facts):
        fx = 56 + i * fw
        s.add(f'<rect x="{fx}" y="{ny+16}" width="{fw-16}" height="60" rx="10" fill="#F0EDE8" stroke="#Dcd6cc" stroke-width="1.4"/>')
        s.text(fx + 16, ny + 46, v, size=22, weight=800, fill=INK)
        s.text(fx + 16, ny + 66, k, size=11.5, weight=600, fill=MUTED)
    save("05_model_pelatihan", s)


# =====================================================================
# 6. ALUR INFERENSI  predict()
# =====================================================================
def d6():
    W = 1200
    s = SVG(W, 1290)
    s.header("Penyajian . Inferensi", "Alur Inferensi pada MesinSentimen.predict()",
             "Prapemrosesan sama persis dengan pelatihan; aturan pasti menutup kasus yang sulit",
             "inference.py")
    col = 120
    cw = 640
    ccx = col + cw / 2
    y = 168

    def down(n, g=26):
        return n[1] + n[3] + g

    steps = [
        ("Teks masuk (mentah, boleh kotor)", ["emoji, campur bahasa, hingga string kosong tetap aman"], "raw"),
        ("bersihkan(): sama seperti pelatihan", ["NFKC, buang kontrol, rapikan spasi, tanpa beda perlakuan"], "prep"),
        ("Pengaman string kosong", ["teks kosong disisipi zero-width space agar tokenizer tidak gagal"], "prep"),
        ("Tokenisasi", ["truncation, max_len 128, padding per batch"], "model"),
        ("Encoder dan tiga kepala menghasilkan logits", ["spam, sikap, dan emosi dihitung sekali jalan"], "model"),
        ("Kalibrasi: softmax(logits / suhu)", ["menghasilkan probabilitas terkalibrasi tiap tugas"], "cal"),
        ("argmax memilih kelas dan keyakinan", ["abstain bila keyakinan di bawah ambang tugas"], "eval"),
    ]
    prev = None
    for t, ln, c in steps:
        n = s.node(col, y, cw, t, ln, c)
        if prev:
            s.arrow([(ccx, prev), (ccx, y)])
        prev = n[1] + n[3]
        y = down(n)

    d1cy = y + 52
    s.diamond(ccx, d1cy, 300, 104, ["spam?"], "decision")
    s.arrow([(ccx, prev), (ccx, d1cy - 52)])
    ov1 = s.node(820, d1cy - 34, 320, "sikap dijadikan tak_jelas",
                 ["komentar spam tidak diberi sikap"], "danger", ts=13.5, ss=11)
    s.arrow([(ccx + 150, d1cy), (820, d1cy)], color="#D65A59", marker="arwR",
            label="ya", label_xy=((ccx + 150 + 820) / 2, d1cy - 13))

    y = d1cy + 52 + 22
    d2cy = y + 52
    s.diamond(ccx, d2cy, 300, 104, ["hanya emoji?"], "decision")
    s.arrow([(ccx, d1cy + 52), (ccx, d2cy - 52)], label="tidak", label_xy=(ccx, (d1cy + 52 + d2cy - 52) / 2))
    ov2 = s.node(820, d2cy - 40, 320, "Aturan emoji yang pasti",
                 ["sikap menjadi tak_jelas; emosi diambil",
                  "dari peta emoji; abstain emosi dimatikan"], "cal", ts=13.5, ss=11)
    s.arrow([(ccx + 150, d2cy), (820, d2cy)], color="#199e70", marker="arwG",
            label="ya", label_xy=((ccx + 150 + 820) / 2, d2cy - 13))

    y = d2cy + 52 + 40
    finw = cw + 60
    fin = s.node(col, y, finw, "Prediksi (objek hasil)",
                 ["spam (bool), sikap, emosi,",
                  "keyakinan, abstain, dan prob (distribusi penuh tiap tugas)"], "serve")
    fin_right = col + finw
    fin_cy = fin[1] + fin[3] / 2
    s.arrow([(ccx, d2cy + 52), (ccx, fin[1])], label="tidak", label_xy=(ccx, (d2cy + 52 + fin[1]) / 2))
    ov_right = 820 + 320
    s.arrow([(ov_right, d1cy), (ov_right + 30, d1cy), (ov_right + 30, fin_cy), (fin_right, fin_cy)],
            width=1.5, dashed=True, color="#D65A59", marker="arwR")
    s.arrow([(ov_right, d2cy + 2), (ov_right + 16, d2cy + 2), (ov_right + 16, fin_cy + 10), (fin_right, fin_cy + 10)],
            width=1.5, dashed=True, color="#199e70", marker="arwG")
    s.text(col, fin[1] + fin[3] + 36,
           "Aturan spam dan emoji menimpa kelas hasil argmax sebelum prediksi akhir dikembalikan.",
           size=13, weight=600, fill=MUTED)
    save("06_inferensi", s)


# =====================================================================
# 7. ARSITEKTUR PENYAJIAN  (Streamlit dan Space HuggingFace)
# =====================================================================
def d7():
    W = 1300
    s = SVG(W, 800)
    s.header("Penyajian . Coba Model", "Arsitektur Inferensi Langsung pada Aplikasi",
             "Streamlit tetap ringan tanpa GPU; inferensi berat berjalan di Space HuggingFace",
             "app.py . space/app.py")
    y = 210
    u = s.node(60, y, 220, "Pengguna", ["mengetik komentar", "pada halaman Coba Model"], "io", ts=15)
    app = s.node(330, y, 300, "Streamlit Cloud", ["aplikasi ringan tanpa torch,",
                                                   "memanggil lewat requests"], "serve", ts=15)
    space = s.node(720, y, 340, "Space HuggingFace (Gradio)",
                   ["hardware ZeroGPU atau CPU basic,",
                    "endpoint /gradio_api/call/analisis"], "model", ts=15)
    ucy = y + u[3] / 2
    s.arrow([(u[0] + u[2], ucy), (app[0], ucy)])
    s.arrow([(app[0] + app[2], ucy), (space[0], ucy)], label="permintaan (requests)",
            label_xy=((app[0] + app[2] + space[0]) / 2, ucy - 16))
    s.arrow([(space[0], ucy + 34), (app[0] + app[2], ucy + 34)], color="#199e70", marker="arwG",
            label="balasan SSE (event complete)", label_xy=((app[0] + app[2] + space[0]) / 2, ucy + 34 + 16))

    iy = y + space[3] + 46
    b1 = s.node(720, iy, 340, "Memuat bobot (snapshot_download)",
                ["dari repo model indobert-sentimen-chromebook"], "artifact", ts=13.5, ss=11)
    b2 = s.node(720, iy + b1[3] + 20, 340, "inference.py . MesinSentimen",
                ["memakai GPU (@spaces.GPU) saat tersedia"], "model", ts=13.5, ss=11)
    scx = space[0] + space[2] / 2
    s.arrow([(scx, space[1] + space[3]), (scx, b1[1])], dashed=True, width=1.6)
    s.arrow([(scx, b1[1] + b1[3]), (scx, b2[1])], width=1.6)

    fy = iy + b1[3] + 20
    fb = s.node(330, fy, 300, "Cadangan: model torch lokal",
                ["dipakai bila kuota ZeroGPU habis",
                 "dan hanya berjalan di lingkungan lokal"], "danger", ts=13.5, ss=11)
    s.arrow([(app[0] + app[2] / 2, app[1] + app[3]), (app[0] + app[2] / 2, fy)], dashed=True,
            marker="arwR", color="#D65A59", label="bila gagal", label_xy=(app[0] + app[2] / 2, (app[1] + app[3] + fy) / 2))

    res = s.node(60, fy, 220, "Kartu prediksi", ["sikap, emosi, keyakinan,", 'penanda "model ragu"'], "eval", ts=14, ss=11)
    s.arrow([(app[0] + app[2] / 2, app[1] + app[3]), (app[0] + app[2] / 2, fy - 18),
             (res[0] + res[2] / 2, fy - 18), (res[0] + res[2] / 2, fy)], width=1.6)
    save("07_serving", s)


if __name__ == "__main__":
    d1(); d2(); d3(); d4(); d5(); d6(); d7()
    print("done")
