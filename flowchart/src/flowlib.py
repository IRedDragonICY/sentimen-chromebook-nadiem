"""Pustaka kecil untuk menyusun flowchart SVG yang rapi (dirender ke PNG via rsvg-convert).

Semua diagram memakai satu sistem desain: latar hangat, tinta gelap, aksen teal,
kategori tahap dikodekan warna. Tanpa emoji di teks (hindari tofu di rsvg).
"""
from __future__ import annotations

FONT = "Noto Sans"
INK = "#1A1614"
MUTED = "#5C564F"
MUTED2 = "#8A837A"
BG = "#FBFAF9"

# fill, border  (per kategori tahap)
CAT = {
    "raw":      ("#FCEED1", "#E0A83A"),
    "prep":     ("#E0F2EA", "#1F9E72"),
    "norm":     ("#E0F2EA", "#1F9E72"),
    "gold":     ("#FBEFCF", "#D9A521"),
    "silver":   ("#EBEEF3", "#8A94A6"),
    "label":    ("#ECE8F7", "#6B5BD1"),
    "split":    ("#E1ECFB", "#2F79D6"),
    "model":    ("#E1EFEB", "#0E6B5E"),
    "cal":      ("#F6E7F1", "#B0559A"),
    "eval":     ("#E6EDF9", "#3F6FB0"),
    "serve":    ("#DDEDE5", "#0E4D45"),
    "artifact": ("#F0EDE8", "#9A9186"),
    "decision": ("#FCEED1", "#E0A83A"),
    "danger":   ("#FBE2E1", "#D65A59"),
    "io":       ("#ECEAE5", "#6B655C"),
    "note":     ("#FFFDF6", "#D9C9A0"),
}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SVG:
    def __init__(self, w, h, bg=None):
        # bg=None -> latar transparan (menyatu dengan papan tulis Canva).
        self.w, self.h, self.bg = w, h, bg
        self.p: list[str] = []

    def add(self, s): self.p.append(s)

    def render(self) -> str:
        defs = (
            '<defs>'
            '<marker id="arw" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#7C766C"/></marker>'
            '<marker id="arwR" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#D65A59"/></marker>'
            '<marker id="arwG" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#199e70"/></marker>'
            '</defs>'
        )
        body = "".join(self.p)
        bg = f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{self.bg}"/>' if self.bg else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">'
            f'{bg}{defs}{body}</svg>'
        )

    # ---- primitives -----------------------------------------------------
    def text(self, x, y, s, size=13, weight=400, fill=INK, anchor="start", spacing=None):
        sp = f' letter-spacing="{spacing}"' if spacing else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{sp}>{esc(s)}</text>')

    def node(self, x, y, w, title, lines=None, cat="prep", h=None,
             ts=15.5, ss=12.5, tw=700, title_fill=INK):
        lines = lines or []
        pad = 14
        tlh = ts + 8
        slh = ss + 6
        if h is None:
            h = pad * 2 + tlh + (len(lines) * slh) + (2 if lines else -6)
        fill, border = CAT[cat]
        # shadow
        self.add(f'<rect x="{x}" y="{y+3}" width="{w}" height="{h}" rx="13" ry="13" fill="#1a140f" opacity="0.06"/>')
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="13" ry="13" '
                 f'fill="{fill}" stroke="{border}" stroke-width="1.8"/>')
        # accent tab
        self.add(f'<rect x="{x}" y="{y+11}" width="5" height="{h-22}" rx="2.5" fill="{border}"/>')
        tx = x + pad + 4
        ty = y + pad + ts
        self.text(tx, ty, title, size=ts, weight=tw, fill=title_fill)
        cy = ty
        for ln in lines:
            cy += slh
            self.text(tx, cy, ln, size=ss, weight=400, fill=MUTED)
        return (x, y, w, h)

    def chip(self, x, y, w, title, sub=None, cat="artifact", h=None, ts=13.5, ss=11.5):
        pad = 11
        h = h or (pad * 2 + ts + (ss + 4 if sub else -4))
        fill, border = CAT[cat]
        self.add(f'<rect x="{x}" y="{y+2}" width="{w}" height="{h}" rx="10" fill="#1a140f" opacity="0.05"/>')
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                 f'fill="{fill}" stroke="{border}" stroke-width="1.5"/>')
        self.text(x + pad, y + pad + ts - 2, title, size=ts, weight=700, fill=INK)
        if sub:
            self.text(x + pad, y + pad + ts + ss + 2, sub, size=ss, weight=400, fill=MUTED)
        return (x, y, w, h)

    def diamond(self, cx, cy, w, h, lines, cat="decision", ss=12.5):
        fill, border = CAT[cat]
        pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
        self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{border}" stroke-width="1.8"/>')
        n = len(lines)
        y0 = cy - (n - 1) * (ss + 4) / 2 + ss / 2 - 1
        for i, ln in enumerate(lines):
            self.text(cx, y0 + i * (ss + 4), ln, size=ss, weight=600, fill=INK, anchor="middle")
        return (cx, cy, w, h)

    def arrow(self, pts, color="#7C766C", marker="arw", dashed=False, width=2.0,
              label=None, label_xy=None, lsize=12):
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"'
                 f'{dash} marker-end="url(#{marker})" stroke-linecap="round" stroke-linejoin="round"/>')
        if label:
            if label_xy is None:
                mx = (pts[0][0] + pts[-1][0]) / 2
                my = (pts[0][1] + pts[-1][1]) / 2
            else:
                mx, my = label_xy
            wl = len(label) * lsize * 0.56 + 14
            self.add(f'<rect x="{mx-wl/2}" y="{my-lsize/2-5}" width="{wl}" height="{lsize+10}" '
                     f'rx="{(lsize+10)/2}" fill="#FFFFFF" stroke="#E3DED6" stroke-width="1"/>')
            self.text(mx, my + lsize * 0.34, label, size=lsize, weight=600, fill=MUTED, anchor="middle")

    # ---- page furniture -------------------------------------------------
    def header(self, kicker, title, subtitle, step=None):
        self.text(56, 52, kicker.upper(), size=13, weight=700, fill="#1F9E72", spacing="2.5")
        self.text(55, 88, title, size=29, weight=800, fill=INK)
        if subtitle:
            self.text(56, 116, subtitle, size=15, weight=400, fill=MUTED)
        self.add(f'<rect x="56" y="132" width="64" height="4" rx="2" fill="#1baf7a"/>')
        if step:
            self.text(self.w - 56, 52, step, size=13, weight=700, fill=MUTED2, anchor="end")

    def footer(self):
        y = self.h - 26
        self.add(f'<line x1="56" y1="{y-16}" x2="{self.w-56}" y2="{y-16}" stroke="#E7E1D8" stroke-width="1"/>')
        self.text(56, y, "Cermin Publik - Analisis Sentimen Kasus Pengadaan Chromebook",
                  size=11.5, weight=600, fill=MUTED2)
        self.text(self.w - 56, y, "Mohammad Farid Hendianto  .  2200018401  .  Universitas Ahmad Dahlan",
                  size=11.5, weight=400, fill=MUTED2, anchor="end")

    def legend(self, x, y, items, box=10, gap=150):
        # items: list of (label, cat)
        for i, (lab, cat) in enumerate(items):
            fill, border = CAT[cat]
            cx = x + i * gap
            self.add(f'<rect x="{cx}" y="{y-box}" width="{box+3}" height="{box+3}" rx="3" '
                     f'fill="{fill}" stroke="{border}" stroke-width="1.5"/>')
            self.text(cx + box + 8, y, lab, size=12, weight=600, fill=MUTED)
