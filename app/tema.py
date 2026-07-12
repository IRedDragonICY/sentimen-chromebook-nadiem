"""Sistem desain aplikasi — token, warna, dan template Plotly.

Satu sumber kebenaran untuk warna & tipografi (lihat skills/design-system).
Palet sikap/emosi memakai slot kategorikal yang sudah divalidasi colorblind-safe
(skill dataviz): CVD ΔE > 60 pada mode terang & gelap. Kelas "netral"/"tak_jelas"
sengaja abu — dimitigasi label langsung + tampilan tabel.
"""

from __future__ import annotations

# --- Palet kategorikal tervalidasi (light, dark) --------------------------------
SIKAP_WARNA = {
    "pro_nadiem": ("#1baf7a", "#199e70"),
    "kontra_nadiem": ("#e34948", "#e66767"),
    "kritik_peradilan": ("#4a3aa7", "#9085e9"),
    "kritik_pemerintah": ("#2a78d6", "#3987e5"),
    "netral_informasional": ("#eda100", "#c98500"),
    "tak_jelas": ("#94a3b8", "#6b7280"),
}
EMOSI_WARNA = {
    "marah": ("#e34948", "#e66767"),
    "duka": ("#4a3aa7", "#9085e9"),
    "sinis": ("#eda100", "#c98500"),
    "harapan": ("#1baf7a", "#199e70"),
    "netral": ("#94a3b8", "#6b7280"),
}

# --- Label tampilan Bahasa Indonesia -------------------------------------------
SIKAP_LABEL = {
    "pro_nadiem": "Mendukung Nadiem",
    "kontra_nadiem": "Menentang Nadiem",
    "kritik_peradilan": "Kritik Peradilan",
    "kritik_pemerintah": "Kritik Pemerintah",
    "netral_informasional": "Netral / Informasi",
    "tak_jelas": "Tak Jelas",
}
EMOSI_LABEL = {
    "marah": "Marah", "duka": "Duka", "sinis": "Sinis",
    "harapan": "Harapan", "netral": "Netral",
}
FASE_LABEL = {
    "f1_sep2025": "Penyelidikan awal · Sep 2025",
    "f2_awal2026": "Babak KPK · Jan–Feb 2026",
    "f3_mei2026": "Penahanan · Mei 2026",
    "f4_jul2026": "Tuntutan & Vonis · Jun–Jul 2026",
}
FASE_URUT = ["f1_sep2025", "f2_awal2026", "f3_mei2026", "f4_jul2026"]


def warna(peta, kunci, gelap=False):
    return peta[kunci][1 if gelap else 0]


def peta_warna_plotly(peta, gelap=False):
    return {k: v[1 if gelap else 0] for k, v in peta.items()}


# --- CSS: token + reset chrome Streamlit ---------------------------------------
CSS = """
<style>
:root{
  --bg:#FBFAF9; --surface:#FFFFFF; --surface-2:#F4F2EF; --border:#E7E3DD;
  --ink:#1A1614; --ink-2:#5C564F; --ink-3:#8A837A;
  --brand:#0E4D45; --brand-2:#1baf7a; --brand-ink:#0a3a34;
  --radius:14px; --radius-sm:8px; --radius-pill:999px;
  --shadow:0 1px 2px rgba(20,17,15,.04), 0 4px 16px rgba(20,17,15,.06);
  --shadow-lg:0 2px 6px rgba(20,17,15,.05), 0 12px 32px rgba(20,17,15,.10);
  --font:-apple-system,"Segoe UI",Roboto,Inter,"Helvetica Neue",sans-serif;
}
@media (prefers-color-scheme: dark){
 :root{
  --bg:#14110F; --surface:#1E1A17; --surface-2:#262019; --border:#332C25;
  --ink:#F4F1EC; --ink-2:#B9B2A8; --ink-3:#8A837A;
  --brand:#1baf7a; --brand-2:#2ed3a0; --brand-ink:#d9fbef;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 6px 20px rgba(0,0,0,.35);
  --shadow-lg:0 2px 8px rgba(0,0,0,.4), 0 16px 40px rgba(0,0,0,.5);
 }
}
html, body, [class*="css"]{ font-family:var(--font); }
.stApp{ background:var(--bg); color:var(--ink); }
.block-container{ max-width:1180px; padding-top:2.4rem; padding-bottom:4rem; }

/* Header hero */
.hero{ margin-bottom:1.6rem; }
.hero .kicker{ font-size:.78rem; font-weight:700; letter-spacing:.08em;
  text-transform:uppercase; color:var(--brand); }
.hero h1{ font-size:2.35rem; line-height:1.12; font-weight:800; margin:.35rem 0 .5rem;
  letter-spacing:-.02em; color:var(--ink); }
.hero p{ font-size:1.02rem; color:var(--ink-2); max-width:70ch; line-height:1.55; margin:0; }

/* KPI card */
.kpi-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:16px; margin:1rem 0 1.4rem; }
.kpi{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:20px 22px; box-shadow:var(--shadow); }
.kpi .label{ font-size:.8rem; font-weight:600; color:var(--ink-2); letter-spacing:.01em; }
.kpi .value{ font-size:2.35rem; font-weight:800; color:var(--ink); line-height:1.05;
  margin-top:.28rem; font-variant-numeric:tabular-nums; letter-spacing:-.02em; }
.kpi .sub{ font-size:.82rem; color:var(--ink-3); margin-top:.3rem; }

/* Pill / badge */
.pill{ display:inline-flex; align-items:center; gap:.4rem; padding:.22rem .6rem;
  border-radius:var(--radius-pill); font-size:.78rem; font-weight:650;
  border:1px solid transparent; }
.pill .dot{ width:.55rem; height:.55rem; border-radius:50%; }

/* Card + section */
.card{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:22px 24px; box-shadow:var(--shadow); margin-bottom:16px; }
.section-title{ font-size:1.32rem; font-weight:750; letter-spacing:-.01em;
  margin:1.8rem 0 .2rem; color:var(--ink); }
.section-sub{ font-size:.92rem; color:var(--ink-2); margin:0 0 1rem; max-width:74ch; line-height:1.5; }

/* Quote / contoh komentar */
.komentar{ border-left:3px solid var(--border); padding:.55rem 0 .55rem .9rem;
  margin:.5rem 0; color:var(--ink); font-size:.95rem; line-height:1.5; }
.komentar .meta{ font-size:.76rem; color:var(--ink-3); margin-top:.3rem; }

/* Disclaimer */
.disclaimer{ background:var(--surface-2); border:1px solid var(--border);
  border-radius:var(--radius-sm); padding:14px 16px; font-size:.86rem;
  color:var(--ink-2); line-height:1.55; }

/* Streamlit tab polish */
.stTabs [data-baseweb="tab-list"]{ gap:4px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"]{ font-weight:600; color:var(--ink-2); }
button[kind="primary"]{ background:var(--brand); border:none; }

#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }
</style>
"""


def plotly_layout(gelap=False):
    """Layout Plotly konsisten dengan token (transparan agar ikut surface app)."""
    ink = "#F4F1EC" if gelap else "#1A1614"
    ink2 = "#B9B2A8" if gelap else "#5C564F"
    grid = "#332C25" if gelap else "#E7E3DD"
    return dict(
        font=dict(family="-apple-system, Segoe UI, Roboto, Inter, sans-serif",
                  color=ink, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor=grid, zerolinecolor=grid, linecolor=grid,
                   tickfont=dict(color=ink2)),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid, linecolor=grid,
                   tickfont=dict(color=ink2)),
        legend=dict(font=dict(color=ink2), bgcolor="rgba(0,0,0,0)"),
        colorway=[SIKAP_WARNA[k][1 if gelap else 0] for k in SIKAP_WARNA],
    )
