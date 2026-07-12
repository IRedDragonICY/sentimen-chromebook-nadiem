"""Komponen UI reusable — KPI, pill sikap, kartu komentar, state kosong.

Semua komponen memakai token dari tema.py. Username tidak pernah ditampilkan
(privasi/PII) — lihat anonimisasi di muat_data.
"""

from __future__ import annotations

import html

import streamlit as st

from .tema import EMOSI_LABEL, EMOSI_WARNA, SIKAP_LABEL, SIKAP_WARNA


def hero(kicker: str, judul: str, deskripsi: str):
    st.markdown(
        f'<div class="hero"><div class="kicker">{html.escape(kicker)}</div>'
        f"<h1>{html.escape(judul)}</h1><p>{html.escape(deskripsi)}</p></div>",
        unsafe_allow_html=True,
    )


def kpi_grid(item: list[dict]):
    """item: [{label, value, sub}]."""
    kartu = "".join(
        f'<div class="kpi"><div class="label">{html.escape(i["label"])}</div>'
        f'<div class="value">{i["value"]}</div>'
        f'<div class="sub">{html.escape(i.get("sub", ""))}</div></div>'
        for i in item
    )
    st.markdown(f'<div class="kpi-grid">{kartu}</div>', unsafe_allow_html=True)


def _pill(teks: str, warna: str) -> str:
    # Latar transparan dari warna (agar teks tetap kontras di terang/gelap).
    return (f'<span class="pill" style="background:{warna}1f;color:{warna};'
            f'border-color:{warna}3d"><span class="dot" style="background:{warna}"></span>'
            f"{html.escape(teks)}</span>")


def pill_sikap(sikap: str, gelap=False) -> str:
    return _pill(SIKAP_LABEL.get(sikap, sikap), SIKAP_WARNA.get(sikap, ("#94a3b8",))[0])


def pill_emosi(emosi: str, gelap=False) -> str:
    return _pill(EMOSI_LABEL.get(emosi, emosi), EMOSI_WARNA.get(emosi, ("#94a3b8",))[0])


def kartu_komentar(teks: str, sikap: str, emosi: str, likes: int, fase_label: str,
                   keyakinan: float | None = None):
    warna = SIKAP_WARNA.get(sikap, ("#94a3b8",))[0]
    meta = f"{pill_sikap(sikap)} {pill_emosi(emosi)} · {likes:,} suka · {html.escape(fase_label)}"
    if keyakinan is not None:
        meta += f" · keyakinan {keyakinan:.0%}"
    st.markdown(
        f'<div class="komentar" style="border-left-color:{warna}">{html.escape(teks)}'
        f'<div class="meta">{meta}</div></div>',
        unsafe_allow_html=True,
    )


def judul_bagian(judul: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{html.escape(judul)}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{html.escape(sub)}</div>', unsafe_allow_html=True)


def state_kosong(pesan: str):
    st.markdown(
        f'<div class="disclaimer">Tak ada data untuk filter ini. {html.escape(pesan)}</div>',
        unsafe_allow_html=True,
    )


def disclaimer(teks: str):
    st.markdown(f'<div class="disclaimer">{teks}</div>', unsafe_allow_html=True)
