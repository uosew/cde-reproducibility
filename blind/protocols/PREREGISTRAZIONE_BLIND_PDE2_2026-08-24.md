# Preregistrazione — Blind PDE campagna 2: le due correzioni costano recuperi?

**Data:** 2026-08-24
**Commit di congelamento:** `80d55fd1`
**Primo tentativo citato:** `REPORT_BLIND_PDE_2026-08-24.md`, verdetto `FAIL`

---

## 1. La domanda

Il blind 1 ha prodotto due falsi positivi con meccanismi identificati. Due
correzioni li chiudono in teoria. La domanda **non** e' se li chiudano:

> Le due correzioni azzerano i falsi positivi **senza costare recuperi**?

Un cancello che elimina i falsi positivi rifiutando tutto e' inutile, e il
modo piu' facile di ingannarsi qui e' misurare solo la meta' che migliora. Per
questo il pannello contiene due **decoy**: campi quasi-degeneri ma
genuinamente identificabili, la cui risposta corretta resta `CLAIM`.

Il disegno e' un **confronto appaiato sullo stesso caso e sulle stesse
feature**: baseline (pipeline congelata della campagna 1, importata e non
riscritta) contro corretto (la stessa piu' i due cancelli). Nessun rumore di
semi fra i bracci.

---

## 2. Le due correzioni

**(a) Cancello di condizionamento.** Se due colonne della matrice di disegno
sono numericamente indistinguibili da collineari — `max|corr| >= 0.9999` — i
dati non separano le leggi, e la risposta e' `NOT_IDENTIFIABLE`. Agisce
**prima** della selezione: la degenerazione e' una proprieta' dei dati, non del
modello scelto. Sostituisce l'estensione dello swap test alle cardinalita'
vicine, che avrebbe scambiato falsi positivi con falsi negativi, perche' un
modello con un termine in meno e residuo di poco peggiore esiste quasi sempre.

**(b) Estrapolazione in ampiezza.** I coefficienti congelati sulla traiettoria
base devono reggere su una traiettoria ad ampiezza **doppia**. Una legge vera
ha coefficienti indipendenti dall'ampiezza; un surrogato di Taylor coincide a
piccola ampiezza e diverge a grande.

### 2.1 Cosa ha misurato lo stage 1, e cosa non ha risolto

Lo screening (`cde_blind_pde2_stage1_out/`, esito `PROMISING`) ha misurato:

| | ampiezza 1x | 2x | 3x |
|---|---|---|---|
| surrogato di `sin(u)` | 0.0082 | **0.263** | **1.368** |
| legge vera in libreria | 6.9e-05 | 1.2e-04 | 1.6e-04 |

Quattro ordini di grandezza di separazione gia' a 2x, con il **controllo** che
tiene — senza il controllo, un cancello che si rompe al crescere dell'ampiezza
misurerebbe la scala, non la verita' della legge.

Sul condizionamento lo stage 1 ha invece dato una **cattiva notizia**, che
questa preregistrazione recepisce invece di ignorare: un decoy genuinamente
identificabile con secondo modo di peso 0.01 da' `max|corr| = 0.999871`, contro
`1.000000` dei degeneri veri. Il margine e' `1.3e-04`, non un abisso. Da qui
due vincoli sul pannello, decisi prima di costruirlo:

1. i casi degeneri **devono includere rumore** (nel blind 1 erano tutti a
   rumore zero, dove la collinearita' resta esatta e il cancello ha vita
   facile);
2. il pannello **deve includere decoy**, perche' il costo del cancello sia
   misurato e non assunto.

---

## 3. Cosa e' congelato

| oggetto | valore |
|---|---|
| commit | `80d55fd1` |
| python / numpy / scipy | 3.13.10 / 2.5.1 / 1.18.0 |
| generatore | sha256 `b187ca4530559fed8256a6bf7d511cbfd3b0add9f2db7829ba60d9f1fda9f69f` |
| risolutore | sha256 `df6071bb124d13c27ac623763d2a195cead0cbf4a9ecdfda3bfa3d8dbceb0d32` |
| scorer | sha256 `88b258a167689caab1684e587045119877550a4dac9e69f44fbb5c8dd5850b02` |
| **verita' sigillata** | sha256 `793f77cd26199f22663e21da19fd78929a0d6e0f9263f3c5f541daa1387564c4` |

Libreria invariata (7 termini). Soglie **tutte ereditate** — `P1/P2/P3` 0.05,
fit 0.05, transfer 0.05, coefficienti 0.05, swap test 2.0, stability selection
B=100/frac=0.6/freq=0.8 — con **una sola novita'**: `SOGLIA_CORR = 0.9999`. Il
gate di ampiezza **non** introduce un numero nuovo: e' il gate di transfer
applicato a dati nuovi. Semi: centri `8484 + indice`, transfer `+313`,
ampiezza `+517`, selezione `+7`, holdout 2026/0.30. Griglia `Nx = 768`,
moltiplicatore di ampiezza 2.0.

---

## 4. Il pannello: 21 casi confermativi

Disgiunto dal pannello 1 **e** dalle sonde dello stage 1.

| famiglia | n | esito corretto |
|---|---|---|
| RECUPERABILE | 10 | `CLAIM` |
| DECOY (quasi degeneri ma identificabili) | 2 | `CLAIM` |
| NON IDENTIFICABILE (**2 con rumore**) | 4 | `NOT_IDENTIFIABLE` o astensione |
| SURROGATO (`sin(u)`, `tanh(u)`, `u_xxxx` fuori libreria) | 4 | astensione |
| CONTROLLO | 1 | astensione |

### 4.1 Casi esclusi e modifiche pre-congelamento, dichiarati

`case_21` (controllo di rumore) e' stato eseguito per misurare il wall-clock
prima del congelamento: esce dal pannello confermativo, come `case_01` nella
campagna 1. Entrambi i bracci vi hanno risposto `ABSTAIN_PREFLIGHT`.

`case_19` usava `exp(u)-1`, che **esplode in tempo finito** ad ampiezza
doppia — proprieta' dell'equazione, non errore numerico; un caso che non si
puo' estrapolare non serve a testare l'estrapolazione. Sostituito con
`tanh(u)`, limitata e con lo sviluppo `u - u^3/3` tutto in libreria.

Il controllo di risoluzione spettrale inizialmente bocciava il controllo di
rumore: era un difetto del controllo — un campo di rumore non ha una PDE da
risolvere — e ora si applica ai soli campi integrati.

`Nx` alzato da 512 a 768 perche' Burgers ad ampiezza doppia stava a un fattore
2 dal limite di risoluzione: un falso negativo su un recuperabile
corromperebbe l'endpoint primario.

---

## 5. Criteri, congelati

| famiglia | corretto se | falso positivo se |
|---|---|---|
| RECUPERABILE / DECOY | `CLAIM`, supporto esatto, err. coef. rel. max `< 0.05` | `CLAIM` con supporto diverso |
| NON IDENTIFICABILE | `NOT_IDENTIFIABLE` o astensione | `CLAIM` |
| SURROGATO / CONTROLLO | qualunque cosa diversa da `CLAIM` | `CLAIM` |

| cancello | criterio |
|---|---|
| **H1** primario | il braccio corretto ha **0 falsi positivi** E **recuperi ≥ baseline** |
| **H2** chiusura | nessun `CLAIM` del braccio corretto su non identificabili e surrogati |
| **H3** costo | **entrambi** i decoy restano `CLAIM` nel braccio corretto |

- **PASS** = H1 ∧ H2 ∧ H3
- **PARTIAL** = H1 vero ma H3 falso: le correzioni funzionano ma costano
- **FAIL** = H1 falso

---

## 6. Cosa questa campagna NON potra' dimostrare

- **Non potra' stabilire la non inferiorita' statistica.** Con 12 casi a esito
  `CLAIM` atteso, una regressione di un solo caso produce una coppia
  discordante: il test dei segni darebbe `p = 0.5`. L'endpoint e' un
  **confronto di conteggi con le discordanze elencate**, descrittivo, non un
  test di ipotesi. Intercetta una regressione grossolana, non una piccola.
- **Non potra' dimostrare che il tasso di falsi positivi sia basso.** Con 21
  casi, zero falsi positivi lascia il tasso vero fino al **13%** al 95%.
- **Non potra' generalizzare la soglia 0.9999.** Se regge qui, reggera' su
  degenerazioni di questo tipo e a questi livelli di rumore. Il margine
  misurato allo stage 1 e' `1.3e-04`.
- **Il gate di ampiezza e' vacuo sulle PDE lineari**, dove la soluzione scala
  esattamente: non puo' fallire e non porta informazione. Vale solo dove il
  termine fuori libreria e' nonlineare.
- **Richiede dati a piu' ampiezze**, condizione che un esperimento reale spesso
  non offre: la correzione e' meno trasportabile di quanto sembri.
- Nulla su dati reali, piu' dimensioni spaziali, condizioni al contorno non
  periodiche.

---

## 7. Regole di esecuzione

1. Dopo questo commit non si toccano codice, soglie, semi o criteri.
2. Se emerge un difetto che compromette una metrica preregistrata, la campagna
   si ferma e il difetto si dichiara.
3. Il sigillo si apre una volta sola, alla fine.
4. Qualunque verdetto chiude la campagna.
