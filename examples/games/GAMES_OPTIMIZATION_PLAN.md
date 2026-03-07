# Plan optymalizacji gier

## Cel

Celem jest poprawa plynnosci, ograniczenie zuzycia CPU/RAM oraz lepsze dopasowanie backendu renderingu (`FRAMEBUFFER`, `DISPLAY_LIST` lub hybryda) do charakteru kazdej gry.

## Zasady ogolne

- `FRAMEBUFFER` preferowac tam, gdzie duza czesc ekranu zmienia sie w kazdej klatce.
- `DISPLAY_LIST` preferowac tam, gdzie scena jest retained, kafelkowa albo zmienia tylko niewielka liczbe obiektow.
- `copy=True` utrzymywac dla retained workloads.
- `copy=False` utrzymywac dla full-redraw animation workloads.
- `gc.collect()` nie wykonywac w rytmie renderu; tylko przy zmianie stanu, ladowaniu zasobow lub ekranach przejsciowych.
- HUD i tekst odswiezac tylko przy rzeczywistej zmianie wartosci.
- Unikac `math.sin()`, formatowania stringow i kosztownych lookupow w hot path.

## Priorytety

1. `game_frogger.py`
2. `game_galaxian.py`
3. `game_sokoban.py`
4. `game_pacman.py`
5. `game_minesweeper.py`
6. `game_flappy_bird.py`
7. `game_snake.py`
8. `game_robbo.py` / `robbo/`

## Rekomendowany backend

| Gra | Aktualny charakter | Rekomendacja | Uzasadnienie |
| --- | --- | --- | --- |
| `game_frogger.py` | full redraw + duzy background blit | `FRAMEBUFFER` teraz, docelowo hybryda lub `DISPLAY_LIST` po refaktorze | obecnie zbyt duza czesc sceny jest rysowana od nowa |
| `game_galaxian.py` | szybka animacja, duzo malych zmian | `FRAMEBUFFER` | `DISPLAY_LIST` dla calej sceny prawdopodobnie nie da zysku |
| `game_sokoban.py` | gra kafelkowa, zmiany lokalne | `DISPLAY_LIST` albo retained `FRAMEBUFFER` | bardzo dobry kandydat do dirty-tiles |
| `game_pacman.py` | retained z ruchomymi bytami | hybryda albo retained `FRAMEBUFFER` | statyczna mapa + dynamiczne byty |
| `game_minesweeper.py` | retained UI, bardzo malo zmian | `DISPLAY_LIST` albo retained `FRAMEBUFFER` | niski koszt sceny, duzo statyki |
| `game_flappy_bird.py` | pelny redraw animacji | `FRAMEBUFFER` | naturalny workload dla `copy=False` |
| `game_snake.py` | delta redraw retained | retained `FRAMEBUFFER` | juz dobrze dopasowane |
| `game_robbo.py` | warstwa pygame-like | najpierw refaktor architektury | backend nie jest glownym problemem |

## Plan per gra

### 1. `game_frogger.py`

Stan:
- pelny blit tla praktycznie w kazdej klatce,
- ruchome obiekty i HUD dokladane po tle,
- architektura nie wykorzystuje retained nature sceny.

Quick wins:
- odswiezac HUD tylko przy zmianie `score`, `lives`, `time`, `high score`,
- ograniczyc lookupi sprite cache przez lokalne aliasy do najczesciej uzywanych sprite'ow,
- przeniesc wszelkie operacje przygotowawcze poza hot loop.

Srednie zmiany:
- rozbic scene na pasy (`road`, `river`, `home`, `hud`) i odswiezac tylko dirty lanes,
- zamiast pelnego blitu tla stosowac restore tla tylko pod obiektami, ktore sie poruszyly,
- scalac dirty recty lane-level, zamiast wykonywac wiele malych redrawow.

Wiekszy refaktor:
- zachowac statyczne tlo jako retained layer,
- ruchome obiekty trzymac jako osobne rekordy i rozważyć backend hybrydowy lub `DISPLAY_LIST` dla warstwy HUD/home slots.

Oczekiwany efekt:
- najwiekszy potencjalny wzrost plynnosci w calej paczce gier,
- wyraznie nizszy koszt CPU i mniejsze skoki czasu klatki.

### 2. `game_galaxian.py`

Stan:
- pelny redraw z `fill_color(BLACK)`, gwiazdami przez `pixel()`, sprite'ami, pociskami i tekstowym HUD,
- okresowe `gc.collect()` w rytmie gry.

Quick wins:
- usunac `gc.collect()` z petli renderu,
- HUD redrawing tylko przy zmianie `score/lives/wave`,
- prealokowac struktury dla efektow i unikac chwilowych alokacji.

Srednie zmiany:
- gwiazdy przeniesc do pre-renderowanej warstwy albo odswiezac tylko ich czesc,
- zgrupowac rysowanie prostych elementow w mniejsza liczbe wywolan,
- rozdzielic pole gry od HUD i trzymac HUD retained.

Wiekszy refaktor:
- hybryda: `FRAMEBUFFER` dla pola gry, retained/HUD na `DISPLAY_LIST`.

Oczekiwany efekt:
- poprawa stabilnosci frametime i usuniecie okresowych przyciec,
- umiarkowany wzrost FPS, ale duza poprawa subiektywnej plynnosci.

### 3. `game_sokoban.py`

Stan:
- redrawuje zbyt duza czesc planszy przy ruchach lokalnych,
- w hot path uzywa `math.sin()` do efektu pulsu.

Quick wins:
- zamienic `math.sin()` na LUT albo prosty krokowy licznik faz,
- ograniczyc redraw UI i licznikow tylko do zmian,
- skeszowac powtarzalne elementy kafli i obramowan.

Srednie zmiany:
- wprowadzic dirty-tile redraw tylko dla: starej pozycji gracza, nowej pozycji gracza, starej i nowej pozycji skrzyni,
- pre-renderowac statyczna warstwe poziomu przy ladowaniu poziomu,
- scalac sasiednie dirty tiles do mniejszej liczby rectow.

Wiekszy refaktor:
- przygotowac wariant `DISPLAY_LIST` dla planszy, gracza, skrzyn i markerow,
- statyczna warstwa planszy jako retained komendy, zmienne obiekty aktualizowane per ruch.

Oczekiwany efekt:
- duzy spadek kosztu pojedynczego ruchu,
- bardzo dobry kandydat do `DISPLAY_LIST`.

### 4. `game_pacman.py`

Stan:
- architektura retained jest juz sensowna,
- przywracanie tla pod bytami robi czesciowo zdublowana prace,
- `gc.collect()` moze powodowac szarpanie.

Quick wins:
- usunac `gc.collect()` z aktywnego gameplayu,
- HUD redraw tylko przy zmianie wyniku/liczby zyc,
- ograniczyc powtarzane przywracanie tla dla nakladajacych sie obszarow.

Srednie zmiany:
- mergowac recty czyszczenia Pacmana i duchow,
- skeszowac restore map tiles dla najczestszych obszarow,
- zmniejszyc liczbe wywolan draw na pojedyncza klatke.

Wiekszy refaktor:
- hybryda: statyczny labirynt retained, ruchome byty redraw tylko lokalnie,
- opcjonalnie `DISPLAY_LIST` dla warstwy UI i static map overlay.

Oczekiwany efekt:
- umiarkowany zysk w plynnosci i nizsze p95/p99 frametime.

### 5. `game_minesweeper.py`

Stan:
- model dirty-cell jest dobry,
- duzo narzutu daje sama reprezentacja danych w Pythonie,
- po redraw wystepuje sztuczne opoznienie.

Quick wins:
- usunac `time.sleep(0.01)` po redraw,
- nie wywolywac `set_font()` w kazdym hot redraw bez potrzeby,
- top bar odswiezac tylko przy zmianie czasu/licznika flag.

Srednie zmiany:
- zastapic zagniezdzone listy `bytearray` albo plaskimi buforami,
- skeszowac gotowe kafle dla najczestszych stanow (`hidden`, `revealed`, `flag`, `mine`),
- ograniczyc liczbe rysowanych elementow dekoracyjnych per tile.

Wiekszy refaktor:
- opcjonalny backend `DISPLAY_LIST` dla planszy i UI,
- trzymanie komorek jako retained entries zamiast rekonstruowania geometrii.

Oczekiwany efekt:
- mniejszy narzut CPU i RAM, ale nie jest to priorytet FPS.

### 6. `game_flappy_bird.py`

Stan:
- sensowny full-redraw workload,
- obecna struktura jest juz dosc dobra.

Quick wins:
- HUD odswiezac tylko przy zmianie wyniku,
- ograniczyc wszystko, co nie zmienia sie co klatke,
- upewnic sie, ze nie ma ukrytych alokacji w petli.

Srednie zmiany:
- rozważyć oddzielenie warstwy chmur/ozdob od glownej animacji,
- minimalizowac liczbe wywolan tekstowych w hot path.

Wiekszy refaktor:
- brak wysokiego ROI; zostawic `FRAMEBUFFER` i `copy=False`.

Oczekiwany efekt:
- raczej niewielki.

### 7. `game_snake.py`

Stan:
- jedna z najlepiej dopasowanych gier do retained `FRAMEBUFFER`,
- aktualizuje tylko niewielka liczbe pol.

Quick wins:
- kosmetyczne ograniczenie redraw HUD,
- sprawdzic, czy inicjalny full draw nie wykonuje zbednych wywolan.

Srednie zmiany:
- mozna rozwazyc jeszcze bardziej zwarte struktury danych dla ciala weza,
- opcjonalnie pre-render tla planszy.

Wiekszy refaktor:
- migracja do `DISPLAY_LIST` jest mozliwa, ale ROI bedzie niewielkie.

Oczekiwany efekt:
- niski priorytet, brak potrzeby pilnych zmian.

### 8. `game_robbo.py` / `robbo/`

Stan:
- glowny problem to warstwa zgodnosci pygame-like,
- spora czesc narzutu pochodzi z architektury, nie z pojedynczych draw calli.

Quick wins:
- ograniczyc koszt warstwy kompatybilnosci tam, gdzie sa oczywiste lookupi i alokacje,
- zidentyfikowac, ktore elementy sa redrawn bez potrzeby.

Srednie zmiany:
- retained redraw dla planszy i sprite'ow,
- redukcja liczby warstw abstrakcji miedzy logika gry a `rm690b0`.

Wiekszy refaktor:
- natywny renderer bez pygame emulation.

Oczekiwany efekt:
- duzy potencjalny zysk, ale najwyzszy koszt wdrozenia.

## Kolejnosc wdrazania

1. `game_frogger.py`: retained lanes + HUD dirty updates.
2. `game_galaxian.py`: usuniecie GC z hot path + retained HUD + optymalizacja gwiazd.
3. `game_sokoban.py`: dirty tiles + usuniecie `math.sin()`.
4. `game_pacman.py`: merge dirty rects i ograniczenie restore tla.
5. `game_minesweeper.py`: cleanup danych i usuniecie sztucznych opoznien.
6. Pozostale gry tylko po potwierdzeniu, ze ROI jest warte pracy.

## Co mierzyc po zmianach

- sredni FPS lub czas klatki,
- `p95` i `max_frame_ms`,
- liczbe draw calli / blitow na klatke,
- liczbe odswiezonych pikseli lub dirty rectow,
- czestotliwosc `gc.collect()` i liczbe alokacji w hot path,
- zuzycie RAM po starcie i po kilku minutach gry.

## Wniosek

Najpierw nalezy optymalizowac gry, ktore dzisiaj rysuja zbyt duzo mimo lokalnych zmian sceny: `Frogger`, `Sokoban`, `Pacman`. `Galaxian` wymaga glownie stabilizacji frametime i ograniczenia kosztow stalego full redraw. `Snake` i `Flappy Bird` sa relatywnie blisko sensownego optimum. `Robbo` ma sens dopiero po decyzji, czy projekt ma odejsc od pygame-like warstwy zgodnosci.
