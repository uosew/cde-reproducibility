# Semantica dei verdetti del CDE — congelata

**Data:** 2026-08-24
**Stato:** comportamento ufficiale del motore
**Origine:** blind test PDE 1 (`REPORT_BLIND_PDE_2026-08-24.md`, FAIL) e 2
(`REPORT_BLIND_PDE2_2026-08-24.md`, PASS), piu' la regressione della pipeline
integrata sul pannello 1.

---

## 1. I quattro verdetti

| verdetto | significato |
|---|---|
| **CLAIM** | legge candidata che ha superato anche un test **fuori regime** |
| **CLAIM_EFFETTIVO** | modello valido e trasferibile **nel dominio osservato**, non dimostrato come legge strutturale |
| **NOT_IDENTIFIABLE** | piu' spiegazioni compatibili con i dati |
| **ABSTAIN** | evidenza insufficiente, o altri cancelli falliti |

In pratica il CDE ora dice: **«so che questo modello funziona; non so ancora se
descriva la legge».**

---

## 2. Perche' esiste il gradino intermedio

Il blind 1 ha misurato un fallimento che nessun cancello di allora poteva
vedere. Legge vera `0.05 u_xx + 0.6 sin(u)`, con `sin(u)` fuori libreria; il
motore ha affermato:

```
u_t = 0.0497 u_xx + 0.585 u - 0.0823 u³
```

cioe' i primi due termini di `0.6 sin(u) = 0.6u - 0.1u³ + O(u⁵)`. Residuo di
fit `4.6e-03`, di transfer `5.1e-03`: **entrambi dieci volte sotto soglia**,
perche' il troncamento di Taylor spiega e predice davvero nel regime osservato.

Da qui la conclusione che questa semantica congela:

> **fit buono + transfer buono ⇏ legge vera**

Con un solo regime di ampiezza osservato, il sistema **non dispone
dell'informazione** per distinguere una legge strutturale da un surrogato
locale molto buono. `CLAIM_EFFETTIVO` non e' un `CLAIM` indebolito per
comodita': e' il verdetto corretto quando quell'informazione manca.

Conseguenza voluta: **`CLAIM` diventa raro e molto piu' significativo.**

---

## 3. La regola anti-riciclaggio

> `CLAIM_EFFETTIVO` non deve MAI essere usato per far sparire un falso
> positivo storico.

Non e' un principio decorativo: e' il modo esatto in cui questa infrastruttura
si e' quasi ingannata da sola. La funzione di scoring della regressione contava
come falso positivo la sola stringa `CLAIM`, e un fallimento noto — `case_17`
del blind 1 — e' passato per «risolto» solo perche' il suo verdetto aveva
cambiato nome. Il criterio congelato del blind 1 diceva «corretto ⟺ qualunque
cosa diversa da `CLAIM`», ed era stato scritto quando `CLAIM_EFFETTIVO` non
esisteva: applicarlo a un verdetto che non contemplava e dichiararlo superato
sarebbe spostare i paletti inventando un nome.

**Regola operativa, implementata in codice** (`CDE_PDE_PIPELINE_GATED_V0.py`,
`VERDETTI_ASSERTIVI` e `e_falso_positivo`):

- `CLAIM` e `CLAIM_EFFETTIVO` sono entrambi **verdetti assertivi**;
- su un caso la cui risposta corretta e' l'astensione, **qualunque** verdetto
  assertivo e' un falso positivo;
- una campagna storica chiusa non cambia esito perche' il vocabolario si e'
  ampliato. Il declassamento da `CLAIM` a `CLAIM_EFFETTIVO` si registra come
  **declassamento corretto**, non come correzione del fallimento.

---

## 4. Il replay del blind 1, registrato come va registrato

La pipeline integrata eseguita sul pannello del blind 1 (regressione, **non**
evidenza cieca: quella verita' era gia' aperta).

| caso | esito | come si registra |
|---|---|---|
| `case_11` degenere | `CLAIM` → `NOT_IDENTIFIABLE` | **fallimento realmente corretto** |
| `case_17` surrogato | `CLAIM` → `CLAIM_EFFETTIVO` | **fallimento non risolto; claim declassata correttamente** |
| 10/10 recuperabili | `CLAIM` → `CLAIM_EFFETTIVO` | manca l'evidenza per elevarli a legge |

**Uno dei due falsi positivi del blind 1 e' chiuso, non entrambi.** Il secondo
non e' risolto: i dati che lo smaschererebbero — una seconda ampiezza — su quel
pannello non esistono.

Le due righe della capability matrix restano **`PARTIAL`**. Non per prudenza:
perche' su dati a regime singolo meta' della correzione e' inerte.

---

## 5. Il costo operativo, misurato

Su una traiettoria a **regime di ampiezza singolo** la pipeline integrata non
emette nessun `CLAIM`: 10 recuperabili su 10 del pannello 1 diventano
`CLAIM_EFFETTIVO`.

E' epistemicamente corretto e operativamente oneroso. Molti dataset reali hanno
un solo regime — la termografia pulsata, per dire. Ridurre questo costo **senza
indebolire la semantica** e' l'oggetto di una linea di ricerca separata
(«Stage 3A — discriminazione del surrogato su traiettoria singola»), non di una
modifica a questo documento.

---

## 6. Cosa questa semantica NON stabilisce

- **Non dice che `CLAIM` implichi verita'.** Dice che ha superato anche un test
  fuori regime. Restano possibili termini fuori libreria che coincidono con la
  loro approssimazione su entrambi i regimi provati.
- **Non fissa quanto debba essere distante il secondo regime.** Nel blind 2 era
  un fattore 2, e il surrogato piu' facile ha rotto il gate di appena `1.2x`
  (0.0605 contro 0.05). Un surrogato ad ampiezza piu' piccola ci passerebbe
  sotto: il cancello **sposta** la classe di fallimento, non la chiude.
- **Non e' validata su PDE lineari**, dove la soluzione scala esattamente e il
  test fuori regime e' vacuo: li' `CLAIM` e `CLAIM_EFFETTIVO` non sono
  distinguibili dall'evidenza, e la distinzione resta formale.
- **Non riguarda dati reali.** Tutta l'evidenza e' su campi sintetici.

---

## 7. Emendamento 2026-09-03 — il limite di risoluzione dichiarato

**Origine:** `CLAIM_CARD_V13_UNBLINDING_2026-09-03.md` (14 claim di sotto-supporto su 423
opportunità) e `CLAIM_CARD_BLIND4_LIMITE_RISOLUZIONE_2026-09-03.md` (CONFIRMED su pannello
sigillato: 59 claim, 0 violazioni). **Adottato per decisione dell'utente il 2026-09-03.**

### 7.1 La regola
Ogni verdetto **assertivo** (`CLAIM`, `CLAIM_EFFETTIVO`) porta obbligatoriamente:

```
X        = 2 · ||A_S ĉ − b||₂ / ||b||₂          limite di risoluzione relativo
c_min(t) = 2 · ||A_S ĉ − b||₂ / ||A_t||₂        coefficiente minimo rilevabile, per ogni t ∉ S
```

Il fattore 2 è `FATTORE_IDENT`, già congelato; k=1 è stato **falsificato** allo Stage 1
(2 violazioni su 14). **Lettura:** «legge S con coefficienti ĉ, a meno di termini della libreria
con contributo relativo inferiore a X». Un CLAIM senza X è **incompleto** e non va citato.

### 7.2 Cosa cambia e cosa no
- **Nessun verdetto cambia.** L'annotazione è a valle dei cancelli e non li tocca (H3 asserita
  in codice e verificata: 0 verdetti cambiati su 120).
- **La definizione di claim falsa stretta non cambia**: supporto esatto, come nei blind 1-4.
  Le 14 della V13 e le 8 del blind-4 restano false strette nei loro scoring. La regola
  anti-riciclaggio (§3) vale anche qui: X non assolve campagne chiuse.
- **Cambia ciò che il sistema afferma**: da «questa è la legge» a «questa è la legge fino a X».
  Nel blind-4 X stava sopra il termine mancante in 8 casi su 8 (margine minimo 1,68×).

### 7.3 Confini dichiarati
- Copre solo termini **dentro la libreria**. Un termine fuori libreria (surrogato di Taylor)
  non ha `f_t`: resta materia del cancello di ampiezza e di `CLAIM_EFFETTIVO` (§2).
- Evidenza: **una** replica sigillata (59 claim, tasso di violazione ≤ 5 % per la regola del
  tre). Stato nel registry: `SUPPORTED`, non `VALIDATED`. Serve ≥ 150 claim per scendere
  sotto il 2 %.
- Misurato sul discoverer termico (ladder v2.1). Sulla pipeline PDE V1 la formula è identica
  e viene applicata (V1.1), ma la soundness lì **non è ancora misurata**.
