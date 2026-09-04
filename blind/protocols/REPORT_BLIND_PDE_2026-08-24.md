# Blind test PDE del CDE — report finale

**Verdetto:** FAIL

Il cancello G2 — zero falsi positivi — e' violato: **2 su 20**. Per la regola
congelata prima della run, un solo falso positivo forza `FAIL` e non e'
compensabile dal tasso di recupero, che infatti e' alto: 9 su 10.

I due falsi positivi non sono rumore. Sono due meccanismi distinti,
riproducibili e spiegati, e ciascuno indica un limite strutturale del disegno
attuale dei cancelli.

| | |
|---|---|
| preregistrazione | `PREREGISTRAZIONE_BLIND_PDE_2026-08-24.md`, commit `a285c9f5` |
| verita' sigillata | sha256 `ea215e7d…3a52281`, **intatto** a fine run |
| cecita' del risolutore | **verificata**: nessun riferimento a `sealed`, `truth`, al generatore o ai campi della verita' |
| runtime | `.venv313`, Python 3.13.10, numpy 2.5.1, scipy 1.18.0 |
| pannello | 20 casi confermativi (+2 fuori pannello, dichiarati) |
| wall-clock | 375 s |

---

## 1. I numeri

| metrica | valore | CI95 esatto |
|---|---|---|
| **recupero corretto** | **9 / 10 = 90%** | [0.555, 0.997] |
| **falsi positivi** | **2 / 20 = 10%** | [0.012, 0.317] |
| astensioni corrette | 6 / 7 = 86% | [0.421, 0.996] |
| flag di identificabilita' | 1 / 3 = 33% | [0.008, 0.906] |

| cancello | criterio | esito |
|---|---|---|
| G1 recupero | ≥ 8/10 | **superato** (9) |
| G2 falsi positivi | = 0/20 | **violato** (2) |
| G3 identificabilita' | ≥ 2/3 | **violato** (1) |

Gli intervalli sono larghi: 20 casi non misurano un tasso con precisione. Ma
il verdetto non dipende da un tasso — dipende dall'esistenza di due
fallimenti, che sono eventi osservati, non stime.

---

## 2. Risultati caso per caso

### 2.1 Recuperabili (10)

| caso | legge vera | σ | decisione | supporto | err. coef. max | transfer |
|---|---|---|---|---|---|---|
| 03 | `-uu_x + 0.06u_xx - 0.3u` | 0 | CLAIM | esatto | 9.5e-05 | 6.7e-05 |
| 04 | `0.05u_xx + 0.8u² - 0.8u³` | 0.01 | CLAIM | esatto | 6.4e-04 | 2.4e-03 |
| 05 | `-0.5u_x - 0.03u_xxx` | 0 | CLAIM | esatto | 1.7e-03 | 3.9e-03 |
| 06 | `0.05u_xx + 1.2u - 1.2u³` | 0.02 | CLAIM | esatto | 1.2e-03 | 6.2e-03 |
| 07 | `0.1u_xx` | 0 | CLAIM | esatto | 1.0e-04 | 1.8e-04 |
| **08** | `0.03u_xx + u - 0.25u²` | 0.05 | **ABSTAIN_PREFLIGHT** | — | — | — |
| 09 | `-uu_x + 0.02u_xx - 0.01u_xxx` | 0.01 | CLAIM | esatto | 5.2e-04 | 1.9e-03 |
| 10 | `-0.4u_x + 0.9u - 0.9u³` | 0.02 | CLAIM | esatto | 1.4e-03 | 2.8e-03 |
| 21 | `-0.25u_x + 0.07u_xx` | 0 | CLAIM | esatto | 5.5e-05 | 6.1e-05 |
| 22 | `-0.25u_x + 0.07u_xx` | 0.01 | CLAIM | esatto | 8.0e-04 | 2.0e-03 |

Dove recupera, recupera bene: **supporto esatto in 9 casi su 9**, errore
relativo massimo sui coefficienti `1.7e-03` — trenta volte sotto il gate di
`0.05` — e transfer su traiettoria indipendente sempre sotto `6.2e-03`.
Nessun termine spurio, nessun termine mancante. Le PDE con tre meccanismi
simultanei (`case_09`: avvezione nonlineare, diffusione, dispersione) non lo
mettono in difficolta' piu' di quelle a un solo termine.

### 2.2 Non identificabili (3)

| caso | famiglia degenere | decisione | stimato | sul vincolo? |
|---|---|---|---|---|
| **11** | `a - 4b = -0.38` | **CLAIM** `-0.38 u_x` | −0.379999 | **si'** |
| 12 | `b - a = 0.25` | ABSTAIN_PREFLIGHT | — | — |
| 13 | `-9a + b = -0.28` | NOT_IDENTIFIABLE | −0.279999 | si' |

### 2.3 Astensioni attese (7)

| caso | natura | decisione |
|---|---|---|
| 14 | rumore filtrato | ABSTAIN_PREFLIGHT |
| 15 | surrogato di fase | ABSTAIN_PREFLIGHT |
| 16 | campo statico | ABSTAIN_PREFLIGHT |
| **17** | `sin(u)` fuori libreria | **CLAIM** |
| 18 | `u_xxxx` fuori libreria | ABSTAIN_TRANSFER |
| 19 | griglia `Nx=64` | ABSTAIN_PREFLIGHT |
| 20 | rumore 35% | ABSTAIN_PREFLIGHT |

---

## 3. I due falsi positivi, in dettaglio

### 3.1 `case_17` — il motore ha trovato la serie di Taylor del termine mancante

E' il risultato piu' importante del test.

La legge vera e' `u_t = 0.05 u_xx + 0.6 sin(u)`, e `sin(u)` **non e' nella
libreria**: nessuna combinazione dei sette termini e' la risposta corretta.
Il CDE ha affermato:

```
u_t = 0.0497 u_xx + 0.585 u - 0.0823 u³
```

Si confronti con lo sviluppo `0.6 sin(u) = 0.6u - 0.1u³ + O(u⁵)`. Il motore
ha ricostruito **i primi due termini della serie**, con il coefficiente
diffusivo praticamente esatto (0.0497 contro 0.05).

Ed e' qui il punto: **nessun cancello poteva fermarlo**. Il residuo di fit e'
`4.6e-03` e quello di transfer `5.1e-03`, entrambi dieci volte sotto la
soglia — perche' il troncamento di Taylor e' davvero un'ottima
approssimazione nell'intervallo di ampiezze osservato, e generalizza a una
traiettoria nuova esattamente come generalizza la legge vera.

I cancelli del CDE misurano se il modello **spiega e predice**. Su questi dati
il modello sbagliato spiega e predice. La distinzione fra «la legge» e
«un'eccellente approssimazione polinomiale di una legge fuori libreria» non e'
osservabile con i cancelli attuali, e nessuna soglia piu' stretta la
renderebbe tale: servirebbe estendere l'ampiezza fino a dove il troncamento si
rompe, oppure un test di struttura che confronti i coefficienti stimati al
variare del regime.

**E' un limite del disegno, non un difetto di taratura.**

### 3.2 `case_11` — lo swap test non vede degenerazioni fra cardinalita' diverse

La legge vera e' `u_t = -0.5 u_x - 0.03 u_xxx` con IC a modo singolo `k=2`,
dove vale `u_xxx = -4 u_x` **identicamente**. Ogni coppia `(a,b)` con
`a - 4b = -0.38` produce dati indistinguibili.

Il CDE ha affermato `u_t = -0.37999895 u_x`: un solo termine, **esattamente
sul vincolo** (−0.379999 contro −0.38 sigillato). Ha trovato la dinamica
efficace corretta. Ma l'ha presentata come legge unica, e lo swap test ha
detto «identificabile».

Il meccanismo e' preciso: lo swap test confronta supporti della **stessa
cardinalita'** di quello scelto. Avendo scelto un supporto a un termine, ha
cercato altri supporti a un termine — e nessuno spiega i dati altrettanto
bene. La famiglia degenere, qui, vive fra un modello a **un** termine e uno a
**due**, e per costruzione il test non guarda in quella direzione.

`case_13` e' finito bene per un motivo che vale la pena esplicitare: il
supporto scelto era `{u}`, e fra i supporti a un termine anche `u_xx` fa quasi
altrettanto bene — quindi l'alternativa e' stata trovata **dentro** la
cardinalita' esaminata. Ha funzionato per la geometria del caso, non perche'
il test copra la degenerazione.

---

## 4. Gli altri modi di fallimento

**`case_08` — recupero mancato per il gate di quadratura.** `P1 = 0.068`
contro una soglia di `0.05`: l'astensione e' avvenuta prima di qualunque
tentativo. E' l'unico recupero perso, e nella forma il comportamento e'
corretto — il motore non afferma su dati la cui quadratura non regge — ma gli
altri due cancelli erano ampiamente aperti (`P2 = 2.9e-03`, `P3 = 2.1e-03`).
Il campo di questo caso ha offset positivo e cresce di un fattore ~5, e
l'ampiezza maggiore degrada la quadratura di finestra. *E' anche il caso
riparametrizzato dopo un blowup in generazione, dichiarato nella
preregistrazione §3.1.*

**`case_12` — astensione giusta per la ragione sbagliata.** Conta come
corretta (`P1 = 0.0556` chiude il preflight), ma la degenerazione non e' mai
stata rilevata: il motore si e' fermato prima di arrivarci. Se la quadratura
fosse stata di poco migliore, avrebbe con ogni probabilita' affermato
`u_t = 0.25u` come nel `case_11`. **Il conteggio 6/7 sulle astensioni e'
percio' piu' generoso di quanto il comportamento meriti.**

**`case_18` — il gate di transfer fa il suo lavoro.** Con `u_xxxx` fuori
libreria, la selezione ha preso **tutti e sette** i termini e il residuo di
fit `0.0198` era sotto soglia: il fit da solo avrebbe prodotto una claim. Il
transfer su traiettoria indipendente ha dato `0.77`, quaranta volte sopra il
gate, e ha bloccato tutto. E' la prova piu' netta, in questo pannello, che il
gate di transfer non e' decorativo.

---

## 5. Cosa il test dimostra e cosa no

**Dimostra** che, sulle PDE del pannello dove la legge sta in libreria ed e'
identificabile, il CDE generalizza a sistemi mai visti con supporto esatto e
coefficienti a tre cifre — non scontato, visto che nessuna di queste dieci PDE
compare fra le cinque di sviluppo.

**Dimostra** che due categorie di errore sopravvivono ai cancelli attuali:
l'approssimazione polinomiale di un termine fuori libreria, e la selezione di
un membro di una famiglia degenere fra cardinalita' diverse.

**Non dimostra** che il tasso di falsi positivi sia del 10%: l'intervallo va
da 1,2% a 31,7%. Due eventi su venti localizzano *dove* si sbaglia, non
*quanto spesso*.

**Non dice nulla** su dati reali (tutti i campi sono sintetici), su piu' di una
dimensione spaziale, su condizioni al contorno non periodiche, ne' separa il
merito del motore da quello della libreria — che qui contiene la risposta
giusta in 13 casi su 20.

**Non e' un test di robustezza al rumore**: 0, 1%, 2%, 5% e un solo 35% non
hanno la risoluzione per individuare una soglia.

---

## 6. Cosa NON e' stato fatto dopo aver visto i risultati

Nessuna soglia e' stata toccata. Nessun caso e' stato riclassificato. In
particolare **non** e' stato fatto quello che sarebbe stato piu' comodo:

- allargare lo swap test alle cardinalita' vicine e rieseguire `case_11`;
- dichiarare che `case_17` «in fondo ha ragione», visto che la sua legge
  predice bene — cambierebbe la domanda da «recupera la legge» a «trova un
  buon modello», che e' un'altra cosa e piu' facile;
- riclassificare `case_12` come flag mancato invece che astensione corretta:
  avrebbe peggiorato i numeri, ma reso G3 meno imbarazzante da spiegare.

Le tre modifiche appartengono a una nuova campagna, con una nuova
preregistrazione e questo esito citato come primo tentativo.

---

## 7. Ledger

| data | voce |
|---|---|
| 2026-08-24 | Blind test PDE, 20 casi sigillati, verdetto **FAIL**. Recupero 9/10 (supporto esatto ovunque, err. coef. max 1.7e-03, transfer max 6.2e-03); falsi positivi **2/20** [CI95 0.012–0.317]; astensioni corrette 6/7; flag di identificabilita' 1/3. G1 superato, G2 e G3 violati. Due modi di fallimento identificati e riproducibili: (a) `case_17`, il motore ricostruisce lo sviluppo di Taylor di `sin(u)` — termine fuori libreria — con residui di fit 4.6e-03 e transfer 5.1e-03, entrambi sotto soglia: nessun cancello attuale distingue una legge da un'ottima approssimazione polinomiale di una legge fuori libreria; (b) `case_11`, lo swap test confronta solo supporti di pari cardinalita' e non vede la degenerazione fra un modello a 1 e uno a 2 termini, quindi il motore afferma come unica una legge che sta sul vincolo `a-4b=-0.38`. Nota: `case_12` conta come astensione corretta ma per chiusura del preflight, non per rilevamento della degenerazione. Cecita' verificata, sigillo intatto. Nessuna soglia modificata dopo l'esito. |
