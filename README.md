# Air-Contitioner

Projekt analogowego układu regulacji temperatury drutu oporowego do cięcia
styropianu (EPS) i styroduru (XPS). Zasilanie: zasilacz ATX 12 V.

- **[Opis projektu i schematy → docs/regulacja-drutu-cieplnego.md](docs/regulacja-drutu-cieplnego.md)**
- Obliczenia i symulacje: `docs/obliczenia/` (`model_drutu.py`, `rysunki.py`)
- Wykresy i schematy: `docs/charts/`

Najkrótsza wersja: drut nichromowy 0,40 mm / 0,60 m, pętla rezystancyjna
(LM358 + MOSFET), która trzyma opór drutu na stałym poziomie — czyli stałą
temperaturę 200–300 °C, niezależnie od przeciągu i rozciągania drutu.
