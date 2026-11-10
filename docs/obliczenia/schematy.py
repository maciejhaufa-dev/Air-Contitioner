#!/usr/bin/env python3
"""
Schematy ukladu regulacji temperatury drutu cieplnego (czysty analog).
Uruchomienie: python3 docs/obliczenia/schematy.py   (wymaga schemdraw)

schemat_A.png - wariant "najprostszy": PWM 0-100 % + MOSFET, reguluje moc
schemat_B.png - wariant "docelowy": petla liniowa, U(drut) = U(nastawa)
"""
import os

import schemdraw
from schemdraw import elements as elm

OUT = os.path.join(os.path.dirname(__file__), "..", "charts")
os.makedirs(OUT, exist_ok=True)

RED = "#c1272d"
BLUE = "#1565c0"
GREEN = "#2e7d32"
GREY = "#4d4d4d"


def _supply(d, x_end, label="+12 V z ATX"):
    """Szyna +12 V z bezpiecznikiem PTC"""
    d.add(elm.Vdd().at((0, 0)).label(label, loc="left", ofst=(0.1, 0)))
    d.add(elm.Line().at((0, 0)).to((0.9, 0)).color(GREY))
    d.add(elm.Fuse().at((0.9, 0)).to((2.5, 0)).label("PTC 3 A", loc="top", ofst=(0, 0.12)))
    d.add(elm.Line().at((2.5, 0)).to((x_end, 0)).color(GREY))


def schemat_a(path):
    """Wariant A: regulator mocy. PWM z NE555 -> bramka MOSFET-u."""
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=2.0, fontsize=10, lw=1.6)
        _supply(d, 6.4)

        d.add(elm.Resistor().at((6.4, 0)).down(3.2).color(RED)
              .label("DRUT\n0,40 mm / 0,60 m\n\u2248 14 \u03a9", loc="right", ofst=(0.4, 0)))
        d.add(elm.Line().at((6.4, -3.2)).down(1.4).color(GREY))
        q = d.add(elm.NFet2().at((6.4, -4.6))
                  .label("IRF3205", loc="bottom", ofst=(0, 0.55)))
        d.add(elm.Line().at(q.source).down(0.9).color(GREY))
        d.add(elm.Ground().at((6.4, -5.5)).label("GND", loc="bottom", ofst=(0, 0.1)))

        # PWM -> bramka
        gate_l=(q.gate.x-3.2, q.gate.y)
        d.add(elm.Resistor().at(gate_l).to(q.gate).color(BLUE)
              .label("100 \u03a9", loc="top", ofst=(0, 0.12)))
        d.add(elm.Dot().at((q.gate.x-0.9, q.gate.y)))
        d.add(elm.Resistor().at((q.gate.x-0.9, q.gate.y)).down(1.6).color(BLUE)
              .label("10 k\u03a9", loc="right", ofst=(0.4, 0)))
        d.add(elm.Ground().at((q.gate.x-0.9, q.gate.y-1.6)))
        d.add(elm.Label().at((q.gate.x-3.25, q.gate.y)).label("PWM 0\u2013100 %\n(z NE555 lub\nz potencjometru)", loc="left").color(BLUE))
        d.save(path)


def schemat_b(path):
    """Wariant B: petla liniowa. U(drut) = U(nastawa) -> temperatura stala."""
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=2.2, fontsize=10, lw=1.6)
        _supply(d, 1.6)

        # rezystor pomiarowy 0,1 oma w plusie
        d.add(elm.Resistor().at((1.6, 0)).to((3.2, 0)).color(GREY)
              .label("R_pom\n0,1 \u03a9", loc="top", ofst=(0, 0.15)))
        d.add(elm.Dot().at((3.2, 0)))
        d.add(elm.Line().at((3.2, 0)).to((7.6, 0)).color(GREY))
        d.add(elm.Label().at((3.35, -0.35)).label("+", loc="right").color(BLUE))

        # drut
        d.add(elm.Resistor().at((7.6, 0)).down(3.0).color(RED)
              .label("DRUT nichrom\n0,40 mm / 0,60 m\n\u2248 14 \u03a9", loc="right", ofst=(0.45, 0)))
        d.add(elm.Dot().at((7.6, -3.0)))
        d.add(elm.Line().at((7.6, -3.0)).down(1.2).color(GREY))

        # MOSFET
        q = d.add(elm.NFet2().at((7.6, -4.2)).label("IRF3205\n(klucz liniowy)", loc="bottom", ofst=(0, 0.5)))
        d.add(elm.Line().at(q.source).down(0.9).color(GREY))
        d.add(elm.Ground().at((7.6, -5.1)).label("GND", loc="bottom", ofst=(0, 0.1)))

        # wzmacniacz bledu
        op = d.add(elm.Opamp().at((2.4, -5.2)).label("1/2 LM358", loc="bottom", ofst=(0.9, 1.35)))
        # in1 (-) = napiecie z drutu, in2 (+) = nastawa
        d.add(elm.Line().at((7.6, -3.0)).to((1.6, -3.0)).color(RED))
        d.add(elm.Line().at((1.6, -3.0)).to((1.6, -4.58)).color(RED))
        d.add(elm.Line().at((1.6, -4.58)).to(op.in1).color(RED))
        d.add(elm.Label().at((1.75, -3.5)).label("pomiar\nnapi\u0119cia\nna drucie", loc="right").color(RED))

        # nastawa -> in2
        d.add(elm.Line().at(op.in2).to((1.6, -5.83)).color(GREEN))
        d.add(elm.Line().at((1.6, -5.83)).down(1.4).color(GREEN))
        d.add(elm.Potentiometer().at((1.6, -7.23)).down(1.2).color(GREEN)
              .label("10 k\u03a9\nNASTAWA", loc="left", ofst=(0.4, 0)))
        d.add(elm.Ground().at((1.6, -8.43)).label("", loc="bottom"))

        # wyjscie -> bramka
        gate_l=(q.gate.x-1.4, q.gate.y)
        d.add(elm.Resistor().at(op.out).to(gate_l).color(BLUE)
              .label("220 \u03a9", loc="top", ofst=(0, 0.12)))
        d.add(elm.Dot().at(gate_l))
        d.add(elm.Resistor().at(gate_l).down(1.3).color(BLUE)
              .label("10 k\u03a9", loc="left", ofst=(0.4, 0)))
        d.add(elm.Ground().at((gate_l[0], gate_l[1]-1.3)))
        d.add(elm.Line().at(gate_l).to(q.gate).color(BLUE))
        d.save(path)


if __name__ == "__main__":
    for fn, name in [(schemat_a, "schemat_A.png"), (schemat_b, "schemat_B.png")]:
        fn(os.path.join(OUT, name))
        print("ok", name)
