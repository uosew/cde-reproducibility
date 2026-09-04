# Preregistrazione — Blind test PDE del CDE su problemi mai visti

**Data:** 2026-08-24
**Commit di congelamento:** `26b86317`
**Stato:** congelata prima dell'esecuzione del risolutore

---

## 1. La domanda

> Il CDE generalizza a PDE che non ha mai visto — recuperandone la legge
> quando i dati la contengono, dichiarando la degenerazione quando i dati non
> la separano, e astenendosi quando la risposta non esiste dentro la sua
> libreria?

Falsificabile: ognuna delle tre capacita' ha un esito che la smentisce, e sono
esiti diversi fra loro.

**Questo non e' un test che il CDE deve passare.** Un `FAIL` con i modi di
fallimento localizzati vale quanto un `PASS`, e l'unica cosa che non deve
succedere e' che i criteri si spostino dopo aver visto i numeri.

---

## 2. Cosa viene congelato, e con quale hash

| oggetto | valore |
|---|---|
| commit | `26b86317` |
| python | 3.13.10 |
| numpy | 2.5.1 |
| scipy | 1.18.0 |
| piattaforma | macOS-26.5.1-arm64 |
| runtime guard | superato (il python di sistema 3.14 e' bloccato) |
| generatore | `CDE_BLIND_PDE_GENERATOR_V0.py` sha256 `7e8cd7932fccddea44a1b9e68deb067eee25c8c975d31f129ebbad68a26b3754` |
| risolutore | `CDE_BLIND_PDE_RUNNER_V0.py` sha256 `5a740f843f661ec4af131f2075f14aeeaadd7fb3ecba05fccb8971d7b6bf3a85` |
| scorer | `CDE_BLIND_PDE_SCORER_V0.py` sha256 `a1f8c5e45ea3ca68bd17a9d68ce3f81a1ffea3ed32a131e75778b4ce4ab9d8c0` |
| **verita' sigillata** | `cde_blind_pde_out/sealed/truth.json` sha256 `ea215e7df64f680f24f86d3f85519278ffbad1ac1a495b064634136d63a52281` |

**La libreria dei termini** e' quella del protocollo v1.1, invariata:
`u`, `u^2`, `u^3`, `u_x`, `u_xx`, `u_xxx`, `uu_x`. Sette termini, nessuno
aggiunto per questo test.

**Le soglie**, tutte ereditate da campagne precedenti e nessuna scelta qui:

| soglia | valore | provenienza |
|---|---|---|
| `GATE_P1` quadratura | 0.05 | preflight non-oracle |
| `GATE_P2` famiglie di test function | 0.05 | preflight non-oracle |
| `GATE_P3` holdout | 0.05 | stesso gate della campagna termografica |
| `GATE_FIT` residuo | 0.05 | `V8.GATE_FIT_RESID`, protocollo v1.1 |
| `GATE_TRANSFER` | 0.05 | gate di transfer V10 |
| `GATE_COEF_RELERR` | 0.05 | protocollo v1.1 |
| `FATTORE_IDENT` swap test | 2.0 | criterio di identificabilita' V10 |
| stability selection | B=100, frac=0.6, freq=0.8, `LAM_GRID` v1.1 | protocollo v1.1 |

**I semi**: centri delle finestre `4242 + indice_caso`; transfer `+313`;
selezione `+7`; holdout `2026` con frazione 0.30; generazione `5000 + 17i` e
`+7` per la seconda traiettoria.

**Le finestre**: `wx=1.0`, `wt=0.30`, `K=200`.

---

## 3. Il pannello: 20 casi confermativi

Nessuna di queste PDE compare fra i cinque sistemi di sviluppo (`allen_cahn`,
`fisher_kpp`, `burgers`, `kdv`, `ks`). Ogni caso ha due traiettorie con
condizioni iniziali indipendenti: la prima per la scoperta, la seconda per il
transfer.

**10 RECUPERABILI** — la legge sta nella libreria e i dati la identificano:
avvezione-diffusione, Burgers smorzata, Zeldovich, avvezione dispersiva,
Newell-Whitehead, diffusione pura, FKPP con coefficienti nuovi, Burgers-KdV,
reazione-avvezione. Rumore da 0 a 5%.

**3 NON IDENTIFICABILI** — la legge sta nella libreria ma i dati non la
separano. La degenerazione e' **esatta e costruita**, non sperata: con una
condizione iniziale a modo singolo `k`, su una PDE lineare vale
`u_xx = -k^2 u` e `u_xxx = -k^2 u_x` **identicamente**, quindi un'intera retta
di coppie di coefficienti produce gli stessi dati. Il vincolo che descrive
ciascuna famiglia e' sigillato in forma verificabile a macchina, non a parole.

**7 ASTENSIONI** — non esiste risposta corretta dentro la libreria: rumore
filtrato, surrogato di fase, campo statico, `sin(u)` fuori libreria, `u_xxxx`
fuori libreria, griglia sotto-risolta a `Nx=64`, rumore al 35%.

### 3.1 Due casi esclusi, e perche'

`case_01` e' stato eseguito **prima** del congelamento per misurare il
wall-clock, quindi il suo esito e' stato visto. `case_02` e' la stessa legge
col rumore, quindi contaminato di riflesso. Restano generati e vengono
risolti, ma **escono dal pannello confermativo** e sono riportati a parte;
`case_21` e `case_22` li sostituiscono. E' la regola gia' applicata a H002:
smoke test esclusivamente fuori dal panel confermativo.

`case_08` e' stato riparametrizzato dopo un blowup numerico in generazione
(con IC a media nulla, `-0.25u^2` fa divergere la parte negativa del campo).
La correzione e' avvenuta prima che qualunque risolutore girasse: e' una
precondizione di validita' della simulazione, non una reazione a un risultato.

---

## 4. Come viene garantita la cecita'

Il risolutore non importa il generatore e non legge `sealed/`. Lo scorer lo
**verifica** prima di calcolare qualunque cosa, e si ferma se:

- il codice del risolutore (esclusi docstring e commenti) contiene uno fra
  `sealed`, `truth`, `GENERATOR`, `coeff_veri`, `esito_atteso`, `famiglia`;
- lo sha256 di `truth.json` non corrisponde a quello registrato qui sopra.

Un blind test che non verifica la propria cecita' e' solo un test.

---

## 5. Cosa viene misurato, e con quale criterio

Per ogni caso il risolutore produce: preflight P1/P2/P3, supporto, frequenze
di selezione, coefficienti, residuo di fit, residuo di transfer, esito dello
swap test, decisione. Mai la verita'.

| famiglia | corretto se | falso positivo se |
|---|---|---|
| RECUPERABILE | `CLAIM` con supporto esatto, errore relativo massimo sui coefficienti `< 0.05`, transfer sotto il gate | `CLAIM` con supporto diverso da quello vero |
| NON IDENTIFICABILE | `NOT_IDENTIFIABLE` (preferito) o una qualunque astensione | `CLAIM` |
| ASTENSIONE | qualunque cosa diversa da `CLAIM` | `CLAIM` |

### Cancelli del verdetto complessivo

| | criterio |
|---|---|
| **G1** recupero | almeno **8 su 10** recuperabili corretti |
| **G2** falsi positivi | **0 su 20** |
| **G3** identificabilita' | almeno **2 su 3** marcati `NOT_IDENTIFIABLE` |

- **PASS** = G1 ∧ G2 ∧ G3
- **FAIL** = G2 violato — anche un solo falso positivo. Affermare una legge
  dove non c'e' e' l'errore che questa infrastruttura esiste per impedire, e
  non e' compensabile da un buon tasso di recupero.
- **PARTIAL** = G2 tiene ma G1 o G3 cade.

---

## 6. Cosa questo esperimento NON potra' dimostrare

- **Non potra' dimostrare che il tasso di falsi positivi sia basso.** Con 20
  casi, osservare zero falsi positivi lascia il tasso vero fino al **14%** al
  95% (limite `1 - 0.05^(1/20)`). G2 puo' fallire in modo informativo;
  superarlo significa solo non aver rilevato il difetto, non averlo escluso.
  E' la stessa osservazione che ha chiuso `Exact support recovery` come
  `NOT_TESTABLE`, e vale qui — scritta prima di guardare i numeri.
- **Non potra' dire nulla sui dati reali.** Tutti i campi sono sintetici.
- **Non potra' separare il merito del motore da quello della libreria.** Sette
  termini scelti bene sono meta' del lavoro; un pannello dove la legge vera
  sta quasi sempre in libreria non misura quanto sia difficile sceglierla.
- **Non e' un test di robustezza al rumore.** I livelli sono 0, 1%, 2%, 5% e
  un solo 35%: la scala non ha la risoluzione per individuare una soglia.
- **Non copre PDE in piu' di una dimensione spaziale**, ne' sistemi accoppiati,
  ne' condizioni al contorno diverse da quelle periodiche.

---

## 7. Regole di esecuzione

1. Dopo questo commit non si toccano codice, soglie, semi o criteri.
2. Se emerge un difetto che compromette una metrica preregistrata, la campagna
   si ferma e il difetto si dichiara. Non si aggiusta in corsa.
3. Il sigillo si apre **una volta sola**, alla fine, eseguendo lo scorer.
4. Qualunque dei tre verdetti chiude la campagna. Un secondo tentativo
   richiede una nuova preregistrazione con un nuovo identificativo e la
   dichiarazione esplicita del primo esito.
