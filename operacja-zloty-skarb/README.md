# Operacja Złoty Skarb

Gotowa do druku kampania klockowa **Policjanci vs Oprychy** dla dwójki dzieci od ok. 6 lat. Powstała z myślą o prostszym systemie niż kupowanie jednostek za punkty.

## Pliki do wydruku

- **`wydruk/Operacja_Zloty_Skarb_pelny_zestaw.pdf`** — cały zestaw: 4 strony zasad i scenariusza oraz 2 strony planszetek.
- **`wydruk/01_Planszetki_A4_2xA5.pdf`** — same planszetki; jedna strona A4 dla każdej frakcji.
- **`wydruk/02_Scenariusz_i_mechanika.pdf`** — instrukcja dla Szefa Miasta i pełny przebieg wszystkich aktów.

### Jak drukować planszetki

1. Wybierz **A4, orientację poziomą, skalę 100% / rozmiar rzeczywisty**.
2. Wydrukuj dwie strony, najlepiej jednostronnie.
3. Przetnij każdą stronę na przerywanej linii. Powstaną **cztery karty A5**: karta misji i karta frakcji dla Policjantów oraz dla Oprychów.
4. Nie używaj opcji „dopasuj do A5” na drukarce — arkusz już zawiera właściwy podział 2 × A5.

Instrukcję można wydrukować na A4 w pionie, dwustronnie, albo czytać z ekranu. Kolor jest zalecany, ale wszystkie pola i symbole mają też kontury widoczne w skali szarości.

## Mechanika w skrócie

- **1 wykonane zadanie = 1 gwiazdka.**
- W każdym akcie jest **jedna premia = 1 dodatkowa gwiazdka**.
- Każda frakcja ma **3 akty × 3 zadania**, czyli 9 zadań i 3 premie; maksymalny wynik to **12★**.
- Nie ma kasy, kupowania jednostek, punktów ujemnych ani oceniania ładności budowli.
- W większości zadań każdy może zdobyć gwiazdkę za własny cel. Pościg i finał są bezpośrednimi pojedynkami.
- Runda ma zawsze ten sam rytm: **posłuchaj → zbuduj → odegraj → zamaluj ★**.

## Fabuła i akty

Oprychy chcą ukraść trzy Złote Kostki i przewieźć je na Wyspę Więzienną. Policjanci próbują ich zatrzymać.

1. **Ekipa gotowa:** bazy, radiowóz i wóz do napadu, tajniak z psem oraz ekspert od bomb.
2. **Napad i pościg:** alarm w banku, bezpieczne „BUM!”, ucieczka z łupem i budowa łodzi albo helikoptera.
3. **Wyspa Więzienna:** kryjówki, poszukiwanie skarbu i finałowe aresztowanie albo ucieczka szefa.

Całość można rozegrać w ok. 60–90 minut albo podzielić na trzy osobne spotkania.

## Przygotuj

- 3 żółte lub złote klocki jako Złote Kostki,
- niebieski ręcznik jako morze,
- 2 książki albo kubki jako przeszkody,
- własne klocki, minifigurki i gotowe zestawy,
- kredki do zamalowywania gwiazdek.

Dorosły pełni rolę **Szefa Miasta**: czyta jedno zadanie naraz, ukrywa trop, pilnuje bezpiecznej zabawy i przyznaje gwiazdki. Pomoc dziecku nie odbiera punktu.

## Podgląd i źródło

Folder `podglad/` zawiera obrazy PNG planszetek i instrukcji. Grafiki są wektorowe i zostały narysowane bezpośrednio w generatorze, więc w PDF są ostre przy każdym rozmiarze wydruku.

Aby ponownie wygenerować pliki w środowisku z Pythonem i czcionką DejaVu Sans:

```bash
python -m pip install -r requirements.txt
python generate.py
```
