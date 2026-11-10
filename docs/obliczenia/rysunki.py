#!/usr/bin/env python3
"""
Rysunki schematow (matplotlib, pelna kontrola geometrii).
Uruchomienie: python3 docs/obliczenia/rysunki.py
Tworzy: docs/charts/schemat_A.png, docs/charts/schemat_B.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Polygon, Rectangle

OUT = os.path.join(os.path.dirname(__file__), "..", "charts")
os.makedirs(OUT, exist_ok=True)

LW = 2.0
C_WIRE = "#1a1a1a"
C_HOT = "#c1272d"
C_CTRL = "#1565c0"
C_SET = "#2e7d32"
C_TXT = "#222222"
FS = 11


def line(ax, *pts, color=C_WIRE, lw=LW, ls="-", z=2):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls,
            solid_capstyle="round", zorder=z)


def dot(ax, p, color=C_WIRE, s=6):
    ax.plot([p[0]], [p[1]], "o", ms=s, color=color, zorder=6)


def res_v(ax, x, y_top, y_bot, label=None, color=C_WIRE, side="right", w=0.5, h=1.5, fs=FS - 1):
    y_mid = (y_top + y_bot) / 2
    ax.add_patch(Rectangle((x - w / 2, y_mid - h / 2), w, h, facecolor="white",
                           edgecolor=color, lw=LW, zorder=3))
    line(ax, (x, y_top), (x, y_mid + h / 2), color=color)
    line(ax, (x, y_mid - h / 2), (x, y_bot), color=color)
    if label:
        dx = 0.45 if side == "right" else -0.45
        ax.text(x + dx, y_mid, label, ha="left" if side == "right" else "right",
                va="center", fontsize=fs, color=color, zorder=7)


def res_h(ax, x1, x2, y, label=None, color=C_WIRE, side="top", w=1.6, fs=FS - 1):
    x_mid = (x1 + x2) / 2
    ax.add_patch(Rectangle((x_mid - w / 2, y - 0.25), w, 0.5, facecolor="white",
                           edgecolor=color, lw=LW, zorder=3))
    line(ax, (x1, y), (x_mid - w / 2, y), color=color)
    line(ax, (x_mid + w / 2, y), (x2, y), color=color)
    if label:
        dy = 0.4 if side == "top" else -0.4
        ax.text(x_mid, y + dy, label, ha="center",
                va="bottom" if side == "top" else "top", fontsize=fs, color=color, zorder=7)


def fuse_h(ax, x1, x2, y, label=None, color=C_WIRE):
    x_mid = (x1 + x2) / 2
    ax.add_patch(Rectangle((x_mid - 0.8, y - 0.25), 1.6, 0.5, facecolor="white",
                           edgecolor=color, lw=LW, zorder=3))
    line(ax, (x_mid - 0.8, y), (x_mid + 0.8, y), color=color, lw=1.2, z=4)
    line(ax, (x1, y), (x_mid - 0.8, y), color=color)
    line(ax, (x_mid + 0.8, y), (x2, y), color=color)
    if label:
        ax.text(x_mid, y + 0.4, label, ha="center", va="bottom", fontsize=FS - 1, color=color)


def ground(ax, x, y, label=None):
    for i, w in enumerate([0.9, 0.58, 0.28]):
        line(ax, (x - w / 2, y - i * 0.2), (x + w / 2, y - i * 0.2), lw=LW - 0.4)
    if label:
        ax.text(x, y - 0.85, label, ha="center", va="top", fontsize=FS - 1, color=C_TXT)


def mosfet(ax, xg, y, hi=1.2, lo=1.2, color=C_WIRE):
    """N-MOSFET: dren u gory, zrodlo u dolu, bramka z lewej. Zwraca (dren, zrodlo, bramka)."""
    x_ch = xg + 0.36
    y_top, y_bot = y + 0.8, y - 0.8
    for y0, y1 in [(y_top, y_top - 0.42), (y - 0.24, y + 0.24), (y_bot, y_bot + 0.42)]:
        line(ax, (x_ch, y0), (x_ch, y1), lw=LW + 1.2, color=color)
    line(ax, (xg, y_top - 0.55), (xg, y_bot + 0.55), color=color)
    xd = x_ch + 0.7
    line(ax, (x_ch, y_top), (xd, y_top), color=color)
    line(ax, (xd, y_top), (xd, y_top + hi), color=color)
    line(ax, (x_ch, y_bot), (xd, y_bot), color=color)
    line(ax, (xd, y_bot), (xd, y_bot - lo), color=color)
    line(ax, (xd, y), (xd, y_bot), color=color)
    ax.add_patch(Polygon([[xd, y], [x_ch + 0.1, y + 0.13], [x_ch + 0.1, y - 0.13]],
                         closed=True, color=color, zorder=5))
    return (xd, y_top + hi), (xd, y_bot - lo), (xg, y)


def opamp(ax, x_back, y, size=2.4, color=C_WIRE, label=None):
    x_out = x_back + size
    half = size / 2
    ax.add_patch(Polygon([(x_back, y + half), (x_back, y - half), (x_out, y)],
                         closed=True, facecolor="white", edgecolor=color, lw=LW, zorder=3))
    ax.text(x_back + 0.5, y + half * 0.45, "\u2212", fontsize=FS + 4, ha="center", va="center", color=color, zorder=4)
    ax.text(x_back + 0.5, y - half * 0.45, "+", fontsize=FS + 3, ha="center", va="center", color=color, zorder=4)
    if label:
        ax.text(x_back + 0.35, y - half - 0.3, label, ha="left", va="top", fontsize=FS - 1, color=color)
    return (x_back, y + half * 0.45), (x_back, y - half * 0.45), (x_out, y)


def pot_divider(ax, x, y_top, y_bot, label=None, color=C_SET, fs=FS - 1):
    """Potencjometr jako dzielnik: gora, dol, suwak (zwraca punkt suwaka)."""
    y_mid = (y_top + y_bot) / 2
    h = (y_top - y_bot) - 0.7
    ax.add_patch(Rectangle((x - 0.25, y_mid - h / 2), 0.5, h, facecolor="white",
                           edgecolor=color, lw=LW, zorder=3))
    line(ax, (x, y_top), (x, y_mid + h / 2), color=color)
    line(ax, (x, y_mid - h / 2), (x, y_bot), color=color)
    # suwak
    xa = x + 0.95
    line(ax, (xa, y_mid), (x + 0.28, y_mid), color=color, lw=1.8)
    ax.add_patch(FancyArrow(xa - 0.02, y_mid - 0.32, 0.0, 0.6, width=0.015,
                            head_width=0.24, head_length=0.2, length_includes_head=True,
                            color=color, zorder=5))
    if label:
        ax.text(x - 0.5, y_mid, label, ha="right", va="center", fontsize=fs, color=color)
    return (xa, y_mid)


def frame(figsize, xlim, ylim, title=None):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.text((xlim[0] + xlim[1]) / 2, ylim[1] - 0.1, title, ha="center", va="top",
                fontsize=FS + 1, color=C_TXT, weight="bold")
    return fig, ax



def box(ax, x, y, w, h, text, fc="white", ec=C_WIRE, lw=1.8, fs=FS-2, color=C_TXT, bold=False):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fc, edgecolor=ec,
                           lw=lw, zorder=3, joinstyle="round"))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color, zorder=4,
            weight="bold" if bold else "normal", linespacing=1.35)


def arrow(ax, p1, p2, text=None, color=C_WIRE, lw=1.8, above=True, fs=FS-3, rad=0.0):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=0, shrinkB=0,
                                connectionstyle=f"arc3,rad={rad}"), zorder=2)
    if text:
        xm, ym = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(xm, ym + (0.28 if above else -0.28), text, ha="center",
                va="bottom" if above else "top", fontsize=fs, color=color, zorder=6)


def schemat_a(path):
    fig, ax = frame((8.8, 4.6), (0, 17.4), (0, 9.0),
                    "WARIANT A  \u2014  regulator MOCY: PWM + 1 MOSFET (prosty, ale temperatura dryfuje)")
    y = 6.2
    box(ax, 1.6, y, 2.6, 1.2, "+12 V\nATX", fc="#f5f5f5", bold=True)
    box(ax, 5.1, y, 2.4, 1.2, "bezpiecznik\nPTC 3 A", fc="white")
    box(ax, 9.0, y, 3.2, 1.5, "DRUT\n0,40 mm / 0,60 m\n5,2 \u03a9", fc="#fdecea", ec=C_HOT, color=C_HOT, bold=True)
    box(ax, 13.2, y, 2.6, 1.2, "MOSFET\nIRF3205", fc="white")
    arrow(ax, (2.9, y), (3.9, y))
    arrow(ax, (6.3, y), (7.4, y))
    arrow(ax, (10.6, y), (11.9, y))
    ax.text(11.25, y + 0.62, "2,3 A", ha="center", fontsize=FS - 3, color=C_TXT)
    line(ax, (14.5, y), (15.6, y))
    line(ax, (15.6, y), (15.6, y - 1.0))
    ground(ax, 15.6, y - 1.0, "GND")

    box(ax, 13.2, y - 3.0, 2.6, 1.1, "PWM 0\u2013100 %\nNE555 / modu\u0142", fc="#e8f0fb", ec=C_CTRL, color=C_CTRL)
    arrow(ax, (13.2, y - 2.45), (13.2, y - 0.6), "bramka", color=C_CTRL)

    ax.text(0.2, 1.9,
            "Regulujesz \u015bredni\u0105 moc\u0105. Gdy drut si\u0119 rozci\u0105gnie albo wieje wiatr, temperatura ucieka\n"
            "\u2014 musisz poprawia\u0107 ga\u0142k\u0105. Przewaga: 1 tranzystor, prawie si\u0119 nie grzeje (pracuje impulsowo).",
            fontsize=FS - 3, color="#444", va="top")
    ax.text(0.2, 0.9, "W pe\u0142nej wersji: NE555 w uk\u0142adzie astabilnym + potencjometr 100 k\u03a9 (wype\u0142nienie 5\u201395 %).",
            fontsize=FS - 3, color="#777", va="top")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def schemat_b(path):
    fig, ax = frame((10.2, 6.2), (0, 20.0), (0, 12.0),
                    "WARIANT B  \u2014  p\u0119tla rezystancji: trzyma R drutu = R nastawy (2 uk\u0142ady + MOSFET)")
    y = 9.4
    box(ax, 1.7, y, 2.6, 1.1, "+12 V\nATX", fc="#f5f5f5", bold=True)
    box(ax, 5.0, y, 2.2, 1.1, "PTC\n3 A")
    box(ax, 9.3, y, 3.6, 1.5, "DRUT nichrom\n0,40 mm / 0,60 m\n5,2 \u03a9", fc="#fdecea", ec=C_HOT, color=C_HOT, bold=True)
    box(ax, 14.0, y, 2.4, 1.1, "MOSFET\nIRF3205")
    box(ax, 17.6, y, 2.2, 1.1, "R_sz\n0,33 \u03a9")
    arrow(ax, (3.0, y), (3.9, y))
    arrow(ax, (6.1, y), (7.5, y))
    arrow(ax, (11.1, y), (12.8, y), "I \u2248 1,5 A")
    arrow(ax, (15.2, y), (16.5, y))
    line(ax, (18.7, y), (19.3, y))
    line(ax, (19.3, y), (19.3, y - 1.1))
    ground(ax, 19.3, y - 1.1, "GND",)

    # A1
    box(ax, 15.6, 5.4, 4.0, 1.5, "A1: wzmacniacz\npr\u0105dowy  \u00d720\nU_I = 20\u00b7I\u00b7R_sz",
        fc="#e8f0fb", ec=C_CTRL, color=C_CTRL, fs=FS - 3)
    arrow(ax, (17.6, y - 0.6), (17.0, 4.7), color=C_CTRL, rad=-0.1)
    ax.text(18.05, 6.6, "U_I \u2248 0,5 V", fontsize=FS - 3, color=C_CTRL, va="center")

    # P1
    box(ax, 15.6, 2.6, 4.0, 1.3, "P1 \u2014 NASTAWA\n10 k\u03a9  \u2192  U_ref", fc="#eaf5ec", ec=C_SET,
        color=C_SET, fs=FS - 3)
    arrow(ax, (15.6, 4.65), (15.6, 3.3), color=C_SET)

    # A2
    box(ax, 9.6, 3.4, 4.2, 1.6, "A2: integrator\npor\u00f3wnuje U_drut\nz U_ref", fc="#f3ecfb", ec="#7a4fbf",
        color="#7a4fbf", fs=FS - 3)
    arrow(ax, (13.55, 2.6), (11.7, 3.05), color=C_SET, above=False)
    arrow(ax, (9.3, 8.6), (9.6, 4.25), color=C_HOT)
    ax.text(9.65, 6.3, "U_drut\n\u2248 8,0 V", fontsize=FS - 3, color=C_HOT, ha="left")
    arrow(ax, (10.6, 2.6), (13.4, 8.85), color="#7a4fbf", rad=0.18)
    ax.text(12.6, 4.3, "bramka", fontsize=FS - 3, color="#7a4fbf", ha="left")

    ax.text(0.2, 1.5,
            "A2 robi wszystko: gdy drut stygnie (np. pianka odbiera ciep\u0142o, albo wieje), jego op\u00f3r ro\u015bnie,\n"
            "U_drut przestaje si\u0119 zgadza\u0107 z U_ref \u2014 A2 podnosi pr\u0105d i temperatura wraca w ~1 s.\n"
            "Zakres nastawy pokr\u0119tla P1: 5,16 \u03a9 (20 \u00b0C) \u2026 5,45 \u03a9 (400 \u00b0C); 250 \u00b0C \u2248 5,34 \u03a9.",
            fontsize=FS - 3.5, color="#444", va="top")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    schemat_a(os.path.join(OUT, "schemat_A.png"))
    schemat_b(os.path.join(OUT, "schemat_B.png"))
    print("ok")
