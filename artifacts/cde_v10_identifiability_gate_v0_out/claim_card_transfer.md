# Claim card — riga `Transfer cross-traiettoria` della capability matrix V10

**Verdetto:** REJECTED

Rifiutata la formulazione universale — «tutte le claim vere trasferiscono» — che
il criterio `V_ITG2` impone come `n_pass == n_tot`. Non e' un limite di
misurabilita' come nel ciclo precedente: le celle che falliscono sono due,
identificate, e falliscono in modo deterministico e spiegabile.

La riga resta `PARTIAL`, ma il suo `23/25` non e' piu' un numero opaco: e' un
**inviluppo di rumore**.

| | |
|---|---|
| riga | `Transfer cross-traiettoria`, oggi `PARTIAL` |
| regola | `CDE_V10_CAPABILITY_MATRIX_V0.py:121` — `PARTIAL if not V_ITG2` |
| criterio | `CDE_V10_IDENTIFIABILITY_GATE_V0.py:317` — `V_ITG2 = (n_pass == n_tot)` |
| evidenza | `cde_v10_identifiability_gate_v0_out/results.json` |
| gate di transfer | `0.05` sul residuo, congelato prima |
| runtime | `.venv313`, Python 3.13.10, numpy 2.5.1, runtime guard superato |

---

## 1. Cosa affermerebbe la riga se fosse vera

> Una legge che il CDE dichiara vera su una traiettoria continua a valere su una
> **traiettoria indipendente**, con condizioni iniziali diverse: il residuo di
> transfer resta sotto il gate in **tutte** le celle.

`V_ITG1` — i sostituti falsi vengono catturati dal transfer — e' verificato, 4 su
4. E' `V_ITG2` a fallire: 23 celle su 25.

---

## 2. Il risultato: non un tasso, un inviluppo

Residuo di transfer per sistema e livello di rumore, gate `0.05`:

| sistema | σ=0.0 | σ=0.01 | σ=0.02 | σ=0.05 | σ=0.1 |
|---|---|---|---|---|---|
| **allen_cahn** | 0.0006 | 0.0221 | 0.0380 | **0.1126** | **0.2200** |
| fisher_kpp | 0.0001 | 0.0008 | 0.0015 | 0.0038 | 0.0091 |
| burgers | 0.0000 | 0.0011 | 0.0018 | 0.0045 | 0.0095 |
| kdv | 0.0001 | 0.0025 | 0.0048 | 0.0125 | 0.0260 |
| ks | 0.0000 | 0.0013 | 0.0029 | 0.0070 | 0.0150 |

| livello di rumore | celle che passano |
|---|---|
| σ ≤ 0.02 | **15 / 15** |
| σ = 0.05 | 4 / 5 |
| σ = 0.1 | 4 / 5 |

**Fino a σ = 0.02 il transfer vale senza eccezioni su tutti e cinque i sistemi.**
Oltre, l'unico che cede e' `allen_cahn`.

La degradazione e' **monotona e piu' che lineare** nel rumore, e attraversa il
gate fra σ=0.02 e σ=0.05. Non e' un incidente: e' una curva. E `allen_cahn` non
si comporta come gli altri fin dall'inizio — a σ=0.01 il suo residuo e' gia'
dieci volte quello di `fisher_kpp`, `burgers` e `ks`.

---

## 3. Perche' i due sistemi problematici falliscono per ragioni OPPOSTE

E' il risultato che nessuna delle due righe, da sola, mostrava. Lo swap test dice:

| sistema | `NOT_IDENTIFIABLE` |
|---|---|
| `fisher_kpp` | **a tutti e cinque i livelli di rumore** |
| `allen_cahn` | **a nessuno** |

**FKPP e' non identificabile ma trasferisce.** `corr(u², u³) = 0.995`: i termini
sono quasi collineari, quindi togliendone uno esiste davvero un sostituto
indistinguibile. I 4 falsi positivi documentati nella claim card di
`Exact support recovery` (`cde_v10_fdr_observability_v0_out/claim_card.md`) non
sono un errore del motore — sono **il motore che riconosce due modelli
equivalenti sui dati disponibili**. Il limite e' nei dati, non nel gate. E infatti
i suoi residui di transfer sono i piu' bassi del pannello.

**Allen-Cahn e' identificabile ma non trasferisce.** Nessuna ambiguita' fra
termini a nessun rumore; cede la **stabilita' dei coefficienti** stimati, che
sotto rumore non reggono il passaggio a una traiettoria nuova.

Sono due limiti distinti — collinearita' dei dati contro varianza di stima — e le
due righe della matrix li descrivevano separatamente senza collegarli. La
spiegazione del «perche' FKPP», lasciata aperta nel ciclo precedente, era gia' nel
repository: in un'altra riga.

---

## 4. Cosa questo NON dimostra

- **Non dimostra che il transfer di `allen_cahn` sia irrecuperabile.** Che sia
  varianza di stima e' l'interpretazione piu' naturale dei dati, non una
  conclusione testata. Un preconditioning diverso, piu' dati o una finestra
  temporale piu' lunga potrebbero spostare la soglia.
- **Non stabilisce dove sia esattamente la soglia.** Sappiamo che sta fra σ=0.02 e
  σ=0.05; i livelli intermedi non sono stati campionati.
- **Non dice che σ ≤ 0.02 sia un inviluppo sicuro in generale**: e' l'inviluppo
  osservato su **questi cinque sistemi**, con 15 celle. Un sesto sistema potrebbe
  cedere prima.
- **Non riguarda i dati reali.** Sul dataset di termografia pulsata il preflight
  chiude 10/10 e nessuna legge viene recuperata: li' non si arriva nemmeno a porsi
  la domanda del transfer.

---

## 5. La conseguenza operativa

Il `23/25` diventa una regola d'uso: **il CDE puo' dichiarare transfer verificato
fino a σ = 0.02 su tutti i sistemi del pannello; oltre, `allen_cahn` va marcato
come non trasferibile.** E' un'informazione utilizzabile, che il criterio
tutto-o-niente di `V_ITG2` comprimeva in un booleano falso.

Modificare `V_ITG2` perche' la riga diventi `SUPPORTED` sarebbe **cambiare la
soglia dopo aver visto i risultati**, ed e' vietato. Il criterio resta com'e'; a
cambiare e' cio' che sappiamo del perche' fallisce.

---

## 6. Nota sugli artefatti

Nessun esperimento eseguito: la chiusura avviene rileggendo evidenza gia' prodotta
e verificando cella per cella. Gli artefatti sono quattro invece di cinque —
analisi, claim card, voce di ledger, commit — e manca il runner perche' non c'era
nulla da eseguire. La replica dichiarata «da completare» nella riga resta tale:
non e' stata eseguita qui, e questo verdetto non ne dipende.

---

## 7. Ledger

| data | voce |
|---|---|
| 2026-08-24 | riga chiusa `REJECTED` per la formulazione universale di `V_ITG2` (25/25). Le due celle che falliscono sono `allen_cahn` a σ=0.05 (residuo 0.1126) e σ=0.1 (0.2200), gate 0.05, degradazione monotona. Inviluppo stabilito: 15/15 celle passano fino a σ=0.02. Collegamento cross-riga: `fisher_kpp` e' NOT_IDENTIFIABLE a tutti i sigma ma ha i residui di transfer piu' bassi; `allen_cahn` e' identificabile ovunque ma non trasferisce — collinearita' dei dati contro varianza di stima. Stato nella matrix invariato a `PARTIAL`. |
