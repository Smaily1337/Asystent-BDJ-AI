# Baza Wiedzy: Techniki Zaawansowane i Instalacje Nietypowe (Water Floating, Kaskady, BOP)

## Metadata
- **Źródło**: „Budowa nowoczesnych sieci telekomunikacyjnych z zastosowaniem techniki wdmuchiwania kabli światłowodowych”, autor: mgr inż. Michał Andrzejewski (GAMM-BUD / Blue Dragon Jet), Rozdziały 12 i 13.
- **Kategoria**: Zaawansowane Techniki Instalacyjne, Floating Wodny, Wdmuchiwanie Kaskadowe (Tandem), System SENSO JET, Technologia BOP w Kanalizacji Ściekowej
- **Słowa kluczowe**: floating wodny, hydroinstalacja, neutralna pływalność kabla, Westerschelde, pompa 25 bar, wdmuchiwanie tandemowe, wdmuchiwanie kaskadowe, Senso Jet Plumettaz, instalacja BOP, relining kanalizacji, mikrorurki stalowe

---

## 1. Technika Floatingu Wodnego (Hydroinstalacja Kabli Światłowodowych)

Technika wdmuchiwania wodnego (tzw. *Water Floating*) jest najbardziej zaawansowaną metodą instalacji kabli światłowodowych w rurociągach kablowych, umożliwiającą osiąganie odległości przekraczających możliwości tradycyjnego sprężonego powietrza (odcinki od $3000\text{ m}$ do ponad $6000\text{ m}$ w jednym ciągu bez przecinania włókien).

### 1.1. Zasada Fizyczna: Neutralna Pływalność
- **Prawo Archimedesa**: Gęstość wody ($\rho \approx 1000\text{ kg/m}^3$) jest kilkaset razy większa od gęstości sprężonego powietrza.
- Ciężar właściwy kabla światłowodowego w powłoce PE jest bardzo zbliżony do gęstości wody. W efekcie siła wyporu hydrostatycznego niemal całkowicie równoważy siłę grawitacji działającą na kabel (stan zbliżony do neutralnej pływalności / „nieważkości” kabla w cieczy).
- **Redukcja tarcia**: Nacisk jednostkowy kabla na dolną ściankę rurociągu spada niemal do zera. Siła tarcia wzdłużnego $F_t = m \cdot l \cdot \mu$ zostaje zredukowana o ponad **$90\%$**, dzięki czemu siła potrzebna do posuwu kabla jest minimalna.
- **Lepkość cieczy**: Przepływający słup wody działa na całej powierzchni powłoki kabla z potężną, jednorodną siłą ciągnącą.

### 1.2. Parametry Techniczne Sprzętu do Floatingu
- **Pompa wysokociśnieniowa**: Wielotłoczkowa pompa wodna generująca ciśnienie robocze **$22 – 25\text{ bar}$**.
- **Prędkość instalacji**: Zazwyczaj wynosi ok. **$17\text{ m/min}$** (posuw jest wolniejszy niż przy powietrzu, lecz nieprzerwany i stabilny).
- **Zapotrzebowanie na medium**: Wbrew pozorom zużycie wody jest relatywnie niewielkie, np. w teście na $5400\text{ m}$ zużyto zaledwie ok. **$450\text{ litrów}$** wody.

### 1.3. Rekordowe Przykłady Aplikacji Referencyjnych
1. **Próba Polowa w Niemczech ($5400\text{ m}$)**:
   - Wprowadzenie kabla światłowodowego na dystans $5400\text{ metrów}$ w jednym podejściu przy ciśnieniu roboczym 25 bar i zużyciu 450 l wody.
2. **Przejście Westerschelde w Holandii ($5500\text{ m}$)**:
   - Rekordowa instalacja kabla pod estuarium rzeki Skaldy (Westerschelde).
   - Kabel zainstalowany w rurociągu podmorskim na dystansie **$5500\text{ metrów}$** bez żadnych złączy pośrednich, co było niemożliwe do wykonania przy użyciu tradycyjnych kompresorów powietrznych ze względu na spadki ciśnienia.

---

## 2. Wdmuchiwanie Kaskadowe i Tandemowe na Trasach Długodystansowych

Dla tras tranzytowych o długościach 6 km, 10 km i dłuższych, stosuje się instalacje sekwencyjne:

### 2.1. Metoda Tandemowa (Wdmuchiwarki w Szeregu)
- W punkcie początkowym instaluje się wdmuchiwarkę główną A.
- W studni pośredniej (np. na 2500 m) montuje się drugą wdmuchiwarkę B (zasilaną niezależnym kompresorem) wyposażoną w złączkę ciśnieniową Y.
- Wdmuchiwarka A podaje kabel do studni pośredniej; w momencie przejścia kabla przez głowicę wdmuchiwarki B, zostaje załączony napęd maszyny B, która przejmuje siłę pchania i dopręża powietrze na kolejnym odcinku trasy.

### 2.2. Strategia Wdmuchiwania Odcinka 6 km z Układaniem w Ósemkę
1. **Zespół Jednoosobowy / Jedna Maszyna**:
   - Ustawienie wdmuchiwarki w studni na 3. kilometrze (środek trasy).
   - Wdmuchnięcie 3 km kabla w stronę studni początkowej (kierunek A).
   - Rozwinięcie pozostałych 3 km kabla z bębna i ułożenie w zwoje ósemkowe w koszu Twister.
   - Wprowadzenie kabla z kosza Twister i wdmuchnięcie w stronę studni końcowej (kierunek B).
2. **Zespół Dwuosobowy / Dwie Maszyny (Zbieżnie do Środka)**:
   - Dwie ekipy wdmuchują kable z obu skrajnych końców trasy (studnia 0 km i studnia 6 km) do studni centralnej (3 km), gdzie wykonuje się mufę światłowodową ze spawami.

---

## 3. Technologia SENSO JET (Precyzyjny Montaż w Kapilarnych Rurkach Stalowych)

Opracowana przez szwajcarską firmę **Plumettaz** specjalistyczna technologia przeznaczona do instalacji światłowodowych czujników telemetrycznych (Distributed Temperature Sensing – DTS oraz Distributed Acoustic Sensing – DAS):

- **Średnice rurociągów**: Mikroskopijne kapilary ze stali nierdzewnej o średnicy wewnętrznej od **$2\text{ mm}$ do $5\text{ mm}$**.
- **Media nośne i ciśnienia**:
  - Woda pod ciśnieniem **$20 – 40\text{ bar}$**.
  - W przypadku rurek o ekstremalnie małym świetle lub przy temperaturach ujemnych stosuje się **czysty alkohol techniczny (etanol / glikol)** pod ciśnieniem sięgającym aż **$100\text{ bar}$**!
- **Zasięg**: Wprowadzanie włókien sensorowych na odległości do **$10\text{ km}$** wzdłuż ropociągów, gazociągów oraz głębokich odwiertów geotermalnych.

---

## 4. Technologia BOP (Bytes in Old Pipes) w Infrastrukturze Ściekowej

Budowa sieci światłowodowej w gęsto zabudowanych centrach miast historycznych napotyka barierę braku miejsca w pasie drogowym i gigantycznych kosztów wykopów otwartych. Rozwiązaniem jest wykorzystanie istniejących kolektorów kanalizacji deszczowej i ściekowej:

### 1. Zasada Systemu BOP
- Wykorzystanie czynnych kanałów ściekowych (o przekrojach od DN 200 do kolektorów przełazowych) jako magistrali teletechnicznych.
- Roboty bezwykopowe wprowadzają do wnętrza kanału specjalne rury osłonowe wykonane ze stali kwasoodpornej lub grubościennego polietylenu zbrojonego, mocując je w sklepieniu kolektora za pomocą rozporowych kotew ze stali nierdzewnej (powyżej lustra ścieków).

### 2. Zastosowanie przy Reliningu Kanalizacji
- Podczas bezwykopowej renowacji starych kanałów metodą rękawa utwardzanego promieniami UV (CIPP – Cured In Place Pipe), rurki światłowodowe wprowadza się pomiędzy stary kanał a zewnętrzną ściankę utwardzanego rękawa, zyskując idealną ochronę mechaniczną i chemiczną kabla bez ograniczania światła kanału ściekowego.
