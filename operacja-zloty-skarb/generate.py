#!/usr/bin/env python3
"""Generator planszetek i scenariusza „Operacja Złoty Skarb”.

Wszystkie ilustracje są rysowane jako wektory w ReportLab — bez zewnętrznych
obrazów i czcionek innych niż DejaVu Sans zainstalowanej w systemie.
"""
from __future__ import annotations

import math
from pathlib import Path

import fitz  # PyMuPDF — tylko do łączenia PDF i podglądów
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "wydruk"
PREVIEW = ROOT / "podglad"
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_BOLD, italic=FONT, boldItalic=FONT_BOLD)

# Paleta przyjazna drukowi: dużo bieli, kolory głównie w nagłówkach i ikonach.
INK = HexColor("#243241")
MUTED = HexColor("#5D6A76")
LINE = HexColor("#CDD6DE")
PAPER = HexColor("#FFFFFF")
SOFT = HexColor("#F4F7F9")
YELLOW = HexColor("#FFC845")
PALE_YELLOW = HexColor("#FFF7DA")
GREEN = HexColor("#23856D")
POLICE = HexColor("#1769AA")
POLICE_DARK = HexColor("#123E67")
POLICE_SOFT = HexColor("#EAF4FC")
CROOK = HexColor("#8C3B46")
CROOK_DARK = HexColor("#532D3B")
CROOK_SOFT = HexColor("#FCEEF0")
ORANGE = HexColor("#E98A2E")

PAGE_W, PAGE_H = A4
BOARD_W, BOARD_H = landscape(A4)
HALF = BOARD_W / 2


def style(size=9, leading=None, color=INK, align=TA_LEFT, font=FONT):
    return ParagraphStyle(
        name=f"s-{size}-{leading}-{align}-{font}",
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.35,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
        allowWidows=0,
        allowOrphans=0,
    )


def para(c, text, x, top, width, size=9, leading=None, color=INK,
         align=TA_LEFT, font=FONT, max_height=None):
    """Rysuje akapit od górnej krawędzi i zwraca jego wysokość."""
    current = size
    while True:
        current_leading = leading * current / size if leading else None
        p = Paragraph(text, style(current, current_leading, color, align, font))
        _, height = p.wrap(width, 2000)
        if max_height is None or height <= max_height or current <= 6.2:
            p.drawOn(c, x, top - height)
            return height
        current -= 0.25


def rr(c, x, y, w, h, radius=8, fill=PAPER, stroke=LINE, sw=0.8):
    c.setLineWidth(sw)
    if stroke is not None:
        c.setStrokeColor(stroke)
    if fill is not None:
        c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, fill=1 if fill is not None else 0,
                stroke=1 if stroke is not None else 0)


def label(c, text, x, y, size=9, color=INK, font=FONT, align="left"):
    c.setFillColor(color)
    c.setFont(font, size)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)


def star_points(cx, cy, r, inner=0.45, rotation=math.pi / 2):
    pts = []
    for i in range(10):
        angle = rotation + i * math.pi / 5
        radius = r if i % 2 == 0 else r * inner
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts


def polygon(c, pts, fill=None, stroke=INK, sw=0.8):
    path = c.beginPath()
    path.moveTo(*pts[0])
    for point in pts[1:]:
        path.lineTo(*point)
    path.close()
    c.setFillColor(fill or PAPER)
    c.setStrokeColor(stroke or INK)
    c.setLineWidth(sw)
    c.drawPath(path, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def draw_star(c, cx, cy, r=8, fill=None, stroke=YELLOW, sw=1.1):
    polygon(c, star_points(cx, cy, r), fill=fill, stroke=stroke, sw=sw)


def draw_check(c, cx, cy, r=6, color=GREEN):
    c.setStrokeColor(color)
    c.setLineWidth(1.8)
    c.setLineCap(1)
    c.line(cx - r * .55, cy, cx - r * .1, cy - r * .45)
    c.line(cx - r * .1, cy - r * .45, cx + r * .65, cy + r * .55)


def draw_brick(c, x, y, w=24, h=12, color=YELLOW, studs=2):
    c.setFillColor(color)
    c.setStrokeColor(INK)
    c.setLineWidth(.65)
    c.roundRect(x, y, w, h, 2, fill=1, stroke=1)
    for i in range(studs):
        sx = x + (i + .5) * w / studs
        c.setFillColor(color)
        c.circle(sx, y + h + 1.5, min(3, w / (studs * 3)), fill=1, stroke=1)
        c.setStrokeColor(white)
        c.setLineWidth(.5)
        c.line(sx - 1.2, y + h + 2.5, sx + 1.2, y + h + 2.5)
        c.setStrokeColor(INK)
        c.setLineWidth(.65)


def draw_badge(c, cx, cy, s=1, color=POLICE):
    pts = [(cx, cy + 26*s), (cx + 21*s, cy + 18*s), (cx + 17*s, cy - 7*s),
           (cx, cy - 24*s), (cx - 17*s, cy - 7*s), (cx - 21*s, cy + 18*s)]
    polygon(c, pts, fill=color, stroke=color, sw=1)
    draw_star(c, cx, cy + 2*s, 10*s, fill=YELLOW, stroke=YELLOW)
    c.setStrokeColor(white)
    c.setLineWidth(1.1*s)
    c.arc(cx - 12*s, cy - 15*s, cx + 12*s, cy + 15*s, 205, 130)


def draw_mask(c, cx, cy, s=1, color=CROOK):
    # Czapka
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.roundRect(cx - 20*s, cy + 13*s, 40*s, 12*s, 5*s, fill=1, stroke=0)
    c.roundRect(cx - 24*s, cy + 10*s, 48*s, 6*s, 3*s, fill=1, stroke=0)
    # Twarz i opaska
    c.setFillColor(HexColor("#F2C9A5"))
    c.circle(cx, cy - 1*s, 19*s, fill=1, stroke=0)
    c.setFillColor(INK)
    c.roundRect(cx - 20*s, cy - 4*s, 40*s, 12*s, 4*s, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx - 8*s, cy + 2*s, 3.2*s, fill=1, stroke=0)
    c.circle(cx + 8*s, cy + 2*s, 3.2*s, fill=1, stroke=0)
    c.setFillColor(INK)
    c.circle(cx - 7*s, cy + 2*s, 1.2*s, fill=1, stroke=0)
    c.circle(cx + 9*s, cy + 2*s, 1.2*s, fill=1, stroke=0)
    c.setStrokeColor(CROOK_DARK)
    c.setLineWidth(1.3*s)
    c.arc(cx - 6*s, cy - 15*s, cx + 6*s, cy - 6*s, 200, 140)


def draw_car(c, x, y, s=1, color=POLICE, crook=False):
    c.setStrokeColor(INK)
    c.setLineWidth(.8*s)
    c.setFillColor(color)
    c.roundRect(x, y + 6*s, 60*s, 17*s, 4*s, fill=1, stroke=1)
    c.setFillColor(color)
    path = c.beginPath()
    path.moveTo(x + 12*s, y + 23*s)
    path.lineTo(x + 21*s, y + 34*s)
    path.lineTo(x + 43*s, y + 34*s)
    path.lineTo(x + 52*s, y + 23*s)
    path.close()
    c.drawPath(path, fill=1, stroke=1)
    c.setFillColor(POLICE_SOFT if not crook else CROOK_SOFT)
    c.rect(x + 23*s, y + 25*s, 9*s, 7*s, fill=1, stroke=0)
    c.rect(x + 34*s, y + 25*s, 9*s, 7*s, fill=1, stroke=0)
    c.setFillColor(INK)
    c.circle(x + 14*s, y + 7*s, 6*s, fill=1, stroke=0)
    c.circle(x + 47*s, y + 7*s, 6*s, fill=1, stroke=0)
    c.setFillColor(LINE)
    c.circle(x + 14*s, y + 7*s, 2.5*s, fill=1, stroke=0)
    c.circle(x + 47*s, y + 7*s, 2.5*s, fill=1, stroke=0)
    if crook:
        draw_brick(c, x + 5*s, y + 23*s, 12*s, 7*s, YELLOW, 1)
    else:
        c.setFillColor(HexColor("#E34F4F"))
        c.rect(x + 26*s, y + 35*s, 7*s, 4*s, fill=1, stroke=0)
        c.setFillColor(POLICE)
        c.rect(x + 33*s, y + 35*s, 7*s, 4*s, fill=1, stroke=0)


def draw_helicopter(c, x, y, s=1, color=POLICE):
    c.setStrokeColor(INK)
    c.setLineWidth(1*s)
    c.setFillColor(color)
    c.ellipse(x, y, x + 43*s, y + 24*s, fill=1, stroke=1)
    c.setFillColor(POLICE_SOFT)
    c.ellipse(x + 5*s, y + 8*s, x + 18*s, y + 20*s, fill=1, stroke=0)
    c.setStrokeColor(INK)
    c.setLineWidth(3*s)
    c.line(x + 38*s, y + 14*s, x + 62*s, y + 21*s)
    c.setLineWidth(1*s)
    c.line(x + 59*s, y + 13*s, x + 59*s, y + 29*s)
    c.line(x + 53*s, y + 21*s, x + 65*s, y + 21*s)
    c.line(x + 19*s, y + 24*s, x + 19*s, y + 31*s)
    c.setLineWidth(2*s)
    c.line(x - 4*s, y + 31*s, x + 43*s, y + 31*s)
    c.setLineWidth(1.2*s)
    c.line(x + 9*s, y, x + 5*s, y - 6*s)
    c.line(x + 34*s, y, x + 38*s, y - 6*s)
    c.line(x, y - 6*s, x + 43*s, y - 6*s)


def draw_boat(c, x, y, s=1, color=POLICE):
    c.setStrokeColor(INK)
    c.setLineWidth(.8*s)
    c.setFillColor(color)
    path = c.beginPath()
    path.moveTo(x, y + 12*s)
    path.lineTo(x + 58*s, y + 12*s)
    path.lineTo(x + 47*s, y)
    path.lineTo(x + 12*s, y)
    path.close()
    c.drawPath(path, fill=1, stroke=1)
    c.setFillColor(POLICE_SOFT)
    c.rect(x + 20*s, y + 13*s, 20*s, 14*s, fill=1, stroke=1)
    c.setFillColor(YELLOW)
    c.rect(x + 27*s, y + 28*s, 6*s, 4*s, fill=1, stroke=0)
    c.setStrokeColor(POLICE)
    c.setLineWidth(1.2*s)
    for off in (0, 8):
        c.arc(x + off*s, y - 7*s, x + (off + 24)*s, y + 3*s, 200, 140)


def draw_house(c, x, y, s=1, color=POLICE, crook=False):
    c.setFillColor(SOFT if not crook else CROOK_SOFT)
    c.setStrokeColor(INK)
    c.setLineWidth(.8*s)
    c.rect(x, y, 48*s, 45*s, fill=1, stroke=1)
    polygon(c, [(x - 4*s, y + 45*s), (x + 24*s, y + 62*s),
                (x + 52*s, y + 45*s)], fill=color, stroke=INK, sw=.8*s)
    c.setFillColor(INK)
    c.rect(x + 18*s, y, 13*s, 24*s, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.circle(x + 27*s, y + 12*s, 1.3*s, fill=1, stroke=0)
    if crook:
        draw_brick(c, x + 5*s, y + 27*s, 13*s, 8*s, YELLOW, 1)
    else:
        draw_star(c, x + 24*s, y + 37*s, 6*s, fill=YELLOW, stroke=YELLOW, sw=.5)


def draw_bomb(c, cx, cy, s=1):
    c.setFillColor(INK)
    c.setStrokeColor(INK)
    c.circle(cx, cy, 12*s, fill=1, stroke=0)
    c.setLineWidth(2*s)
    c.line(cx + 6*s, cy + 10*s, cx + 12*s, cy + 18*s)
    c.setStrokeColor(ORANGE)
    c.line(cx + 12*s, cy + 18*s, cx + 17*s, cy + 21*s)
    draw_star(c, cx + 19*s, cy + 23*s, 5*s, fill=YELLOW, stroke=ORANGE, sw=.7)
    label(c, "BUM", cx, cy - 3*s, 5.5*s, white, FONT_BOLD, "center")


def draw_person(c, cx, cy, s=1, color=POLICE, animal=False):
    c.setStrokeColor(INK)
    c.setLineWidth(.8*s)
    if animal:
        c.setFillColor(HexColor("#B9814E"))
        c.roundRect(cx - 12*s, cy, 24*s, 12*s, 4*s, fill=1, stroke=1)
        c.circle(cx + 12*s, cy + 13*s, 7*s, fill=1, stroke=1)
        polygon(c, [(cx + 7*s, cy + 18*s), (cx + 7*s, cy + 27*s),
                    (cx + 13*s, cy + 20*s)], fill=HexColor("#B9814E"), stroke=INK, sw=.6)
        c.setLineWidth(2*s)
        c.line(cx - 8*s, cy, cx - 8*s, cy - 7*s)
        c.line(cx + 7*s, cy, cx + 7*s, cy - 7*s)
        c.line(cx - 12*s, cy + 9*s, cx - 19*s, cy + 16*s)
    else:
        c.setFillColor(HexColor("#F2C9A5"))
        c.circle(cx, cy + 28*s, 7*s, fill=1, stroke=1)
        c.setFillColor(color)
        c.roundRect(cx - 8*s, cy + 7*s, 16*s, 17*s, 3*s, fill=1, stroke=1)
        c.setLineWidth(2.4*s)
        c.line(cx - 4*s, cy + 7*s, cx - 5*s, cy - 5*s)
        c.line(cx + 4*s, cy + 7*s, cx + 5*s, cy - 5*s)
        c.line(cx - 7*s, cy + 20*s, cx - 14*s, cy + 10*s)
        c.line(cx + 7*s, cy + 20*s, cx + 14*s, cy + 10*s)


FACTIONS = {
    "policja": {
        "name": "POLICJANCI",
        "short": "POLICJA",
        "color": POLICE,
        "dark": POLICE_DARK,
        "soft": POLICE_SOFT,
        "motto": "Trop • Pościg • Aresztowanie",
        "start": ["Posterunek z celą", "Radiowóz dla 2 figurek", "Szef, tajniak i pies"],
        "roles": ["Szef", "Tajniak", "Pies"],
        "acts": [
            {
                "title": "AKT I • EKIPA GOTOWA",
                "tasks": [
                    "<b>1. Baza:</b> posterunek z celą i miejscem na radiowóz. Wpuść figurkę.",
                    "<b>2. Radiowóz:</b> przewieź 2 figurki wokół 2 przeszkód bez strat.",
                    "<b>3. Trop:</b> tajniak i pies odnajdują klocek ukryty przez Szefa Miasta.",
                ],
                "bonus": "Nazwij szefa, tajniaka i psa.",
            },
            {
                "title": "AKT II • NAPAD I POŚCIG",
                "tasks": [
                    "<b>4. Alarm:</b> po „BUM!” przyjedź do banku, zanim Szef doliczy do 8.",
                    "<b>5. Pościg:</b> dotknij wozu oprychów przed jego metą.",
                    "<b>6. Pojazd specjalny:</b> łódź ALBO helikopter przewozi policjanta.",
                ],
                "bonus": "Pojazd specjalny ma ruchomy element.",
            },
            {
                "title": "AKT III • WYSPA WIĘZIENNA",
                "tasks": [
                    "<b>7. Więzienie:</b> przygotuj na wyspie celę z zamykanymi drzwiami.",
                    "<b>8. Obława:</b> znajdź min. 2 z 3 Złotych Kostek w 60 sekund.",
                    "<b>9. Finał:</b> zatrzymaj szefa oprychów i zamknij go w celi.",
                ],
                "bonus": "W finale użyj ruchomego elementu konstrukcji.",
            },
        ],
    },
    "oprychy": {
        "name": "OPRYCHY",
        "short": "OPRYCHY",
        "color": CROOK,
        "dark": CROOK_DARK,
        "soft": CROOK_SOFT,
        "motto": "Kryjówka • Napad • Ucieczka",
        "start": ["Baza z tajnym wyjściem", "Wóz z miejscem na łup", "Szef, ekspert i obserwator"],
        "roles": ["Szef", "Ekspert od bomb", "Obserwator"],
        "acts": [
            {
                "title": "AKT I • EKIPA GOTOWA",
                "tasks": [
                    "<b>1. Baza:</b> kryjówka z miejscem na skarb i tajnym wyjściem.",
                    "<b>2. Wóz do napadu:</b> przewieź kierowcę i skrzynię wokół 2 przeszkód.",
                    "<b>3. Próbne BUM:</b> zbuduj bombę i mur; po „BUM!” zdejmij 3 klocki.",
                ],
                "bonus": "Nazwij szefa, eksperta i obserwatora.",
            },
            {
                "title": "AKT II • NAPAD I POŚCIG",
                "tasks": [
                    "<b>4. Napad:</b> otwórz mur i włóż min. 1 Złotą Kostkę do wozu.",
                    "<b>5. Ucieczka:</b> przekrocz metę z łupem, zanim policja dotknie wozu.",
                    "<b>6. Pojazd specjalny:</b> łódź ALBO helikopter przewozi szefa i łup.",
                ],
                "bonus": "Pojazd specjalny ma ruchomy element.",
            },
            {
                "title": "AKT III • WYSPA WIĘZIENNA",
                "tasks": [
                    "<b>7. Kryjówka:</b> przygotuj na wyspie ukrycie skarbu i tajne wyjście.",
                    "<b>8. Zmyłka:</b> ukryj 3 Kostki; zdobądź ★, jeśli min. 1 zostanie ukryta.",
                    "<b>9. Finał:</b> szef dociera z min. 1 Kostką do bazy przed aresztowaniem.",
                ],
                "bonus": "W finale użyj ruchomego elementu konstrukcji.",
            },
        ],
    },
}


def draw_panel_header(c, x, top, w, data, faction, right=False):
    color = data["color"]
    c.setFillColor(color)
    c.roundRect(x, top - 54, w, 54, 10, fill=1, stroke=0)
    # Drobne klocki w tle.
    if faction == "policja":
        draw_badge(c, x + 30, top - 28, .63, white)
    else:
        draw_mask(c, x + 30, top - 27, .62, CROOK_DARK)
    if right:
        label(c, "KARTA FRAKCJI", x + 61, top - 24, 16, white, FONT_BOLD)
        label(c, data["motto"], x + 61, top - 41, 7.8, white)
    else:
        label(c, data["name"], x + 61, top - 25, 17, white, FONT_BOLD)
        label(c, "OPERACJA ZŁOTY SKARB", x + 61, top - 41, 7.8, YELLOW, FONT_BOLD)


def draw_act_card(c, x, top, w, act, data):
    header_h, row_h, bonus_h = 23, 31, 22
    h = header_h + row_h * 3 + bonus_h + 6
    rr(c, x, top - h, w, h, 8, PAPER, LINE, .75)
    c.setFillColor(data["soft"])
    c.roundRect(x, top - header_h, w, header_h, 8, fill=1, stroke=0)
    c.rect(x, top - header_h, w, 8, fill=1, stroke=0)
    label(c, act["title"], x + 10, top - 16, 9.2, data["dark"], FONT_BOLD)
    y_top = top - header_h
    for idx, task in enumerate(act["tasks"]):
        if idx:
            c.setStrokeColor(LINE)
            c.setLineWidth(.45)
            c.line(x + 29, y_top - idx * row_h, x + w - 8, y_top - idx * row_h)
        cy = y_top - idx * row_h - row_h / 2
        draw_star(c, x + 14, cy, 7, fill=None, stroke=data["color"], sw=1)
        para(c, task, x + 28, y_top - idx * row_h - 5, w - 37,
             size=8.0, leading=9.8, color=INK, max_height=25)
    bonus_top = top - header_h - row_h * 3
    c.setFillColor(PALE_YELLOW)
    c.roundRect(x + 4, top - h + 4, w - 8, bonus_h, 5, fill=1, stroke=0)
    draw_star(c, x + 15, top - h + 4 + bonus_h / 2, 6.2, fill=YELLOW, stroke=ORANGE, sw=.7)
    para(c, "<b>PREMIA +1★:</b> " + act["bonus"], x + 27,
         top - h + 4 + bonus_h - 5, w - 36, size=7.2, leading=8.8,
         color=INK, max_height=16)
    return top - h


def draw_scene(c, x, y, w, h, data, faction):
    rr(c, x, y, w, h, 8, data["soft"], None, 0)
    label(c, "BAZA • EKIPA • MASZYNY", x + 10, y + h - 15, 7.2, data["dark"], FONT_BOLD)
    if faction == "policja":
        draw_house(c, x + 16, y + 13, .75, POLICE)
        draw_car(c, x + 82, y + 15, .85, POLICE)
        draw_person(c, x + 156, y + 16, .62, POLICE)
        draw_person(c, x + 180, y + 18, .58, POLICE, animal=True)
        draw_helicopter(c, x + 220, y + 40, .72, POLICE)
        draw_boat(c, x + 295, y + 17, .72, POLICE)
    else:
        draw_house(c, x + 16, y + 13, .75, CROOK, crook=True)
        draw_car(c, x + 82, y + 15, .85, CROOK, crook=True)
        draw_person(c, x + 158, y + 16, .62, CROOK)
        draw_bomb(c, x + 194, y + 25, .65)
        draw_helicopter(c, x + 220, y + 40, .72, CROOK)
        draw_boat(c, x + 295, y + 17, .72, CROOK)


def section_title(c, text, x, y, color):
    c.setFillColor(color)
    c.roundRect(x, y - 2, 4, 14, 2, fill=1, stroke=0)
    label(c, text, x + 10, y, 9, color, FONT_BOLD)


def draw_right_panel(c, x, top, w, data, faction):
    draw_panel_header(c, x, top, w, data, faction, right=True)
    scene_y = top - 54 - 8 - 88
    draw_scene(c, x, scene_y, w, 88, data, faction)

    y = scene_y - 16
    section_title(c, "PRZYGOTUJ W AKCIE I — ZAZNACZ", x, y, data["color"])
    y -= 18
    for item in data["start"]:
        c.setStrokeColor(data["color"])
        c.setLineWidth(.8)
        c.rect(x + 2, y - 1, 8, 8, fill=0, stroke=1)
        label(c, item, x + 17, y, 7.8, INK)
        y -= 15

    y -= 5
    section_title(c, "TWOJA EKIPA — NADAJ IMIONA", x, y, data["color"])
    y -= 18
    for role in data["roles"]:
        label(c, role, x + 2, y, 7.3, MUTED, FONT_BOLD)
        c.setStrokeColor(LINE)
        c.setLineWidth(.7)
        c.line(x + 102, y - 2, x + w - 3, y - 2)
        y -= 17

    y -= 3
    section_title(c, "RYTM KAŻDEJ RUNDY", x, y, data["color"])
    y -= 20
    steps = [("1", "POSŁUCHAJ"), ("2", "ZBUDUJ"), ("3", "ODEGRAJ"), ("4", "ZAMALUJ ★")]
    cell_w = (w - 6) / 4
    for i, (num, txt) in enumerate(steps):
        sx = x + i * cell_w
        c.setFillColor(data["soft"])
        c.circle(sx + 9, y + 4, 8, fill=1, stroke=0)
        label(c, num, sx + 9, y + 1, 7.5, data["dark"], FONT_BOLD, "center")
        label(c, txt, sx + 20, y + 1, 6.4, data["dark"], FONT_BOLD)
        if i < 3:
            label(c, "›", sx + cell_w - 3, y, 12, LINE, FONT_BOLD)

    y -= 26
    section_title(c, "WYNIK — 3 ZADANIA + PREMIA W KAŻDYM AKCIE", x, y, data["color"])
    y -= 23
    for act in range(3):
        label(c, f"AKT {['I', 'II', 'III'][act]}", x + 2, y + 1, 7.4, MUTED, FONT_BOLD)
        for j in range(4):
            draw_star(c, x + 75 + j * 42, y + 4, 11, fill=None,
                      stroke=YELLOW if j == 3 else data["color"], sw=1.25)
        label(c, "premia" if False else "", x, y)
        y -= 30
    rr(c, x, y - 3, w, 27, 6, PALE_YELLOW, None, 0)
    draw_star(c, x + 14, y + 10, 6, fill=YELLOW, stroke=ORANGE, sw=.6)
    para(c, "<b>1 wykonane zadanie = 1 gwiazdka.</b> Bez kupowania i punktów ujemnych. Możesz zdobyć maksymalnie 12★.",
         x + 26, y + 19, w - 32, size=7.1, leading=8.7, max_height=20)


def draw_board(c, faction):
    data = FACTIONS[faction]
    c.setPageSize((BOARD_W, BOARD_H))
    c.setFillColor(PAPER)
    c.rect(0, 0, BOARD_W, BOARD_H, fill=1, stroke=0)
    margin = 18
    panel_w = HALF - 2 * margin
    top = BOARD_H - margin

    # Lewa planszetka A5: misje.
    x = margin
    draw_panel_header(c, x, top, panel_w, data, faction)
    y = top - 62
    for act in data["acts"]:
        y = draw_act_card(c, x, y, panel_w, act, data) - 7
    label(c, "Zamaluj ★ dopiero po wykonaniu zadania. Zasady pojedynków są w scenariuszu.",
          x + 2, 23, 6.5, MUTED)

    # Prawa planszetka A5: ekipa, grafika i wynik.
    x2 = HALF + margin
    draw_right_panel(c, x2, top, panel_w, data, faction)

    # Linia cięcia 2 × A5.
    c.saveState()
    c.setStrokeColor(HexColor("#8B98A5"))
    c.setLineWidth(.7)
    c.setDash(3, 3)
    c.line(HALF, 12, HALF, BOARD_H - 12)
    c.restoreState()
    rr(c, HALF - 28, BOARD_H - 12, 56, 10, 3, PAPER, None, 0)
    label(c, "LINIA CIĘCIA • 2 × A5", HALF, BOARD_H - 9, 5.5, MUTED, FONT, "center")
    c.showPage()


def make_boards():
    path = OUT / "01_Planszetki_A4_2xA5.pdf"
    c = canvas.Canvas(str(path), pagesize=(BOARD_W, BOARD_H), pageCompression=1)
    c.setTitle("Operacja Złoty Skarb — planszetki Policjanci i Oprychy")
    c.setAuthor("Gotowy scenariusz gry klockowej dla dzieci")
    draw_board(c, "policja")
    draw_board(c, "oprychy")
    c.save()
    return path


# ---------- Scenariusz ----------

def footer(c, page, text="OPERACJA ZŁOTY SKARB"):
    c.setStrokeColor(LINE)
    c.setLineWidth(.6)
    c.line(38, 29, PAGE_W - 38, 29)
    label(c, text, 38, 17, 6.6, MUTED, FONT_BOLD)
    label(c, str(page), PAGE_W - 38, 17, 7, MUTED, FONT_BOLD, "right")


def story_box(c, top, text, color=POLICE, height=54):
    x, w = 42, PAGE_W - 84
    rr(c, x, top - height, w, height, 9, SOFT, None, 0)
    c.setFillColor(YELLOW)
    c.roundRect(x, top - height, 6, height, 3, fill=1, stroke=0)
    para(c, text, x + 16, top - 10, w - 30, size=9, leading=12.5,
         color=INK, max_height=height - 16)
    return top - height


def act_header(c, act, title, subtitle, page, color):
    c.setFillColor(color)
    c.rect(0, PAGE_H - 91, PAGE_W, 91, fill=1, stroke=0)
    # Dekoracyjne klocki.
    for i in range(5):
        c.setStrokeColor(white)
        c.setLineWidth(.4)
        c.rect(PAGE_W - 132 + i * 20, PAGE_H - 27 - (i % 2) * 9, 16, 10,
               fill=0, stroke=1)
    label(c, act, 42, PAGE_H - 34, 9, YELLOW, FONT_BOLD)
    label(c, title, 42, PAGE_H - 60, 23, white, FONT_BOLD)
    label(c, subtitle, 42, PAGE_H - 78, 8.2, white)
    footer(c, page)


def mission_card(c, top, number, title, police_text, crook_text, play_text,
                 height=133, tag="OBIE FRAKCJE MOGĄ ZDOBYĆ ★"):
    x, w = 42, PAGE_W - 84
    rr(c, x, top - height, w, height, 9, PAPER, LINE, .75)
    c.setFillColor(INK)
    c.circle(x + 22, top - 22, 12, fill=1, stroke=0)
    label(c, str(number), x + 22, top - 26, 10, white, FONT_BOLD, "center")
    label(c, title, x + 42, top - 22, 12.2, INK, FONT_BOLD)
    label(c, tag, x + w - 10, top - 21, 6.4, MUTED, FONT_BOLD, "right")
    c.setStrokeColor(LINE)
    c.setLineWidth(.5)
    c.line(x + 12, top - 40, x + w - 12, top - 40)

    gap = 14
    col_w = (w - 28 - gap) / 2
    left_x = x + 14
    right_x = left_x + col_w + gap
    label(c, "POLICJANCI", left_x, top - 55, 7.2, POLICE, FONT_BOLD)
    label(c, "OPRYCHY", right_x, top - 55, 7.2, CROOK, FONT_BOLD)
    text_space = height - 100  # Zostaw 2 pt odstępu nad paskiem „Jak gramy”.
    para(c, police_text, left_x, top - 62, col_w, size=8.1, leading=10.5,
         max_height=text_space)
    para(c, crook_text, right_x, top - 62, col_w, size=8.1, leading=10.5,
         max_height=text_space)
    c.setFillColor(SOFT)
    c.roundRect(x + 10, top - height + 8, w - 20, 28, 5, fill=1, stroke=0)
    para(c, "<b>Jak gramy:</b> " + play_text, x + 18, top - height + 31,
         w - 36, size=7.5, leading=9.3, max_height=22)
    return top - height


def bonus_box(c, top, text, height=42):
    x, w = 42, PAGE_W - 84
    rr(c, x, top - height, w, height, 8, PALE_YELLOW, None, 0)
    draw_star(c, x + 20, top - height / 2, 10, fill=YELLOW, stroke=ORANGE, sw=.8)
    para(c, "<b>PREMIA AKTU • +1★ DLA KAŻDEJ FRAKCJI</b><br/>" + text,
         x + 40, top - 8, w - 52, size=8, leading=10.5, max_height=height - 12)
    return top - height


def make_cover(c):
    c.setPageSize(A4)
    c.setFillColor(POLICE_DARK)
    c.rect(0, PAGE_H - 160, PAGE_W, 160, fill=1, stroke=0)
    c.setFillColor(CROOK_DARK)
    path = c.beginPath()
    path.moveTo(PAGE_W * .67, PAGE_H)
    path.lineTo(PAGE_W, PAGE_H)
    path.lineTo(PAGE_W, PAGE_H - 160)
    path.lineTo(PAGE_W * .56, PAGE_H - 160)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    draw_badge(c, 70, PAGE_H - 73, .85, POLICE)
    draw_mask(c, PAGE_W - 66, PAGE_H - 72, .8, CROOK)
    label(c, "LEGO • KAMPANIA DLA 2 GRACZY", PAGE_W / 2, PAGE_H - 34,
          8, YELLOW, FONT_BOLD, "center")
    label(c, "OPERACJA", PAGE_W / 2, PAGE_H - 67, 20, white, FONT_BOLD, "center")
    label(c, "ZŁOTY SKARB", PAGE_W / 2, PAGE_H - 99, 28, white, FONT_BOLD, "center")
    label(c, "POLICJANCI vs OPRYCHY", PAGE_W / 2, PAGE_H - 124,
          10, white, FONT_BOLD, "center")
    label(c, "3 akty • 9 zadań dla każdej frakcji • od 6 lat", PAGE_W / 2,
          PAGE_H - 145, 7.8, white, FONT, "center")

    top = PAGE_H - 178
    top = story_box(c, top,
        "Oprychy chcą ukraść z banku <b>trzy Złote Kostki</b>. Szykują wóz do napadu i kryjówkę na Wyspie Więziennej. Policjanci ruszają po tropie z psem, tajniakiem i pojazdami specjalnymi. Po trzech aktach wygrywa frakcja z większą liczbą gwiazdek.",
        height=63) - 14

    # Najważniejsza mechanika — duży, czytelny pasek.
    x, w = 42, PAGE_W - 84
    box_h = 67
    rr(c, x, top - box_h, w, box_h, 10, PALE_YELLOW, None, 0)
    cells = [("1 ZADANIE", "= 1★"), ("1 PREMIA W AKCIE", "= 1★"), ("RAZEM", "MAKS. 12★")]
    cw = w / 3
    for i, (a, b) in enumerate(cells):
        label(c, a, x + i * cw + cw / 2, top - 23, 7.4, MUTED, FONT_BOLD, "center")
        label(c, b, x + i * cw + cw / 2, top - 48, 15, INK, FONT_BOLD, "center")
        if i < 2:
            c.setStrokeColor(YELLOW)
            c.line(x + (i + 1) * cw, top - 13, x + (i + 1) * cw, top - box_h + 13)
    top -= box_h + 15

    # Dwie kolumny przygotowania.
    col_gap = 14
    col_w = (w - col_gap) / 2
    prep_h = 117
    rr(c, x, top - prep_h, col_w, prep_h, 9, SOFT, None, 0)
    rr(c, x + col_w + col_gap, top - prep_h, col_w, prep_h, 9, SOFT, None, 0)
    section_title(c, "PRZYGOTUJ", x + 12, top - 20, POLICE)
    para(c,
         "• 3 żółte lub złote klocki = Złote Kostki<br/>"
         "• niebieski ręcznik = woda<br/>"
         "• 2 książki lub kubki = przeszkody<br/>"
         "• kredki do zamalowywania gwiazdek<br/>"
         "• własne klocki, figurki i gotowe zestawy",
         x + 12, top - 34, col_w - 24, size=8.1, leading=13, max_height=75)
    section_title(c, "SZEF MIASTA = DOROSŁY", x + col_w + col_gap + 12,
                  top - 20, CROOK)
    para(c,
         "Czyta fabułę, ukrywa trop, pilnuje zasad i przyznaje ★.<br/><br/>"
         "<b>Nie ocenia ładności ani wielkości budowli.</b> Liczy się tylko warunek zadania i użycie konstrukcji w zabawie.",
         x + col_w + col_gap + 12, top - 34, col_w - 24, size=8.1,
         leading=11.2, max_height=76)
    top -= prep_h + 16

    section_title(c, "JAK WYGLĄDA KAŻDA RUNDA?", x, top, INK)
    top -= 22
    steps = [("1", "POSŁUCHAJ", "Szef czyta krótki wstęp."),
             ("2", "ZBUDUJ", "Zwykle 5–10 minut."),
             ("3", "ODEGRAJ", "Pokaż konstrukcję w akcji."),
             ("4", "ZAMALUJ ★", "Sprawdź swój własny cel.")]
    step_w = w / 4
    for i, (num, head, body) in enumerate(steps):
        sx = x + i * step_w
        c.setFillColor(POLICE_SOFT if i % 2 == 0 else CROOK_SOFT)
        c.circle(sx + 13, top - 2, 11, fill=1, stroke=0)
        label(c, num, sx + 13, top - 6, 10, INK, FONT_BOLD, "center")
        label(c, head, sx + 30, top - 5, 7.2, INK, FONT_BOLD)
        para(c, body, sx + 2, top - 24, step_w - 8, size=7.1, leading=9.2,
             color=MUTED, max_height=28)
    top -= 63

    rr(c, x, top - 66, w, 66, 9, PAPER, LINE, .7)
    para(c,
         "<b>Pojedynki:</b> przy pościgu i finale ★ dostaje zwycięzca; remis = ★ dla obojga. W pozostałych rundach każdy zdobywa ★ za własny cel.<br/>"
         "<b>Bez presji:</b> minutnik służy tylko do zakończenia budowania, nigdy do przyznawania punktów. Można grać jeden akt dziennie.",
         x + 12, top - 10, w - 24, size=7.9, leading=11, max_height=49)
    top -= 78

    rr(c, x, top - 52, w, 52, 9, CROOK_SOFT, None, 0)
    draw_bomb(c, x + 24, top - 27, .62)
    para(c,
         "<b>Bezpieczne „BUM!”:</b> bomba jest tylko konstrukcją z klocków. Po krzyku „BUM!” zdejmujemy ręką 3 klocki z próbnego muru. Nie rzucamy klockami, nie celujemy w ludzi i nie niszczymy cudzych baz.",
         x + 48, top - 9, w - 60, size=7.6, leading=10.2, max_height=38)
    top -= 62
    rr(c, x, top - 38, w, 38, 8, POLICE_SOFT, None, 0)
    para(c,
         "<b>Dla 6-latka:</b> czytaj tylko jedno zadanie naraz i w razie potrzeby pokaż je na klockach. Pomoc dorosłego ani brata nie odbiera gwiazdki.",
         x + 12, top - 9, w - 24, size=7.7, leading=10.2, max_height=25)
    footer(c, 1, "OPERACJA ZŁOTY SKARB • ZASADY I PRZYGOTOWANIE")
    c.showPage()


def make_act_one(c):
    act_header(c, "AKT I / 3", "EKIPA GOTOWA", "Bazy • pojazdy • specjaliści", 2, POLICE_DARK)
    top = PAGE_H - 108
    top = story_box(c, top,
        "<b>Szef Miasta:</b> „Zanim ruszymy po Złote Kostki, każda ekipa musi przygotować bazę, pojazd i specjalistów. Nie ma kupowania — używacie tego, co macie, i własnych pomysłów!”",
        height=48) - 10
    top = mission_card(c, top, 1, "Bazy gotowe",
        "Zbuduj lub przebuduj posterunek. Ma mieć <b>celę</b> i <b>miejsce na radiowóz</b>. Minifigurka musi wejść do środka.",
        "Zbuduj kryjówkę z <b>miejscem na skarb</b> i <b>tajnym wyjściem</b>. Minifigurka musi móc z niego uciec.",
        "Budujcie równocześnie przez 5–10 minut. Potem każdy przez 30 sekund pokazuje oba wymagane miejsca. Za pokazanie ich zamaluj ★.",
        height=132) - 9
    top = mission_card(c, top, 2, "Próba pojazdów",
        "Radiowóz zabiera <b>2 minifigurki</b>. Żadna nie może wypaść podczas jazdy.",
        "Wóz do napadu zabiera <b>kierowcę i skrzynię na łupy</b>. Skrzynia nie może wypaść.",
        "Ustawcie 2 książki lub kubki. Każdy pojazd jedzie wokół nich i wraca do bazy. Nie liczy się czas ani kolejność — tylko dotarcie bez utraty ładunku.",
        height=132) - 9
    top = mission_card(c, top, 3, "Specjaliści w akcji",
        "Wybierz szefa, tajniaka i psa. <b>Tajniak z psem</b> odnajduje klocek-trop. Wolno użyć jednej podpowiedzi Szefa Miasta.",
        "Wybierz szefa, eksperta od bomb i obserwatora. Ekspert buduje <b>bombę</b> i mur z 6 klocków.",
        "Policja: Szef Miasta ukrywa zwykły klocek w uzgodnionej strefie. Oprychy: po „BUM!” ekspert zdejmuje ręką dokładnie 3 klocki muru. Wykonanie własnej próby = ★.",
        height=137) - 10
    top = bonus_box(c, top,
        "Nazwij swoich trzech specjalistów i wpisz ich imiona (dorosły może pisać). Wpis na karcie frakcji = dodatkowa ★.") - 10
    para(c, "<b>Koniec aktu:</b> Pies wywąchuje trop prowadzący do banku. Obserwator oprychów już tam czeka z planem muru…",
         42, top, PAGE_W - 84, size=8, leading=10.5, color=MUTED, max_height=28)
    c.showPage()


def make_act_two(c):
    act_header(c, "AKT II / 3", "NAPAD I POŚCIG", "Alarm • złoty łup • łódź albo helikopter", 3, CROOK_DARK)
    top = PAGE_H - 108
    top = story_box(c, top,
        "<b>Szef Miasta:</b> „Za mną trzy Złote Kostki i jeden mur banku. Gdy rozlegnie się BUM, nie będzie już odwrotu. Policjo, szykuj radiowóz. Oprychy, szykujcie ładunek!”",
        height=48) - 10
    top = mission_card(c, top, 4, "Alarm w banku",
        "Po „BUM!” przyjedź radiowozem z posterunku do banku <b>zanim Szef Miasta doliczy do 8</b>.",
        "Po „BUM!” zdejmij 3 klocki muru. Weź <b>min. 1 Złotą Kostkę</b> i umieść ją w swoim wozie.",
        "Ustaw 3 żółte klocki za murem. Policja rusza spoza banku i objeżdża 1 przeszkodę. W tej rundzie nie przeszkadzacie sobie — każdy może zdobyć własną ★.",
        height=132) - 9
    top = mission_card(c, top, 5, "Wielki pościg",
        "★, jeśli <b>dotkniesz wozu oprychów przed metą</b>. Nie wolno taranować ani chwytać ręki przeciwnika.",
        "★, jeśli <b>przekroczysz metę z łupem</b>, zanim policja dotknie twojego wozu. Jedno dotknięcie przed metą kończy ucieczkę.",
        "Prosty tor, wspólny start i meta, najwyżej 2 przeszkody. Na „START” oboje prowadzicie auta jedną ręką. Jedna próba. Równoczesny wynik = ★ dla obojga.",
        height=136, tag="POJEDYNEK O 1★") - 9
    top = mission_card(c, top, 6, "Łódź albo helikopter",
        "Zbuduj <b>łódź policyjną ALBO helikopter</b>. Przewieź policjanta przez ręcznik-morze albo nad 2 książkami.",
        "Zbuduj <b>łódź ALBO helikopter do ucieczki</b>. Przewieź szefa i łup przez morze albo nad 2 książkami.",
        "Nie potrzebujecie gotowego zestawu. Pojazd ma zmieścić wymagany ładunek i dotrzeć na koniec trasy. Pokaz w akcji = ★. Jeśli oprychy nie mają łupu, używają skrzyni.",
        height=137) - 10
    top = bonus_box(c, top,
        "Twój nowy pojazd specjalny ma działający ruchomy element: śmigło, ster, drzwi, hak albo skrzydło. Pokaż, jak działa = dodatkowa ★.") - 10
    para(c, "<b>Koniec aktu:</b> Śmigło zauważa światła na Wyspie Więziennej. To tam oprychy chcą schować Złote Kostki!",
         42, top, PAGE_W - 84, size=8, leading=10.5, color=MUTED, max_height=28)
    c.showPage()


def make_act_three(c):
    act_header(c, "AKT III / 3", "WYSPA WIĘZIENNA", "Kryjówki • obława • wielki finał", 4, POLICE_DARK)
    top = PAGE_H - 106
    top = story_box(c, top,
        "<b>Przygotowanie:</b> Niebieski ręcznik to morze, a wyspa to gotowy zestaw albo własna budowla. Postawcie bazy po przeciwnych stronach. Na wyspie połóżcie 3 Złote Kostki — bez względu na wynik wcześniejszych pościgów.",
        height=49) - 9
    top = mission_card(c, top, 7, "Bazy na wyspie",
        "Przygotuj <b>celę z zamykanymi drzwiami</b>. Możesz użyć gotowego więzienia i tylko je przebudować.",
        "Przygotuj <b>ukrycie skarbu i tajne wyjście</b>. Obserwator pokazuje drogę ucieczki szefa.",
        "Macie 5–10 minut. Nie trzeba budować od zera. Pokażcie oba wymagane elementy i przechodnicie przez nie minifigurką. Własny pokaz = ★.",
        height=135) - 8
    top = mission_card(c, top, 8, "Obława i zmyłka",
        "Tajniak i pies mają <b>60 sekund</b>. ★ za odnalezienie co najmniej <b>2 z 3 Kostek</b>.",
        "Obserwator ukrywa 3 Kostki. ★, jeśli po 60 sekundach <b>co najmniej 1 nadal będzie ukryta</b>.",
        "Policja odwraca się. Kostki mogą być tylko na uzgodnionej wyspie i muszą być choć trochę widoczne — bez demontażu. Przy 2 znalezionych obie frakcje dostają ★!",
        height=133, tag="WSPÓLNA PRÓBA • OBA CELE SĄ MOŻLIWE") - 8
    top = mission_card(c, top, 9, "Wielki finał",
        "★, jeśli <b>szef oprychów trafi do celi</b>. Aresztowanie: policjant dotyka szefa, a potem odprowadzasz go do celi.",
        "★, jeśli <b>szef z min. 1 Kostką dotrze do własnej bazy</b> przed aresztowaniem. Może użyć pojazdu specjalnego.",
        "Szef oprychów startuje na wyspie, policja przy swojej bazie. Na „START” prowadzicie tylko własne figurki/pojazdy. Bez łapania rąk i taranowania. Jednoczesny sukces = ★ dla obojga.",
        height=139, tag="FINAŁOWY POJEDYNEK") - 9
    top = bonus_box(c, top,
        "W finale użyj ruchomego elementu własnej konstrukcji: drzwi celi, tajnego wyjścia, haka, bramy albo bomby. Pokaz działania = dodatkowa ★.",
        height=40) - 9

    # Wynik i dogrywka — zwarte, ale kompletne zakończenie.
    x, w = 42, PAGE_W - 84
    rr(c, x, top - 66, w, 66, 8, SOFT, None, 0)
    para(c,
         "<b>WYNIK:</b> Policja i Oprychy liczą swoje gwiazdki (maks. 12). Więcej ★ = wygrana kampanii. "
         "Przy remisie zagrajcie w <b>„Maszt ratunkowy”</b>: w 60 sekund każdy buduje najwyższą wieżę-antenę, która stoi samodzielnie przez 5 sekund. Wyższa wygrywa.<br/>"
         "<b>Zakończenie:</b> wygrana policji = skarb wraca do muzeum; wygrana oprychów = szef ucieka, a policja znajduje trop do kolejnej kampanii.",
         x + 12, top - 9, w - 24, size=7.6, leading=10.1, max_height=52)
    c.showPage()


def make_rules():
    path = OUT / "02_Scenariusz_i_mechanika.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("Operacja Złoty Skarb — scenariusz i mechanika")
    c.setAuthor("Gotowy scenariusz gry klockowej dla dzieci")
    make_cover(c)
    make_act_one(c)
    make_act_two(c)
    make_act_three(c)
    c.save()
    return path


def combine_and_preview(boards, rules):
    full = OUT / "Operacja_Zloty_Skarb_pelny_zestaw.pdf"
    doc = fitz.open()
    # Najpierw zasady, potem dwie planszetki do druku.
    for path in (rules, boards):
        src = fitz.open(path)
        doc.insert_pdf(src)
        src.close()
    doc.set_metadata({
        "title": "Operacja Złoty Skarb — pełny zestaw do druku",
        "author": "Scenariusz i grafiki wektorowe",
        "subject": "Policjanci vs Oprychy — 3 akty, 9 zadań, proste gwiazdki",
    })
    doc.save(full, garbage=4, deflate=True)
    doc.close()

    # Podglądy PNG do szybkiego obejrzenia i kontroli jakości.
    src = fitz.open(boards)
    for i, name in enumerate(("policjanci", "oprychy")):
        pix = src[i].get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        pix.save(PREVIEW / f"planszetka_{name}.png")
    src.close()
    src = fitz.open(rules)
    pix = src[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    pix.save(PREVIEW / "zasady_strona_1.png")
    src.close()
    return full


def main():
    boards = make_boards()
    rules = make_rules()
    full = combine_and_preview(boards, rules)
    print("Utworzono:")
    for path in (boards, rules, full):
        print(f"  {path.relative_to(ROOT)} ({path.stat().st_size:,} B)")


if __name__ == "__main__":
    main()
