# Blind PDE campagna 2 — le due correzioni chiudono i falsi positivi a costo zero

**Verdetto:** PASS

Su un pannello nuovo e disgiunto, il braccio corretto azzera i falsi positivi
del baseline — **4 → 0** — mantenendo **tutti e 12** i recuperi e **entrambi**
i decoy. H1, H2 e H3 superati.

Il risultato e' vero e va preso con una riserva precisa: **entrambi i cancelli
nuovi hanno superato il loro caso piu' difficile con un margine sottile**, molto
piu' sottile di quanto lo screening dello stage 1 lasciasse prevedere. La
sezione §4 quantifica quanto.

| | |
|---|---|
| preregistrazione | `PREREGISTRAZIONE_BLIND_PDE2_2026-08-24.md`, commit `38eb97e5` |
| verita' sigillata | sha256 `793f77cd…387564c4`, **intatta** |
| cecita' del risolutore | **verificata** a macchina |
| runtime | `.venv313`, Python 3.13.10, numpy 2.5.1 |
| disegno | appaiato, stesse feature per i due bracci |
| wall-clock | 770 s |

---

## 1. Il risultato

| metrica | baseline | corretto |
|---|---|---|
| recuperi corretti | 12 / 12 | **12 / 12** |
| **falsi positivi** | **4** | **0** |
| flag di identificabilita' | 2 / 4 | **4 / 4** |
| astensioni corrette | 3 / 6 | **6 / 6** |
| decoy mantenuti | 2 / 2 | **2 / 2** |

| cancello | criterio | esito |
|---|---|---|
| H1 primario | 0 falsi positivi **e** recuperi ≥ baseline | **superato** |
| H2 chiusura | nessun `CLAIM` su degeneri e surrogati | **superato** |
| H3 costo | entrambi i decoy restano `CLAIM` | **superato** |

**Cinque discordanze, tutte nella direzione giusta**, nessuna nell'altra.

---

## 2. Il baseline ha replicato i suoi fallimenti su dati nuovi

E' il controllo che rende leggibile tutto il resto. La pipeline della campagna
1, su un pannello che non aveva mai visto, ha prodotto **gli stessi due modi di
fallimento**:

| caso | famiglia | baseline | modo |
|---|---|---|---|
| case_11 | degenere `k=2` | `CLAIM` | ha affermato un membro della famiglia degenere |
| case_17 | `sin(u)` fuori libreria | `CLAIM` | ha affermato una legge dove non ce n'e' |
| case_18 | `sin(u)` fuori libreria | `CLAIM` | idem |
| case_19 | `tanh(u)` fuori libreria | `CLAIM` | idem |

I fallimenti del blind 1 non erano artefatti di quel pannello: **si
riproducono**, su leggi diverse e con coefficienti diversi. Il `tanh` mostra
che il fenomeno non riguarda `sin(u)` ma qualunque nonlinearita' il cui
sviluppo di Taylor cada in libreria.

---

## 3. Cosa ha fatto ciascun cancello

### 3.1 Condizionamento — e il rumore non lo ha rotto

Il rischio che avevo registrato prima di costruire il pannello era che la
collinearita' restasse esatta solo sui dati puliti. **Non si e' verificato** a
questi livelli di rumore:

| caso | σ | `max\|corr\|` | decisione |
|---|---|---|---|
| case_11 | 0 | 1.0000000 | `NOT_IDENTIFIABLE` |
| case_14 | 0 | 1.0000000 | `NOT_IDENTIFIABLE` |
| **case_12** | **0.01** | **0.99999973** | `NOT_IDENTIFIABLE` |
| **case_13** | **0.02** | **0.99999984** | `NOT_IDENTIFIABLE` |

Il rumore erode la collinearita' di circa `3e-07`: nulla, rispetto alla soglia.

Il cancello ha anche migliorato un caso che il baseline aveva gia' contato come
corretto: `case_13`, dove il baseline si astiene con **supporto vuoto** — cioe'
non trova nulla — mentre il braccio corretto dichiara `NOT_IDENTIFIABLE`, che
e' la ragione giusta. Stesso punteggio, informazione diversa.

### 3.2 Estrapolazione in ampiezza

| caso | transfer normale | **ampiezza 2x** | gate |
|---|---|---|---|
| case_17 `sin(u)` | 0.0066 | **0.0605** | 0.05 |
| case_18 `sin(u)` | 0.0100 | **0.2870** | 0.05 |
| case_19 `tanh(u)` | 0.0213 | **0.3814** | 0.05 |

Tutti e tre passavano il transfer ordinario di un ordine di grandezza e sono
stati fermati solo dall'ampiezza. `case_20` (`u_xxxx` fuori libreria) non ha
mai raggiunto questo cancello: il preflight lo chiude prima, in entrambi i
bracci — quindi **solo 3 dei 4 surrogati hanno effettivamente messo alla prova
il cancello nuovo**.

---

## 4. La riserva: due margini sottili

Qui il report si discosta dall'ottimismo che i conteggi suggerirebbero.

**Il decoy piu' difficile ha evitato il cancello per `2.2e-05`.**

| | `max\|corr\|` | distanza dalla soglia 0.9999 |
|---|---|---|
| degenere con rumore (case_12) | 0.99999973 | +9.97e-05 sopra |
| **decoy case_16** | **0.99987813** | **−2.19e-05 sotto** |
| decoy case_15 | 0.99878562 | −1.1e-03 sotto |

La soglia vive in una finestra larga circa `1.2e-04`, e il decoy piu' ostile ci
sta dentro a un quinto di quella distanza. Ha funzionato; non ha molto spazio.

**Il surrogato piu' facile ha rotto il gate di appena 1.2×.** `case_17` da'
`0.0605` contro `0.05`. Il peggior recuperabile a doppia ampiezza da' `0.0091`
(`case_10`). La separazione reale fra «legge vera a 2x» e «surrogato a 2x» su
questo pannello e' quindi un **fattore 6.6** — non i quattro ordini di
grandezza misurati dallo stage 1, che aveva usato una sonda piu' favorevole.
**Lo screening ha sovrastimato la separazione**, ed e' una lezione sul valore
probatorio di uno stage 1: dice se un discriminante esiste, non quanto sia
robusto.

Un surrogato con ampiezza ancora piu' piccola, o una nonlinearita' piu' vicina
al suo troncamento, cadrebbe sotto il gate. **Il cancello non chiude la classe
di fallimento: la sposta.**

---

## 5. Cosa questa campagna NON dimostra

- **Non dimostra che il tasso di falsi positivi sia nullo.** Con 21 casi, zero
  falsi positivi lascia il tasso vero fino al **13,3%** al 95%.
- **Non dimostra la non inferiorita' statistica** del braccio corretto: con 12
  casi a `CLAIM` atteso e zero discordanze sfavorevoli, il disegno intercetta
  una regressione grossolana, non una piccola. Era dichiarato prima della run.
- **Non generalizza la soglia 0.9999**, che qui ha un margine di `2.2e-05` sul
  caso peggiore.
- **Il gate di ampiezza e' vacuo sulle PDE lineari**, dove la soluzione scala
  esattamente, e richiede dati a piu' ampiezze: in un esperimento reale spesso
  non esistono.
- Nulla su dati reali, piu' dimensioni spaziali, condizioni al contorno non
  periodiche.

---

## 6. Una discrepanza fra preregistrazione e scorer, dichiarata

La preregistrazione §4 escludeva `case_21` dal pannello confermativo (era
servito al pilota di costo), fissando il pannello a 21 casi. **Lo scorer ne ha
contati 22**, includendolo: e' una svista di implementazione, non una scelta
fatta dopo i risultati.

Effetto misurato: `case_21` e' un controllo di rumore su cui **entrambi i
bracci rispondono `ABSTAIN_PREFLIGHT`**. Escluderlo porta le astensioni
corrette da 6/6 a 5/5 nel braccio corretto e da 3/6 a 2/5 nel baseline, e
**non tocca H1, H2 ne' H3**. Il verdetto e' invariante rispetto alla
discrepanza. Le tabelle qui sopra riportano i conteggi dello scorer, su 22.

---

## 7. Ledger

| data | voce |
|---|---|
| 2026-08-24 | Blind PDE campagna 2, confronto appaiato su pannello disgiunto, verdetto **PASS**. Baseline 12/12 recuperi con **4 falsi positivi**; corretto 12/12 recuperi con **0 falsi positivi**, 4/4 flag di identificabilita', 2/2 decoy mantenuti. H1, H2, H3 superati; 5 discordanze, tutte favorevoli. Il baseline ha **replicato su dati nuovi** entrambi i modi di fallimento del blind 1, incluso su `tanh(u)`: il fenomeno non riguarda `sin(u)` ma qualunque nonlinearita' con sviluppo di Taylor in libreria. Il cancello di condizionamento non e' stato rotto dal rumore (degeneri a σ=0.01 e 0.02 danno max-corr 0.99999973 e 0.99999984). **Riserva quantificata**: il decoy piu' ostile sta 2.19e-05 sotto la soglia 0.9999, e il surrogato piu' facile rompe il gate di ampiezza di appena 1.2x (0.0605 contro 0.05) contro un peggior recuperabile a 0.0091 — separazione di fattore 6.6, non i 4 ordini di grandezza dello stage 1, che aveva usato una sonda piu' favorevole. Il cancello sposta la classe di fallimento, non la chiude. Dichiarata una discrepanza: lo scorer ha contato 22 casi invece dei 21 preregistrati (incluso `case_21`, escluso perche' usato nel pilota di costo); entrambi i bracci vi si astengono al preflight e il verdetto e' invariante. Cecita' verificata, sigillo intatto, nessuna soglia modificata dopo l'esito. |
