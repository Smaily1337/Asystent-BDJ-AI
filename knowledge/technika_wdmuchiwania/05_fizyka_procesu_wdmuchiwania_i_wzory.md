# Baza Wiedzy: Fizyka Procesu Wdmuchiwania Kabli i Wzory Inżynieryjne

## Metadata
- **Źródło**: „Budowa nowoczesnych sieci telekomunikacyjnych z zastosowaniem techniki wdmuchiwania kabli światłowodowych”, autor: mgr inż. Michał Andrzejewski (GAMM-BUD / Blue Dragon Jet), Rozdział 7 (Teoretyczne aspekty procesu wdmuchiwania).
- **Kategoria**: Fizyka Wdmuchiwania, Wzory Matematyczne, Mechanika Płynów, Obliczenia Sił Tarcia, Stopień Wypełnienia
- **Słowa kluczowe**: tarcie proste, formuła Eulera, opory na łukach, siła ciągnąca wdmuchiwania, metoda strumieniowa Jetting, metoda tłoczkowa Piston, wzór na siłę aerodynamiczną, współczynnik wypełnienia rury, wyboczenie kabla, ciśnienie manometryczne

---

## 1. Siły Działające na Kabel w Rurociągu

W procesie pneumatyczno-mechanicznego wprowadzania kabla światłowodowego do rurociągu zachodzi jednoczesne oddziaływanie trzech sił:
1. **Siła tarcia kabla o ściankę rurociągu ($F_t$)**: siła oporowa przeciwdziałająca ruchowi kabla, zależna od masy kabla, geometrii trasy, współczynnika tarcia tworzyw oraz zafalowania rury.
2. **Siła pchająca podajnika wdmuchiwarki ($F_p$)**: siła mechaniczna przekazywana przez pasy lub rolki podajnika wdmuchiwarki na powłokę kabla.
3. **Siła ciągnąca powietrza ($F_c$)**: siła wzdłużna generowana przez przepływający strumień sprężonego powietrza (w metodzie strumieniowej) lub różnicę ciśnień na czole tłoczka (w metodzie tłoczkowej).

Równowaga dynamiczna ruchu kabla zachodzi, gdy:
$$F_p + F_c > F_t$$

---

## 2. Siła Tarcia w Rurociągu Prostoliniowym

Dla idealnie prostego, poziomego odcinka rurociągu kablowego siłę tarcia ślizgowego wyznacza wzór:

$$F_t = m \cdot l \cdot \mu$$

gdzie:
- $F_t$ – całkowita siła oporu tarcia [N],
- $m$ – ciężar jednostkowy kabla światłowodowego na metr bieżący [N/m] (np. masa $0{,}2\text{ kg/m} \times 9{,}81\text{ m/s}^2 \approx 2\text{ N/m}$),
- $l$ – długość rurociągu / odcinka kabla w rurze [m],
- $\mu$ – współczynnik tarcia ślizgowego powłoki kabla o wewnętrzną ściankę rury [-].
  - Dla pary PE (kabel) – HDPE (rura) z profesjonalnym lubrykantem: $\mu \approx 0{,}08 – 0{,}10$.
  - Dla rury suchej lub zanieczyszczonej: $\mu \approx 0{,}25 – 0{,}40$.

### Przykład Inżynieryjny z Książki:
- Ciężar kabla: $m = 2\text{ N/m}$
- Długość odcinka: $l = 2000\text{ m}$
- Współczynnik tarcia: $\mu = 0{,}08$
- Siła tarcia teoretyczna:
  $$F_t = 2 \cdot 2000 \cdot 0{,}08 = 320\text{ N}$$
- **Uwaga praktyczna**: W warunkach rzeczywistych (niewielkie naturalne zafalowania gruntu, zmiany temperatur) rzeczywista siła tarcia jest o **ok. 30% wyższa** od wartości teoretycznej i wynosi ok. **$416\text{ N}$**.

---

## 3. Tarcie na Łukach – Formuła Eulera (Wykładniczy Wzrost Tarcia)

Gdy rurociąg zmienia kierunek (łuk poziomy lub pionowy), siła docisku kabla do ścianki rury gwałtownie wzrasta pod wpływem naciągu wzdłużnego. Zjawisko to opisuje **równanie Eulera-Eytelweina**:

$$F_2 = F_1 \cdot e^{\mu \cdot \alpha}$$

gdzie:
- $F_1$ – siła osiowa działająca na kabel bezpośrednio przed łukiem [N],
- $F_2$ – siła osiowa za łukiem [N],
- $\mu$ – współczynnik tarcia [-],
- $\alpha$ – kąt zagięcia łuku wyrażony w radianach [rad] ($90^\circ = \frac{\pi}{2} \approx 1{,}57\text{ rad}$),
- $e$ – podstawa logarytmu naturalnego ($e \approx 2{,}71828$).

### Wpływ Skumulowanych Zakrętów:
Dla pojedynczego zakrętu pod kątem $90^\circ$ ($\alpha = 1{,}57\text{ rad}$) przy współczynniku tarcia $\mu = 0{,}08$:
$$e^{0{,}08 \cdot 1{,}57} = e^{0{,}1256} \approx 1{,}134$$
Oznacza to, że **każdy pojedynczy zakręt $90^\circ$ zwiększa siłę oporu wzdłużnego o 13,4%**.

Jeśli na trasie znajduje się $n = 8$ takich łuków (np. ominięcia przeszkód, wejścia do studni):
$$(1{,}134)^8 \approx 2{,}0$$

> [!WARNING]
> **Zasada 8 Łuków**: Zaledwie **osiem zakrętów o kącie $90^\circ$ podwaja całkowitą siłę oporu tarcia** na trasie! Dlatego bezwzględnym celem projektanta i wykonawcy jest unikanie ostrych zmian kierunku i stosowanie łuków o promieniach powyżej 2,5 m.

---

## 4. Siła Ciągnąca w Metodzie Strumieniowej (Jetting)

W metodzie strumieniowej przepływający z dużą prędkością strumień powietrza opływa kabel na całej jego długości, wytwarzając naprężenia ścinające (opór lepki) skierowane w stronę wylotu rury. 

Siłę wzdłużną generowaną przez strumień powietrza opisuje wzór:

$$F_{\text{jetting}} = \frac{\pi}{4} \cdot \frac{L_2}{L_1} \cdot d \cdot (D - d) \cdot P$$

gdzie:
- $F_{\text{jetting}}$ – siła ciągnąca powietrza [N],
- $L_1$ – całkowita długość rurociągu [m],
- $L_2$ – długość kabla już wprowadzonego do rury [m] (gdy kabel dochodzi do końca trasy, $\frac{L_2}{L_1} = 1$),
- $d$ – zewnętrzna średnica kabla [mm],
- $D$ – wewnętrzna średnica rury [mm],
- $P$ – ciśnienie robocze sprężonego powietrza na wejściu [MPa].

### Przykład Obliczeniowy z Książki:
- Średnica zewnętrzna kabla: $d = 12\text{ mm}$
- Średnica wewnętrzna rury HDPE 40: $D = 35\text{ mm}$
- Ciśnienie robocze kompresora: $P = 0{,}8\text{ MPa}$ ($8\text{ bar}$)
- Stan: koniec wdmuchiwania ($L_2 = L_1 \rightarrow \frac{L_2}{L_1} = 1$)

$$F_{\text{jetting}} = \frac{\pi}{4} \cdot 1 \cdot 12 \cdot (35 - 12) \cdot 0{,}8 = 0{,}7854 \cdot 12 \cdot 23 \cdot 0{,}8 \approx \mathbf{173{,}4\text{ N}}$$

**Analiza inżynieryjna**:
Jeśli całkowita siła tarcia kabla na 2000 m wynosi ok. $300\text{ N}$, a strumień powietrza dostarcza $173{,}4\text{ N}$, wówczas pozostałe:
$$F_{\text{pusher}} = 300\text{ N} - 173{,}4\text{ N} = \mathbf{126{,}6\text{ N}}$$
musi zostać doprowadzone przez mechaniczny podajnik wdmuchiwarki (pasy/rolki).

---

## 5. Siła Ciągnąca w Metodzie Tłoczkowej (Piston)

W metodzie tłoczkowej czoło kabla wyposażone jest w szczelny tłoczek (piston). Ciśnienie sprężonego powietrza działa bezpośrednio na powierzchnię czołową tłoczka, pomniejszoną o przekrój kabla:

$$F_{\text{piston}} = \frac{\pi}{4} \cdot (D^2 - d^2) \cdot P$$

gdzie:
- $F_{\text{piston}}$ – siła ciągnąca tłoczka [N],
- $D$ – wewnętrzna średnica rury [mm],
- $d$ – zewnętrzna średnica kabla [mm],
- $P$ – ciśnienie robocze powietrza [MPa].

### Przykład Obliczeniowy z Książki (Dla tych samych parametrów):
- $d = 12\text{ mm}$, $D = 35\text{ mm}$, $P = 0{,}8\text{ MPa}$ ($8\text{ bar}$):
$$F_{\text{piston}} = \frac{\pi}{4} \cdot (35^2 - 12^2) \cdot 0{,}8 = \frac{\pi}{4} \cdot (1225 - 144) \cdot 0{,}8 = 0{,}7854 \cdot 1081 \cdot 0{,}8 \approx \mathbf{679{,}2\text{ N}}$$

> [!NOTE]
> **Porównanie Metod**:
> W tych samych warunkach metoda tłoczkowa generuje siłę ciągnącą aż **$\approx 679\text{ N}$** (prawie 4-krotnie więcej niż metoda strumieniowa $173\text{ N}$)!
> Siła $679\text{ N}$ z naddatkiem pokonuje opór tarcia kabla ($300\text{ N}$), dlatego w metodzie tłoczkowej kabel jest ciągnięty przez tłok, a podajnik wdmuchiwarki nie pcha kabla z dużą siłą, lecz kontroluje jego prędkość i zapobiega nadmiernemu rozpędzeniu.

---

## 6. Stopień Wypełnienia Rurociągu (Fill Ratio)

Stopień wypełnienia rurociągu kablem jest kluczowym parametrem decydującym o przepływie aerodynamicznym oraz podatności kabla na wyboczenie.

### 6.1. Definicje
- **Wypełnienie średnicowe ($K_d$)**:
  $$K_d = \frac{d}{D} \times 100\%$$
- **Wypełnienie powierzchniowe ($K_s$)**:
  $$K_s = \frac{d^2}{D^2} \times 100\%$$

### 6.2. Zalecane Wartości Graniczne
- **Kanalizacja wtórna i tradycyjne kable**:
  - Zalecane wypełnienie powierzchniowe: **$K_s \le 40\%$** (maksymalnie 50%).
- **Mikrokanalizacja (mikrokable w mikrorurach)**:
  - Optymalne wypełnienie średnicowe: **$K_d = 50\% – 70\%$** (najwyższe zasięgi osiąga się przy $K_d \approx 60\%$).

### 6.3. Konsekwencje Niewłaściwego Doboru Średnic
1. **Zbyt małe wypełnienie ($K_d < 35\% – 40\%$)**:
   - Kabel posiada zbyt dużą swobodę przestrzenną w rurze.
   - Popychany przez wdmuchiwarkę kabel ulega natychmiastowemu pofałdowaniu (tzw. zjawisko helisy / węża – *snaking*), zapierając się o ścianki rury i doprowadzając do zablokowania lub złamania włókien.
2. **Zbyt duże wypełnienie ($K_d > 75\% – 80\%$)**:
   - Przekrój szczeliny pierścieniowej między kablem a ścianką rury staje się zbyt wąski.
   - Dochodzi do zdławienia przepływu powietrza; spadek ciśnienia wzdłuż trasy jest gwałtowny, prędkość powietrza spada, a siła aerodynamiczna $F_{\text{jetting}}$ drastycznie maleje. Wdmuchiwanie zatrzymuje się po kilkuset metrach.
