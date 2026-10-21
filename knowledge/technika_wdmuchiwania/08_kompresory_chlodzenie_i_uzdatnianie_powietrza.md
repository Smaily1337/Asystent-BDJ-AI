# Baza Wiedzy: Kompresory, Chłodzenie i Uzdatnianie Sprężonego Powietrza

## Metadata
- **Źródło**: „Budowa nowoczesnych sieci telekomunikacyjnych z zastosowaniem techniki wdmuchiwania kabli światłowodowych”, autor: mgr inż. Michał Andrzejewski (GAMM-BUD / Blue Dragon Jet), Rozdziały 9.1, 10.7, 10.8, 10.9 i 11.4.
- **Kategoria**: Sprzęt Pneumatyczny, Kompresory Śrubowe, Chłodnice Końcowe (Aftercooler), Osuszacze Powietrza, Podgrzewacze Powietrza na Propan-Butan, Naolejacze
- **Słowa kluczowe**: kompresor śrubowy, po chłodnica, chłodnica końcowa, aftercooler, osuszacz powietrza, podgrzewacz powietrza, propan-butan, separator cyklonowy, Kaeser M82, Kaeser M13, Kaeser i-comp 3, balonowanie mikrorur, zamarzanie silnika pneumatycznego, mgła olejowa

---

## 1. Wymagania Pneumatyczne dla Różnych Klas Rurociągów

Sprężone powietrze jest nośnikiem energii w procesie wdmuchiwania kabli. W zależności od średnicy rurociągu wymagane są zupełnie inne parametry ciśnienia i wydatku objętościowego:

| Kategoria instalacji | Średnice kabla | Średnice rurociągu (ID) | Wymagane ciśnienie robocze | Wymagany wydatek objętościowy powietrza | Typowe modele sprężarek z programu produkcyjnego |
|:---|:---:|:---:|:---:|:---:|:---|
| **Tradycyjne kable doziemne i rury wtórne** | $10 – 25\text{ mm}$ | $26 – 41\text{ mm}$ (HDPE 32, 40, 50) | **$8 – 10\text{ bar}$** | **$8{,}0 – 12{,}0\text{ m}^3\text{/min}$** | Przewoźna sprężarka śrubowa dużej wydajności (np. **Kaeser M82**, **M100**, **M122**, Atlas Copco) |
| **Mikrokable standardowe** | $2 – 10\text{ mm}$ | $6 – 16\text{ mm}$ (Speedpipe 10–20) | **do $15 – 16\text{ bar}$** | **$1{,}0 – 2{,}0\text{ m}^3\text{/min}$** | Przewoźna sprężarka wysokociśnieniowa (np. **Kaeser M13 15 bar**, **M17A 15 bar**, **M27 14 bar**, **M31**) |
| **Cienkie mikrokable i wiązki EPFU** | $0{,}8 – 2\text{ mm}$ | $3 – 6\text{ mm}$ (Speedpipe 5–7) | **$10 – 12\text{ bar}$** | **$0{,}1 – 0{,}5\text{ m}^3\text{/min}$** | Kompaktowy kompresor tłokowy wysokociśnieniowy (np. **Kaeser i-comp 3**) |

> [!CRITICAL]
> **Fakt Inżynieryjny: Brak Uniwersalnego Kompresora**:
> **Nie istnieje jeden uniwersalny kompresor obsługujący całe spektrum telekomunikacji!**
> 1. Sprężarka do rur grubościennych (np. $10\text{ m}^3\text{/min}$ przy $8\text{ bar}$) jest **całkowicie bezużyteczna przy wdmuchiwaniu mikrokabli**, ponieważ nie jest w stanie wygenerować ciśnienia $15\text{ bar}$ niezbędnego do przezwyciężenia oporów mikrorur.
> 2. Sprężarka wysokociśnieniowa do mikrokanalizacji ($15\text{ bar}$, lecz wydatek tylko $1{,}2 – 1{,}5\text{ m}^3\text{/min}$) jest **bezużyteczna dla rury HDPE 40**, ponieważ prędkość liniowa powietrza w rurze o dużym przekroju spadnie niemal do zera – powietrze natychmiast ucieknie bez wytworzenia siły aerodynamicznej.

---

## 2. Krytyczna Rola Chłodnicy Końcowej (Aftercoolera)

Podczas sprężania w kompresorze śrubowym powietrze ulega gwałtownemu nagrzaniu w wyniku przemian termodynamicznych. Temperatura powietrza na wylocie ze stopnia śrubowego standardowo przekracza **$+90^\circ\text{C} \text{ do } +115^\circ\text{C}$**.

### 2.1. Skutki Wdmuchiwania Gorącym Powietrzem (Bez Chłodnicy)
1. **Zjawisko „balonowania” mikrorur**:
   - Tworzywo HDPE oraz modyfikowany polipropylen tracą wytrzymałość na rozciąganie w temperaturze powyżej $+40^\circ\text{C}$.
   - Pod wpływem ciśnienia 10–15 bar i temperatury $+90^\circ\text{C}$ ścianka mikrorury ulega plastycznemu rozszerzeniu („balonowaniu”), co prowadzi do gwałtownego wybuchu rury w wykopie lub wyskoczenia ze złączki push-fit.
2. **Plastyfikacja powłoki kabla i zanik poślizgu**:
   - Gorąca powłoka zewnętrzna kabla mięknie i staje się lepka.
   - Płyn poślizgowy ulega odparowaniu lub termicznej degradacji wiązań chemicznych.
   - Współczynnik tarcia $\mu$ skacze z $0{,}08$ do wartości powyżej $0{,}50$, doprowadzając do natychmiastowego zablokowania kabla w rurociągu.

### 2.2. Standard Techniczny Chłodnicy
- Sprężone powietrze przed podaniem do wdmuchiwarki musi przejść przez chłodnicę końcową (po-chłodnicę chłodzoną wentylatorem mechanicznym lub elektrycznym).
- **Zadanie chłodnicy**: Obniżenie temperatury sprężonego powietrza do poziomu **maksymalnie o $5^\circ\text{C} – 10^\circ\text{C}$ wyższego niż temperatura otoczenia**.
- Wdmuchiwanie mikrokabli pod ciśnieniem 15 bar bez chłodnicy powietrza jest kardynalnym błędem sztuki inżynieryjnej!

---

## 3. Uzdatnianie Powietrza: Separacja Wody i Osuszacze

Schłodzenie sprężonego powietrza w chłodnicy powoduje gwałtowny spadek jego zdolności do utrzymywania pary wodnej, co prowadzi do wykroplenia setek mililitrów wody na minutę.

### 3.1. Separator Cyklonowy
- Zintegrowany bezpośrednio za chłodnicą końcową.
- Za pomocą siły odśrodkowej odrzuca krople wody kondensacyjnej na ścianki naczynia, skąd woda odprowadzana jest na zewnątrz przez automatyczny zawór pływakowy lub czasowy zrzut kondensatu.
- Zapobiega wpompowaniu strug wody do rurociągu światłowodowego.

### 3.2. Osuszacz Powietrza (Ziębniczy / Adsorpcyjny)
- **Problem przymrozków i pracy w temperaturach $< +5^\circ\text{C}$**:
  - W temperaturze bliskiej $0^\circ\text{C}$ wilgotne sprężone powietrze ulega zjawisku rozprężania na dyszach wdmuchiwarki i w silnikach pneumatycznych (zjawisko Joule'a-Thomsona).
  - Gwałtowny spadek temperatury powoduje **natychmiastowe zamarzanie wilgoci i powstawanie lodu**.
  - W efekcie łopatki silnika pneumatycznego wdmuchiwarki blokują się lodem w ciągu kilkudziesięciu sekund, a w rurze tworzy się korek lodowy blokujący czoło kabla.
- **Wymóg**: Przy pracach w temperaturach otoczenia poniżej $+5^\circ\text{C}$ kompresor musi być wyposażony w zintegrowany lub zewnętrzny osuszacz sprężonego powietrza obniżający ciśnieniowy punkt rosy (PDP) do min. $-20^\circ\text{C} \text{ do } -40^\circ\text{C}$.

---

## 4. Podgrzewacze Powietrza na Gaz Propan-Butan (Praca w Warunkach Zimowych)

W sytuacjach awaryjnych lub przy pracach w warunkach głębokiego mrozu i wysokiej wilgotności względnej, gdy ekipa instalacyjna nie dysponuje sprężarką z wbudowanym osuszaczem adsorpcyjnym, stosuje się **zewnętrzne podgrzewacze powietrza**:
- **Zasada działania**: Urządzenie wyposażone w wysokowydajny palnik gazowy zasilany butlą z gazem **propan-butan**.
- **Funkcja**: Sprężone powietrze przepływa przez wymiennik ciepła podgrzewacza gazowego przed podaniem do wdmuchiwarki.
- **Efekt**: Podniesienie temperatury strumienia powietrza powyżej punktu tworzenia się kryształków lodu całkowicie eliminuje ryzyko zamarznięcia łopatek silników pneumatycznych oraz korków lodowych wewnątrz rurociągu kablowego.

---

## 5. Naolejacz Mgłowy do Silników Pneumatycznych

1. **Konstrukcja i Przeznaczenie**:
   - Wdmuchiwarki wyposażone w napęd pneumatyczny (np. silniki łopatkowe) wymagają ciągłego smarowania elementów wirujących.
   - Na wejściu zasilania pneumatycznego silnika instaluje się naolejacz mgłowy (lubricator).
2. **Rygorystyczne Rozdzielenie Linii Powietrza**:
   > [!WARNING]
   > Powietrze zaolejone może trafiać **WYŁĄCZNIE do zasilania silnika pneumatycznego wdmuchiwarki**!
   > **POWIETRZE WTŁACZANE DO RUROCIĄGU I KOMORY KABLA MUSI BYĆ W 100% WOLNE OD OLEJU MASZYNOWEGO!**
   > Olej mineralny niszczy płaszcz kabla HDPE/PA, degraduje złączki tworzywowe oraz uniemożliwia prawidłowe działanie wodnych płynów poślizgowych.
