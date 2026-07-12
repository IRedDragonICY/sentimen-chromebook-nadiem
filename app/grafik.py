"""Fungsi grafik Plotly — mengikuti kaidah skill dataviz.

Prinsip: satu grafik menjawab satu pertanyaan; palet sikap/emosi tervalidasi &
konsisten; label langsung ketimbang legenda berlebih; sumbu jujur (bar mulai 0).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .tema import (
    EMOSI_LABEL, EMOSI_WARNA, FASE_LABEL, FASE_URUT,
    SIKAP_LABEL, SIKAP_WARNA, plotly_layout,
)


def _w(peta, k, gelap):
    return peta.get(k, ("#94a3b8", "#6b7280"))[1 if gelap else 0]


def komposisi_sikap(df: pd.DataFrame, gelap=False) -> go.Figure:
    """Berapa besar tiap sikap? Bar horizontal terurut + label langsung."""
    vc = df["sikap"].value_counts()
    urut = [k for k in SIKAP_WARNA if k in vc.index]
    urut = sorted(urut, key=lambda k: vc[k])
    total = vc.sum()
    fig = go.Figure()
    for k in urut:
        fig.add_bar(
            y=[SIKAP_LABEL[k]], x=[vc[k]], orientation="h",
            marker_color=_w(SIKAP_WARNA, k, gelap), showlegend=False,
            text=[f"{vc[k] / total:.0%}"], textposition="outside",
            hovertemplate=f"{SIKAP_LABEL[k]}: {vc[k]:,} komentar<extra></extra>",
        )
    lay = plotly_layout(gelap)
    lay["xaxis"]["visible"] = False
    fig.update_layout(**lay, height=290, bargap=0.32)
    return fig


def tren_sikap_fase(df: pd.DataFrame, gelap=False) -> go.Figure:
    """Bagaimana komposisi sikap bergeser antar fase peristiwa? Bar 100% bertumpuk."""
    fase_ada = [f for f in FASE_URUT if f in df["fase"].unique()]
    tab = (pd.crosstab(df["fase"], df["sikap"], normalize="index") * 100).reindex(fase_ada)
    fig = go.Figure()
    for k in SIKAP_WARNA:
        if k not in tab.columns:
            continue
        fig.add_bar(
            x=[FASE_LABEL[f] for f in fase_ada], y=tab[k].values, name=SIKAP_LABEL[k],
            marker_color=_w(SIKAP_WARNA, k, gelap),
            hovertemplate="%{y:.0f}%<extra>" + SIKAP_LABEL[k] + "</extra>",
        )
    lay = plotly_layout(gelap)
    lay["yaxis"]["ticksuffix"] = "%"
    lay["barmode"] = "stack"
    lay["legend"] = dict(orientation="h", y=-0.18, font=lay["legend"]["font"],
                         bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**lay, height=420)
    return fig


def volume_harian(df: pd.DataFrame, gelap=False) -> go.Figure:
    """Kapan lonjakan percakapan terjadi? Garis volume harian."""
    harian = df.groupby("tanggal").size().reset_index(name="n")
    fig = go.Figure()
    fig.add_scatter(
        x=harian["tanggal"], y=harian["n"], mode="lines",
        line=dict(color="#2a78d6" if not gelap else "#3987e5", width=2),
        fill="tozeroy", fillcolor="rgba(42,120,214,.10)",
        hovertemplate="%{x|%d %b %Y}: %{y:,} komentar<extra></extra>",
    )
    fig.update_layout(**plotly_layout(gelap), height=300)
    return fig


def emosi_bar(df: pd.DataFrame, gelap=False) -> go.Figure:
    """Emosi dominan apa? Bar vertikal + label langsung."""
    vc = df["emosi"].value_counts()
    urut = [k for k in EMOSI_WARNA if k in vc.index]
    total = vc.sum()
    fig = go.Figure()
    for k in urut:
        fig.add_bar(
            x=[EMOSI_LABEL[k]], y=[vc[k]], marker_color=_w(EMOSI_WARNA, k, gelap),
            showlegend=False, text=[f"{vc[k] / total:.0%}"], textposition="outside",
            hovertemplate=f"{EMOSI_LABEL[k]}: {vc[k]:,}<extra></extra>",
        )
    lay = plotly_layout(gelap)
    lay["yaxis"]["visible"] = False
    fig.update_layout(**lay, height=300, bargap=0.35)
    return fig


def sikap_per_target_topik(pivot: pd.DataFrame, gelap=False) -> go.Figure:
    """Sikap dominan per topik/sub-isu. pivot: index=topik, kolom=sikap (proporsi %)."""
    fig = go.Figure()
    for k in SIKAP_WARNA:
        if k not in pivot.columns:
            continue
        fig.add_bar(
            y=pivot.index, x=pivot[k].values, orientation="h", name=SIKAP_LABEL[k],
            marker_color=_w(SIKAP_WARNA, k, gelap),
            hovertemplate="%{x:.0f}%<extra>" + SIKAP_LABEL[k] + "</extra>",
        )
    lay = plotly_layout(gelap)
    lay["xaxis"]["ticksuffix"] = "%"
    lay["barmode"] = "stack"
    lay["legend"] = dict(orientation="h", y=-0.15, font=lay["legend"]["font"],
                         bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**lay, height=90 + 46 * len(pivot))
    return fig
