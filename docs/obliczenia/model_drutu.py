#!/usr/bin/env python3
"""
Model termiczny drutu oporowego do ciecia pianki + wszystkie liczby i wykresy
uzyte w dokumencie docs/regulacja-drutu-cieplnego.md

Uruchomienie:  python3 docs/obliczenia/model_drutu.py
Wymaga: numpy, matplotlib

Zalozenia:
  * drut nichromowy NiCr 80/20: rho20 = 1.08e-6 ohm*m, alfa = 1.5e-4 1/K,
    cp = 450 J/(kg*K), rho = 8400 kg/m3, emisyjnosc 0.8
  * chlodzenie: konwekcja swobodna poziomego/ pionowego walca (Churchill-Chu)
    + promieniowanie; powietrze 20 C, bezruch (mozna skalowac "przeciagiem")
  * zasilanie: stale napiecie 12 V, "wypelnienie" = udzial czasu zalaczenia
Model jest rzedu wielkosci (+-20 %) - sluzy do doboru drutu i zrozumienia,
ktore efekty sa duze, a ktore pomijalne.
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(__file__), "..", "charts")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
    "axes.edgecolor": "#444", "figure.dpi": 160,
    "font.family": "DejaVu Sans", "axes.titlesize": 9.5,
})

RHO20 = 1.08e-6
ALPHA = 1.5e-4
SIGMA = 5.67e-8
EMIS = 0.80
TA = 293.0
CP = 450.0
RHO_S = 8400.0
V0 = 12.0

EPS_BAND = (200, 250)
XPS_BAND = (260, 300)
LIMIT = 320

D_REC = 0.0004        # zalecany drut
L_REC = 0.60


# ------------------------------------------------------------------ fizyka
def _k_air(t_k):
    return 0.0241 + 7.2e-5 * (t_k - 273.15)


def _nu_air(t_k):
    return 1.32e-5 + 9.6e-8 * (t_k - 273.15)


def h_conv(d, d_t, factor=1.0):
    t_f = TA + d_t / 2.0
    k, nu, pr, beta = _k_air(t_f), _nu_air(t_f), 0.70, 1.0 / t_f
    ra = 9.81 * beta * max(d_t, 1e-3) * d ** 3 / nu ** 2 * pr
    nu_n = max(0.36 + 0.518 * ra ** 0.25 / (1 + (0.559 / pr) ** (9 / 16)) ** (4 / 9), 0.5)
    return factor * nu_n * k / d


def q_loss(d, t_k, length, factor=1.0):
    """Straty ciepla drutu [W]."""
    d_t = max(t_k - TA, 1e-3)
    return (h_conv(d, d_t, factor) * d_t + EMIS * SIGMA * (t_k ** 4 - TA ** 4)) * math.pi * d * length


def r_cold(d=L_REC, length=L_REC):
    return RHO20 * length / (math.pi * (d / 2) ** 2)


def r_hot(d, length, t_k):
    return r_cold(d, length) * (1 + ALPHA * (t_k - TA))


def t_steady(d, length, duty, v=V0, factor=1.0):
    """Temperatura ustalona [C] przy stalym wypelnieniu."""
    t = 380.0
    for _ in range(300):
        r = r_hot(d, length, t)
        p = duty * v * v / r
        lo, hi = TA + 0.2, 1800.0
        for _ in range(90):
            mid = (lo + hi) / 2
            if q_loss(d, mid, length, factor) < p:
                lo = mid
            else:
                hi = mid
        t_new = (lo + hi) / 2
        if abs(t_new - t) < 0.05:
            return t_new - 273.15
        t = 0.5 * t + 0.5 * t_new
    return t - 273.15


def duty_for(d, length, t_c, v=V0, factor=1.0):
    lo, hi = 0.005, 1.0
    for _ in range(55):
        mid = (lo + hi) / 2
        if t_steady(d, length, mid, v, factor) < t_c:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def operating_point(d, length, t_c, v=V0, factor=1.0):
    """(wypelnienie, moc, prad) potrzebne do utrzymania t_c."""
    duty = duty_for(d, length, t_c, v, factor)
    r = r_hot(d, length, t_c + 273)
    p = duty * v * v / r
    return duty, p, math.sqrt(p / r)


def u_for_temperature(d, length, t_c, factor=1.0):
    """Napiecie na drucie, ktore ustabilizuje temperature t_c (petla liniowa)."""
    lo, hi = 0.5, 12.0
    for _ in range(60):
        mid = (lo + hi) / 2
        r = r_hot(d, length, mid ** 2 / 1.0 if False else t_c + 273)
        # rownowaga: P = U^2/R(T) == straty(T)
        p = mid ** 2 / r
        if p < q_loss(d, t_c + 273, length, factor):
            lo = mid
        else:
            hi = mid
    u = (lo + hi) / 2
    return u, u ** 2 / r_hot(d, length, t_c + 273)


def t_for_voltage(d, length, u, factor=1.0):
    """Temperatura ustalona przy zadanym napieciu na drucie (petla liniowa)."""
    t = 400.0
    for _ in range(200):
        r = r_hot(d, length, t)
        p = u * u / r
        lo, hi = TA + 0.2, 1800.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if q_loss(d, mid, length, factor) < p:
                lo = mid
            else:
                hi = mid
        t_new = (lo + hi) / 2
        if abs(t_new - t) < 0.05:
            return t_new - 273.15
        t = 0.5 * t + 0.5 * t_new
    return t - 273.15


# ------------------------------------------------------------------ wykresy
def chart_t_vs_duty(path):
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    duties = np.linspace(0.03, 1.0, 55)
    for d_mm, length, color, lw, label in [
        (0.40, 0.60, "#c1272d", 2.6, "drut 0,40 mm / 0,60 m  \u2190 zalecany"),
        (0.40, 0.80, "#1f7a8c", 1.7, "drut 0,40 mm / 0,80 m"),
        (0.50, 0.80, "#e08e0b", 1.7, "drut 0,50 mm / 0,80 m"),
        (0.60, 1.00, "#5b3a99", 1.7, "drut 0,60 mm / 1,00 m"),
    ]:
        ax.plot(duties * 100, [t_steady(d_mm / 1000, length, x) for x in duties],
                color=color, lw=lw, label=label)
    ax.axhspan(*EPS_BAND, color="#2e7d32", alpha=0.10)
    ax.axhspan(*XPS_BAND, color="#1565c0", alpha=0.10)
    ax.axhline(LIMIT, color="#b71c1c", lw=1.0, ls="--")
    ax.text(1.5, EPS_BAND[0] + 8, "EPS / bia\u0142y styropian  200\u2013250 \u00b0C", fontsize=7.5, color="#1b5e20")
    ax.text(1.5, XPS_BAND[0] + 8, "XPS / styrodur  260\u2013300 \u00b0C", fontsize=7.5, color="#0d47a1")
    ax.text(1.5, LIMIT + 7, "powy\u017cej ~320 \u00b0C: palenie pianki, dym, szybkie zu\u017cycie drutu",
            fontsize=7.5, color="#b71c1c")
    ax.set_xlabel("wype\u0142nienie PWM / czas za\u0142\u0105czenia  [%]")
    ax.set_ylabel("temperatura drutu [\u00b0C]")
    ax.set_title("12 V z ATX \u2014 jaka temperatura przy jakim wype\u0142nieniu (drut w bezruchu)", fontsize=9.5)
    ax.set_ylim(0, 520)
    ax.set_xlim(0, 100)
    ax.legend(fontsize=7.3, loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_tmax_vs_d(path):
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ds = np.linspace(0.15, 1.0, 60)
    for length, color in [(0.4, "#1f7a8c"), (0.6, "#2e7d32"), (0.8, "#c1272d"), (1.0, "#5b3a99")]:
        ax.plot(ds, [t_steady(x / 1000, length, 1.0) for x in ds], color=color, lw=1.9,
                label=f"L = {length:.1f} m")
    ax.axhspan(200, 300, color="#2e7d32", alpha=0.10)
    ax.text(0.17, 205, "docelowy zakres pracy 200\u2013300 \u00b0C", fontsize=7.5, color="#1b5e20")
    t_rec = t_steady(D_REC, L_REC, 1.0)
    ax.plot([0.40], [t_rec], "o", ms=8, mfc="none", mec="#c1272d", mew=2)
    ax.annotate(f"zalecany punkt:\n0,40 mm, 0,60 m \u2192 {t_rec:.0f} \u00b0C\n(pe\u0142ne 12 V = zapas mocy)",
                xy=(0.40, t_rec), xytext=(0.47, 320), fontsize=7.3, color="#c1272d",
                arrowprops=dict(arrowstyle="->", color="#c1272d", lw=0.9))
    ax.set_xlabel("\u015brednica drutu nichromowego [mm]")
    ax.set_ylabel("temperatura przy 100 % mocy [\u00b0C]")
    ax.set_title("Ile stopni wyci\u015bnie z drutu ATX 12 V bez regulacji \u2014 tak dobiera si\u0119 \u015brednic\u0119", fontsize=9.5)
    ax.legend(fontsize=7.5)
    ax.set_ylim(0, 700)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_sensitivity(path):
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2))
    duty = duty_for(D_REC, L_REC, 250)
    lens = np.linspace(0.54, 0.66, 40)
    axs[0].plot((lens / L_REC - 1) * 100, [t_steady(D_REC, x, duty) for x in lens],
                color="#c1272d", lw=2.0, label="sta\u0142e wypelnienie (bez p\u0119tli)")
    axs[0].plot((lens / L_REC - 1) * 100, [t_steady(D_REC, x, 1.0) for x in lens],
                color="#8c8c8c", lw=1.6, ls="--", label="pe\u0142ne 12 V (bez p\u0119tli)")
    axs[0].axhline(250, color="#2e7d32", lw=1.0, ls=":")
    axs[0].set_xlabel("rozci\u0105gni\u0119cie drutu [%]")
    axs[0].set_ylabel("temperatura [\u00b0C]")
    axs[0].set_title("Wp\u0142yw d\u0142ugo\u015bci drutu", fontsize=9)
    axs[0].legend(fontsize=6.8)

    facs = [0.4, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5]
    labels = ["bezruch", "", "", "norma", "", "przeci\u0105g", "", "wiatr"]
    axs[1].bar(range(len(facs)), [t_steady(D_REC, L_REC, duty, factor=f) for f in facs],
               color="#90a4ae")
    axs[1].set_xticks(range(len(facs)))
    axs[1].set_xticklabels(labels, fontsize=7)
    axs[1].axhline(250, color="#2e7d32", lw=1.0, ls=":")
    axs[1].set_xlabel("warunki ch\u0142odzenia (ruch powietrza)")
    axs[1].set_ylabel("temperatura [\u00b0C]")
    axs[1].set_title("Wp\u0142yw przeci\u0105gu \u2014 g\u0142\u00f3wny winowajca", fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_u_vs_t(path):
    """Petla liniowa: nastawa napiecia -> temperatura (drut 0,40/0,60)."""
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    us = np.linspace(3.0, 11.5, 70)
    ts = [t_for_voltage(D_REC, L_REC, u) for u in us]
    ax.plot(us, ts, color="#c1272d", lw=2.2)
    ax.axhspan(*EPS_BAND, color="#2e7d32", alpha=0.10)
    ax.axhspan(*XPS_BAND, color="#1565c0", alpha=0.10)
    for tc, color in [(200, "#1b5e20"), (250, "#1b5e20"), (280, "#0d47a1"), (300, "#0d47a1")]:
        u, _ = u_for_temperature(D_REC, L_REC, tc)
        ax.plot([u], [tc], "o", ms=5, color=color)
        ax.annotate(f"{u:.1f} V", xy=(u, tc), xytext=(u + 0.15, tc - 22),
                    fontsize=7.2, color=color)
    ax.set_xlabel("napi\u0119cie na drucie = nastawa (suwak) [V]")
    ax.set_ylabel("temperatura drutu [\u00b0C]")
    ax.set_title("WARIANT B: jedna ga\u0142ka = jedna temperatura (drut 0,40 mm / 0,60 m)", fontsize=9.5)
    ax.set_xlim(3, 11.5)
    ax.set_ylim(0, 420)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def simulate(strategy, d=D_REC, length=L_REC, t_set_c=250.0, t_end=240.0, dt=0.002,
             cut_w=7.0, t_on=150.0, t_off=200.0, stretch=1.0, draft=1.0,
             ki=600.0, kp=0.4):
    """
    strategy:
      'duty'  - stale wypelnienie PWM (regulator mocy, wariant A)
      'power' - stala moc
      'R'     - petla rezystancji (wariant B): mierzy U i I, trzyma R = const
    stretch - rozciagniecie drutu (1.1 = +10 %)
    draft   - mnoznik wspolczynnika chlodzenia (1.6 = przeciag)
    """
    lx = length * stretch
    mass = RHO_S * math.pi * (d / 2) ** 2 * length
    c_th = mass * CP
    t = TA + 2.0
    now = 0.0
    duty0 = duty_for(d, length, t_set_c)
    p_set = q_loss(d, t_set_c + 273, length)
    p_cmd = 0.0
    out = {"t": [], "T": [], "P": [], "R": []}
    r_set = r_hot(d, length, t_set_c + 273)
    while now < t_end:
        r = r_hot(d, lx, t)
        extra = cut_w if t_on <= now < t_off else 0.0
        avail = V0 * V0 / r
        if strategy == "duty":
            p = duty0 * avail
        elif strategy == "power":
            p = min(p_set, avail)
        else:
            err = r_set - r
            p_cmd = min(avail, max(0.0, p_cmd + ki * err * dt + kp * err))
            p = p_cmd
        t += (p - q_loss(d, t, lx, draft) - extra) / c_th * dt
        now += dt
        out["t"].append(now)
        out["T"].append(t - 273.15)
        out["P"].append(p)
        out["R"].append(r)
    return {k: np.array(v) for k, v in out.items()}


def chart_dynamics(path):
    fig, axs = plt.subplots(2, 1, figsize=(6.9, 5.6), sharex=True,
                            gridspec_kw={"height_ratios": [2.3, 1]})
    for mode, color, lw, label in [
        ("duty", "#8c8c8c", 2.0, "sta\u0142e wypelnienie 45 % (wariant A: regulator mocy)"),
        ("power", "#1f7a8c", 1.4, "p\u0119tla mocy: P = 12 W"),
        ("R", "#c1272d", 2.2, "p\u0119tla rezystancji (wariant B: regulator temperatury)"),
    ]:
        sim = simulate(mode)
        axs[0].plot(sim["t"], sim["T"], color=color, lw=lw, label=label)
        axs[1].plot(sim["t"], sim["P"], color=color, lw=1.0)
    axs[0].axhline(250, color="#2e7d32", lw=1.0, ls="--")
    axs[0].text(108, 268, "nastawa 250 \u00b0C", fontsize=7, color="#1b5e20")
    axs[0].axvspan(150, 200, color="#dcdcdc", alpha=0.7)
    axs[0].text(152, 60, "CI\u0118CIE\n(pianka odbiera\n~7 W)", fontsize=7, color="#555")
    axs[0].set_ylabel("temperatura drutu [\u00b0C]")
    axs[0].set_title("Drut 0,40 mm / 0,60 m: co robi 7 W odbierane przez ci\u0119cie", fontsize=9.5)
    axs[0].legend(fontsize=7.2, loc="lower left")
    axs[0].set_ylim(0, 300)
    axs[1].set_ylabel("moc [W]")
    axs[1].set_xlabel("czas [s]")
    axs[1].set_ylim(0, 30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_strategies(path):
    """Porownanie strategii w trzech scenariuszach."""
    scen = [("przeci\u0105g x1,6", dict(draft=1.6, t_on=1e9, t_off=1e9)),
            ("ci\u0119cie: 7 W", dict(cut_w=7.0)),
            ("ci\u0119cie: 12 W", dict(cut_w=12.0))]
    names = {"duty": "sta\u0142e wype\u0142nienie", "power": "sta\u0142a moc",
             "R": "p\u0119tla rezystancji"}
    colors = {"duty": "#9e9e9e", "power": "#1f7a8c", "R": "#c1272d"}
    fig, ax = plt.subplots(figsize=(6.9, 3.7))
    width = 0.26
    for i, (label, kw) in enumerate(scen):
        for j, mode in enumerate(["duty", "power", "R"]):
            sim = simulate(mode, **kw)
            x = i + (j - 1) * width
            val = sim["T"][-400:].min() if kw.get("cut_w") else sim["T"][-400:].mean()
            ax.bar(x, val, width=width * 0.92, color=colors[mode],
                   label=names[mode] if i == 0 else None)
            ax.text(x, val + 6, f"{val:.0f}", ha="center", fontsize=7.2, color="#333")
    ax.axhline(250, color="#2e7d32", lw=1.1, ls="--")
    ax.text(2.42, 256, "cel: 250 \u00b0C", fontsize=7.5, color="#1b5e20", ha="right")
    ax.axhspan(*EPS_BAND, color="#2e7d32", alpha=0.07)
    ax.set_xticks(range(len(scen)))
    ax.set_xticklabels([s[0] for s in scen], fontsize=8)
    ax.set_ylabel("temperatura drutu [\u00b0C]")
    ax.set_ylim(0, 300)
    ax.set_title("Dlaczego regulator mocy to nie regulator temperatury", fontsize=9.5)
    ax.legend(fontsize=7.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_setpoint(path):
    """Wariant B: nastawa (rezystancja) -> temperatura."""
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    rs = np.linspace(5.10, 5.50, 60)
    ts = [(x / (1 + ALPHA * 0)) for x in rs]
    temps = []
    for x in rs:
        # R = R20*(1+alpha*(T-20)) -> T
        t = (x / r_cold(D_REC, L_REC) - 1) / ALPHA + 20
        temps.append(t)
    ax.plot(rs, temps, color="#c1272d", lw=2.2)
    ax.axhspan(*EPS_BAND, color="#2e7d32", alpha=0.10)
    ax.axhspan(*XPS_BAND, color="#1565c0", alpha=0.10)
    for tc in (200, 250, 280):
        r = r_hot(D_REC, L_REC, tc + 273)
        ax.plot([r], [tc], "o", ms=5, color="#333")
        ax.annotate(f"{r:.2f} \u03a9", xy=(r, tc), xytext=(r - 0.19, tc + 12), fontsize=7.2)
    ax.set_xlabel("nastawa: rezystancja drutu [\u03a9]  (jeden potencjometr trymerowy)")
    ax.set_ylabel("temperatura drutu [\u00b0C]")
    ax.set_title("WARIANT B: pokretlo ustawia rezystancj\u0119 \u2192 temperatur\u0119 (drut 0,40/0,60)", fontsize=9)
    ax.set_ylim(0, 420)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_mechanics(path):
    """Szkic mechaniki: rama, sprezyna, drut + detal zacisku 4-przewodowego."""
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 4.6), gridspec_kw={"width_ratios": [1.0, 1.0]})

    # ---------------- lewy: rama
    ax = axs[0]
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Rama: spr\u0119\u017cyna trzyma naci\u0105g", fontsize=9)
    wood = dict(facecolor="#e8dcc8", edgecolor="#8d6e63", lw=1.6)
    ax.add_patch(plt.Rectangle((1.0, 0.5), 8.6, 0.8, **wood))
    ax.add_patch(plt.Rectangle((1.5, 1.3), 0.6, 9.4, **wood))
    ax.add_patch(plt.Rectangle((8.5, 1.3), 0.6, 9.4, **wood))
    ax.add_patch(plt.Rectangle((1.5, 10.1), 7.6, 0.6, **wood))
    ax.add_patch(plt.Rectangle((1.5, 6.4), 7.6, 0.14, color="#cfcfcf"))
    ax.text(5.3, 5.6, "st\u00f3\u0142 / prowadnica", fontsize=6.8, color="#777", ha="center")

    # izolatory + zaciski
    for ytop in (9.5, 2.1):
        ax.add_patch(plt.Rectangle((3.6, ytop - 0.22), 1.1, 0.44, facecolor="#fafafa",
                                   edgecolor="#666", lw=1.1))
    ax.text(3.0, 9.5, "zacisk\nizolowany", fontsize=6.5, ha="right", va="center", color="#444")
    ax.text(3.0, 2.1, "zacisk\nizolowany", fontsize=6.5, ha="right", va="center", color="#444")

    # sprezyna (od gornego zacisku w gore do poprzeczki)
    yy = np.linspace(10.1, 9.72, 33)
    ax.plot(4.15 + 0.3 * np.sin((yy - 9.72) / 0.12), yy, color="#888", lw=1.7)
    ax.annotate("spr\u0119\u017cyna\n2\u20134 N", xy=(4.6, 9.9), xytext=(5.6, 10.4),
                fontsize=6.8, color="#444",
                arrowprops=dict(arrowstyle="->", lw=0.7, color="#888"))

    # drut
    ax.plot([4.15, 4.15], [9.28, 2.32], color="#c1272d", lw=2.6)
    ax.annotate("drut nichrom 0,40 mm / 0,60 m", xy=(4.15, 7.4), xytext=(5.1, 8.3),
                fontsize=7, color="#c1272d",
                arrowprops=dict(arrowstyle="->", lw=0.8, color="#c1272d"))
    ax.annotate("kierunek ci\u0119cia\n(pianka przesuwa si\u0119 w prawo)", xy=(4.15, 4.6), xytext=(5.1, 4.0),
                fontsize=6.8, color="#555",
                arrowprops=dict(arrowstyle="->", lw=0.8, color="#555"))
    ax.annotate("", xy=(6.6, 4.6), xytext=(5.3, 4.6),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#555"))

    # grube przewody w dol do zasilacza
    ax.plot([4.7, 7.6], [10.2, 10.2], color="#1a1a1a", lw=2.4)
    ax.plot([7.6, 7.6], [10.2, 0.9], color="#1a1a1a", lw=2.4)
    ax.plot([4.7, 7.6], [1.9, 1.9], color="#1a1a1a", lw=2.4)
    ax.text(7.75, 5.5, "grube przewody\ndo zasilacza", fontsize=6.5, color="#222", va="center")
    ax.text(1.0, 0.05, "rama sztywna \u2014 drut ma trzyma\u0107 lini\u0119 prost\u0105", fontsize=6.5, color="#666")

    # ---------------- prawy: zacisk 4-przewodowy
    ax = axs[1]
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Jeden zacisk, cztery przewody", fontsize=9)

    ax.plot([2.6, 2.6], [0.8, 5.0], color="#c1272d", lw=3.0)
    ax.text(2.3, 0.45, "drut nichromowy", fontsize=6.8, color="#c1272d", ha="center")
    ax.add_patch(plt.Rectangle((1.9, 5.0), 1.4, 1.5, facecolor="#f2f2f2", edgecolor="#555", lw=1.4))
    ax.text(2.6, 5.75, "\u015bruba", fontsize=6.5, ha="center", va="center", color="#555")
    ax.plot([2.6, 2.6], [6.5, 11.0], color="#c1272d", lw=3.0)

    # 2 grube (zasilanie) i 2 cienkie (pomiar) - wszystkie w jednym punkcie
    for dy, color, lw, txt, ty in [(0.5, "#1a1a1a", 2.6, "zasilanie  (~2 A)", 9.4),
                                    (-0.5, "#1565c0", 1.1, "pomiar napi\u0119cia", 7.9)]:
        ax.plot([3.3, 8.0], [5.75 + dy, 5.75 + dy], color=color, lw=lw)
        ax.plot([3.3, 3.3], [5.75 + dy, 5.75], color=color, lw=lw)
        ax.text(8.15, 5.75 + dy, txt, fontsize=6.8, va="center", color=color)
    ax.text(3.3, 7.4, "gruby i cienki przew\u00f3d\nspotykaj\u0105 si\u0119 dopiero\nna \u015brubie", fontsize=6.4,
            color="#333", ha="center", va="bottom")
    ax.text(0.2, 3.3,
            "Dzi\u0119ki temu spadek napi\u0119cia na grubych\n"
            "przewodach i na stykach nie psuje pomiaru \u2014\n"
            "mierzone jest tylko napi\u0119cie na samym drucie.\n"
            "Bez tego b\u0142\u0105d si\u0119ga kilkudziesi\u0119ciu kelwin\u00f3w\n"
            "i zale\u017cy od tego, jak mocno dokr\u0119cona jest \u015bruba.",
            fontsize=6.5, color="#444", va="center", ha="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ------------------------------------------------------------------ raport
def print_report():
    d, length = D_REC, L_REC
    print("=" * 74)
    print("1) DOBOR DRUTU DO 12 V (kryterium: przy 100 % mocy ok. 400 C)")
    print("=" * 74)
    print(f"{'L[m]':>5} {'d[mm]':>6} {'R20[ohm]':>9} {'I_zim[А]':>9} {'I_max[A]':>9}"
          f" {'P_max[W]':>9} {'T(100%)':>8} {'U@250C':>7}")
    for L in (0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        best = None
        for i in range(40):
            dmm = 0.15 + 0.02 * i
            t100 = t_steady(dmm / 1000, L, 1.0)
            if best is None or abs(t100 - 400) < abs(best[1] - 400):
                best = (dmm, t100)
        dmm, t100 = best
        u250, _ = u_for_temperature(dmm / 1000, L, 250)
        print(f"{L:5.1f} {dmm:6.2f} {r_cold(dmm / 1000, L):9.2f} {12 / r_cold(dmm / 1000, L):9.2f}"
              f" {12 / r_hot(dmm / 1000, L, t100 + 273):9.2f} {144 / r_hot(dmm / 1000, L, t100 + 273):9.1f}"
              f" {t100:8.0f} {u250:7.2f}")

    print()
    print("=" * 74)
    print("2) ZALECANY DRUT 0,40 mm / 0,60 m - punkty pracy")
    print("=" * 74)
    print(f"  R zimny = {r_cold(d, length):.2f} ohm,  prad zimny = {12 / r_cold(d, length):.2f} A")
    t100 = t_steady(d, length, 1.0)
    print(f"  przy 100 % wypelnienia: {t100:.0f} C, {144 / r_hot(d, length, t100 + 273):.1f} W")
    print(f"  {'T[C]':>6} {'wypeln.':>8} {'P[W]':>6} {'I[A]':>6} {'U_drut[V]':>10} {'R[ohm]':>7}")
    for tc in (150, 200, 250, 280, 300):
        duty, p, i = operating_point(d, length, tc)
        u, _ = u_for_temperature(d, length, tc)
        r = r_hot(d, length, tc + 273)
        print(f"  {tc:6.0f} {duty * 100:7.0f}% {p:6.1f} {i:6.2f} {u:10.2f} {r:7.2f}")
    mass = RHO_S * math.pi * (d / 2) ** 2 * length
    print(f"  masa drutu {mass * 1e3:.2f} g, C_th = {mass * CP:.2f} J/K")

    print()
    print("=" * 74)
    print("3) JAK STRATEGIA REGULACJI RADZI SOBIE Z ZAKLOCENIAMI")
    print("=" * 74)
    scenarios = [
        ("przeciag x1.6", dict(draft=1.6, t_on=1e9, t_off=1e9)),
        ("przeciag x2.5", dict(draft=2.5, t_on=1e9, t_off=1e9)),
        ("ciecie 7 W", dict(cut_w=7.0)),
        ("ciecie 12 W", dict(cut_w=12.0)),
    ]
    print(f"  {'scenariusz':22} {'stale wypeln.':>14} {'stala moc':>11} {'petla R':>10}")
    for lab, kw in scenarios:
        cells = []
        for mode in ("duty", "power", "R"):
            sim = simulate(mode, **kw)
            val = sim["T"][-400:].min() if kw.get("cut_w") else sim["T"][-400:].mean()
            cells.append(f"{val:6.1f} C")
        print(f"  {lab:22} {cells[0]:>14} {cells[1]:>11} {cells[2]:>10}")
    print("  (cel 250 C; 'petla R' mierzy U i I drutu, wiec utrzymuje jego rezystancje,")
    print("   a rezystancja jest bezposrednia miara temperatury)")
    print()
    print("  Rozciaganie drutu: petla R utrzymuje rezystancje CALEGO obwodu (drut + zaciski),")
    print("  wiec po kazdej zmianie geometrii trzeba ja raz przekalibrowac pokretlem.")
    print("  Stały blad (np. 10 mOhm stykow) to ~13 C - zjada go kalibracja; dryf w czasie")
    print("  to pojedyncze mOhm, czyli kilka kelwinow.")

    print()
    print("=" * 74)
    print("4) ROZCIAGANIE DRUTU (sprężyna, naprężenie 5-10 N)")
    print("=" * 74)
    for dmm in (0.30, 0.40, 0.50, 0.60):
        dd = dmm / 1000
        m_per_m = RHO_S * math.pi * (dd / 2) ** 2
        dl = 0.6 * 14e-6 * 230
        print(f"  d={dmm:.2f} mm: {m_per_m * 1000:.2f} g/m, wydluzenie 0,60 m przy +230 K = {dl * 1000:.2f} mm")
        for tn in (5, 10):
            sag = m_per_m * 0.6 * 9.81 * 0.6 ** 2 / (8 * tn) * 1000
            print(f"      naprezenie {tn:2d} N -> strzalka zwisu {sag:.2f} mm")
    duty250 = duty_for(d, length, 250)
    print(f"  bez petli: +10 % dlugosci (0,60->0,66 m) przy stalym wypelnieniu "
          f"{duty250 * 100:.0f}%: {t_steady(d, 0.66, duty250):.0f} C zamiast 250 C")
    print(f"            +10 % dlugosci przy pelnym 12 V: {t_steady(d, 0.66, 1.0):.0f} C zamiast {t100:.0f} C")

    print()
    print("=" * 74)
    print("5) WARUNEK LINIOWY (wariant B): straty MOSFET-u i radiator")
    print("=" * 74)
    for tc in (150, 200, 250, 300):
        u, p = u_for_temperature(d, length, tc)
        i = u / r_hot(d, length, tc + 273)
        print(f"  T={tc:3d} C: U_drut={u:4.2f} V, I={i:4.2f} A -> Uds={12 - u:5.2f} V, "
              f"P_mos={(12 - u) * i:4.1f} W")
    pm = (12 - u_for_temperature(d, length, 250)[0]) * 250 and (12 - u_for_temperature(d, length, 250)[0])
    print("  radiator: dla 6 W i 150 C zlacza wystarczy byle zeberko 5-10 K/W")
    print("  (IRF3205: R_th(j-c) ~1 K/W, obudowa TO-220)")

    print()
    print("=" * 74)
    print("6) DYNAMIKA I NASTAWY PETLI REZYSTANCJI (wariant B)")
    print("=" * 74)
    print("  Warunek rownowagi: U_drut = R_nastawy * I  (+ male napiecie startu)")
    print(f"  {'R nastawy':>10} {'temperatura':>12} {'prad':>7} {'moc':>7}")
    for x in (5.20, 5.26, 5.30, 5.335, 5.37, 5.41, 5.45):
        t = (x / r_cold(d, length) - 1) / ALPHA + 20
        p = q_loss(d, t + 273, length)
        i = math.sqrt(p / x)
        print(f"  {x:10.3f} {t:11.0f} C {i:6.2f} A {p:6.1f} W")
    print()
    print("  Uwaga praktyczna: rezystancja drutu zmienia sie tylko o ~0,05 oma na kazde")
    print("  30 C, wiec petla musi miec wzmocnienie ~100-200 i potencjometr do kalibracji.")
    print()
    print("  Termostat dwustanowy (dla porownania) - teTOnie vs histereza i opoznienie czujnika:")
    print(f"  {'histereza':>10} {'tau czujnika':>13} {'teTOnie':>9} {'T srednia':>10}")

    def bang(hyst, tau, t_set=523.15, tend=200, dt=0.002):
        dd, ll = D_REC, L_REC
        mass = RHO_S * math.pi * (dd / 2) ** 2 * ll
        c_th = mass * CP
        t, ts, tn, on = TA, TA, 0.0, True
        rec = []
        while tn < tend:
            r = r_hot(dd, ll, t)
            if ts > t_set + hyst / 2:
                on = False
            elif ts < t_set - hyst / 2:
                on = True
            p = (V0 * V0 / r) if on else 0.0
            t += (p - q_loss(dd, t, ll)) / c_th * dt
            ts += (t - ts) * dt / tau
            tn += dt
            rec.append(t - 273.15)
        a = np.array(rec[int(150 / dt):])
        return a.mean(), a.max() - a.min()

    for hyst in (2, 5, 10):
        for tau in (0.1, 0.4, 1.0):
            mean, ptp = bang(hyst, tau)
            print(f"  {hyst:10.0f} {tau:13.1f} {ptp:9.1f} {mean:10.1f}")

    print()
    print("=" * 74)
    print("7) MOC POTRZEBNA DO SAMEgo CIECIA (szacunek: rho=15 kg/m3, 700 kJ/kg)")
    print("=" * 74)
    for v in (0.03, 0.05, 0.08):
        for kerf in (0.2e-3, 0.4e-3):
            for th in (0.05, 0.10):
                print(f"  v={v * 100:4.1f} cm/s, szczelina {kerf * 1000:.1f} mm, grubosc {th * 100:.0f} cm"
                      f" -> {15.0 * v * kerf * th * 700e3:5.1f} W")


if __name__ == "__main__":
    print_report()
    chart_t_vs_duty(os.path.join(OUT, "t_vs_duty.png"))
    chart_tmax_vs_d(os.path.join(OUT, "tmax_vs_d.png"))
    chart_sensitivity(os.path.join(OUT, "wrazliwosc.png"))
    chart_dynamics(os.path.join(OUT, "dynamika.png"))
    chart_strategies(os.path.join(OUT, "strategie.png"))
    chart_setpoint(os.path.join(OUT, "nastawa_vs_temperatura.png"))
    chart_mechanics(os.path.join(OUT, "mechanika.png"))
    print("\nWykresy w docs/charts/")
