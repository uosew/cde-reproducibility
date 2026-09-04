# Preregistrazione — CDE su dati sperimentali REALI (termografia pulsata)

**Data di congelamento: 2026-08-07.** Questo documento è congelato PRIMA di
qualunque esecuzione confermativa. Chiude — in un senso o nell'altro —
l'unica riga `NOT_TESTED` della capability matrix V10: *«Validazione su dati
sperimentali reali»*. La matrice non è stata rigenerata dopo le campagne
V11–V13, ma quella riga non è stata toccata da nessuna di esse.

Protocollo di riferimento: `PREREGISTRATION_PROTOCOL_V2_2026_07_30.md`
(ladder v2) e `EXPERIMENTAL_DESIGN_THERMAL_V0_2026_07_31.md` (design termico,
libreria emendata 2026-07-31). Il core di selezione v1.1 **non viene toccato**:
il runner reale sostituisce soltanto il generatore sintetico con un loader.

---

## 1. Dati

Dataset pubblico, misurato, di terze parti — nessuna misura è prodotta da noi.

- Fonte: *Thermal imagery from composite material academic samples*,
  Mendeley Data, DOI `10.17632/v4knrwgj9y.2`, licenza **CC BY 4.0**.
- Riferimento: Data in Brief, *Thermal imaging dataset from composite material
  academic samples inspected by pulsed thermography* (PMC7508994).
- Contenuto: 12 sequenze (6 piastre CFRP/GFRP 300×300×2 mm, ispezionate fronte
  e retro), 2000 frame 512×512 ciascuna, valori in **°C**, camera IR a 120 o
  145 Hz, eccitazione a flash.
- Integrità: ogni zip è verificato contro lo `sha256` pubblicato dall'API
  Mendeley; l'indice con gli hash è committato in
  `data_real_thermography/FILE_INDEX.json`. Gli hash entrano nell'evidence
  envelope.

### 1.1 Traiettoria di calibrazione (dichiarata, MAI confermativa)

`CFRP-006_facq-145Hz_s-Front_Img-2000.zip`
(`sha256 8775d8ad380074c1b7ba37ea933f59c6da282108d86d578f496d1b264aea2dee`).

È l'unica sequenza su cui è lecito guardare i dati prima del congelamento, ed è
stata usata soltanto per accertare formato, unità, istante del flash e
ampiezza del transiente. **Non entra in nessun braccio confermativo e non
contribuisce a nessun verdetto.** Osservazioni già fatte su di essa e qui
dichiarate: flash tra il frame 5 e il 10; media di piastra 35.7 °C al picco,
25.0 °C all'asintoto; deviazione standard spaziale da 2.85 a 0.29 °C.

### 1.2 Sequenze confermative

Le 10 sequenze rimanenti, escluse la calibrazione e la sua gemella di lato
(`CFRP-006_facq-120Hz_s-Back`), che è la stessa piastra fisica e quindi non
indipendente. Restano **10 sequenze su 5 piastre distinte** (CFRP-007, CFRP-008,
GFRP-006, GFRP-007, GFRP-008 × {Front 145 Hz, Back 120 Hz}).

---

## 2. Modello dichiarato e perché è chiuso in 1D

Variabile: `v(x,t) = T(x,t) − T_amb`, con `T_amb` la mediana del frame 1
(pre-flash) della sequenza, dichiarata per sequenza e non riadattata.

Dopo l'equilibratura attraverso lo spessore (2 mm), la dinamica residua di una
piastra sottile è la diffusione **nel piano** con perdita superficiale:

    v_t = α_∥ v_xx − β v

La finestra di analisi (§3) è scelta proprio per scartare il transiente in cui
la conduzione attraverso lo spessore domina e il modello 1D-in-x **non** è
chiuso. Se la scelta è sbagliata, il preflight o il gate residuo devono
rifiutare: è questo il test.

**Libreria congelata** (identica al design termico, tutta sample-only):

    {const, v, v², v_x, v_xx, v·v_x, (v v_x)_x}    con (v v_x)_x = ½(v²)_xx

Supporto atteso (dichiarato ORA, non è un oracle: non è noto al pipeline e non
entra in nessun gate): `{v, v_xx}`, con `α_∥ > 0` e coefficiente di `v`
negativo.

---

## 3. Parametri di analisi congelati

Ereditati dal protocollo V1 del dress rehearsal (`--v1`), riscalati alle
specifiche di questa camera. Nessuno è ottimizzato sui dati confermativi.

| Parametro | Valore congelato | Origine |
|---|---|---|
| Scala spaziale | 300 mm / 512 px = `5.859e-4 m/px` | geometria di piastra dichiarata nel dataset |
| Righe analizzate | 5 tagli 1D a `y = {128, 192, 256, 320, 384}` px | griglia fissa, nessuna selezione sui dati |
| Ritaglio ai bordi | scartati 40 px per lato lungo x | evita il bordo piastra e il vignetting |
| Finestra temporale | `[0.5 s, 8.0 s]` dopo il flash | scarta il transiente attraverso lo spessore e la coda in cui il segnale è sotto il rumore |
| Istante del flash | primo frame con `mean > mean(frame 1) + 2 °C` | regola, non ispezione |
| Binning temporale | ×5 | eredita `BIN` della variante V2 |
| Semi-larghezza finestre | `WX = 0.02 m` (34 px), `WT = 0.6 s` | ~⅓ della lunghezza di diffusione attesa nel piano sulla durata utile |
| Numero finestre | `K = 200` per taglio | eredita il rehearsal |
| Gate residuo di fit | `V8.GATE_FIT_RESID` (invariato) | ereditato, mai ricalibrato |
| Gate preflight | `P3 < 0.05` | ereditato |
| Criterio swap | alternativa entro `2×` il residuo base | ereditato dalla campagna primi |

---

## 4. Ipotesi e criteri di falsificazione

Ogni ipotesi ha un esito che la smentisce. Un `ABSTAIN` non è un fallimento del
protocollo: è un esito dichiarato in anticipo e verrà riportato come tale.

| ID | Ipotesi | Confermata se | Respinta se |
|---|---|---|---|
| **R-P1** | Il preflight non-oracle apre i dati reali alle specifiche di questa camera | `P3 < 0.05` in ≥ 8/10 sequenze | `P3 ≥ 0.05` in ≥ 3/10 |
| **R-S1** | Il supporto recuperato è `{v, v_xx}` | supporto esatto in ≥ 7/10 sequenze | supporto diverso in ≥ 4/10 |
| **R-S2** | Il segno è fisico: `coef(v_xx) > 0`, `coef(v) < 0` | in tutte le sequenze che superano il gate | anche una sola violazione |
| **R-T1** | Transfer reale tra sequenze: coefficienti congelati su una piastra reggono su un'altra dello stesso materiale | residuo di transfer sotto il gate in ≥ 6/10 coppie testate | ≥ 7/10 coppie oltre il gate |
| **R-N1** | I nulli non producono scoperte | 0 FD su shuffle temporale + surrogati di fase (10 sequenze × 2 nulli = 20) | ≥ 1 FD |
| **R-I1** | Il supporto è identificabile sui dati reali | nessuna alternativa entro 2× in ≥ 7/10 | alternative in ≥ 4/10 |
| **R-M1** | Coerenza di materiale: `α_∥` stimato è più simile tra piastre dello stesso materiale che tra materiali diversi | separazione CFRP/GFRP visibile | nessuna separazione |

### Esiti dichiarati come legittimi

- **CLAIM**: R-P1, R-S1, R-S2, R-N1, R-I1 confermate → prima legge recuperata
  da dati misurati; la riga della capability matrix passa a `SUPPORTED`.
- **ABSTAIN**: il preflight apre ma il gate residuo non è superato → i dati
  reali non contengono informazione sufficiente per la libreria dichiarata.
  La riga passa a `PARTIAL` con l'astensione documentata.
- **REJECTED**: il preflight chiude → i dati sono inadeguati alla risoluzione
  richiesta. La riga resta `NOT_TESTED` ma con un limite quantificato.
- **NOT_IDENTIFIABLE**: supporto trovato ma alternative entro 2× → esito
  corretto e riportato come tale.

Qualunque di questi quattro esiti chiude la campagna. **Non è ammesso**
riaggiustare finestre, ritagli o soglie dopo aver visto i risultati
confermativi: un secondo tentativo richiede una nuova preregistrazione con un
nuovo identificativo e la dichiarazione esplicita del primo esito.

---

## 5. Claim vietati

Anche in caso di CLAIM, restano vietati:

- qualunque affermazione sulla diffusività dei materiali oltre le piastre
  misurate (5 piastre, 2 materiali, un solo laboratorio, una sola camera);
- l'uso di `α_∥` come misura metrologica: la scala px→m è dichiarata dalla
  geometria nominale della piastra, non calibrata da noi, e la piastra CFRP è
  anisotropa nel piano secondo il layup, che il dataset non specifica. Il
  confronto con valori tabulati è **solo report, mai gate**;
- qualunque claim sulla rilevazione di difetti: i tagli 1D sono su griglia
  fissa e possono attraversare inserti; la loro presenza è una sorgente di
  eterogeneità dichiarata, non un oggetto di studio;
- qualunque estensione a geometrie, spessori o regimi di eccitazione diversi.

---

## 6. Ambiente e riproducibilità

- Interprete: `.venv313/bin/python` (3.13.10, numpy 2.5.1), matrice certificata;
  replica su `.venv312` (3.12.12, numpy 2.5.1) obbligatoria prima del verdetto.
- Il runtime guard (canary elisione numpy) deve passare: l'incidente
  py3.14 + numpy 2.2.6 resta in quarantena, cfr.
  `QUARANTENA_NUMPY_ELISION_2026_07_28.md`.
- Evidence envelope con hash dei risultati e degli zip sorgente; verdetto
  riconciliato in `CDE_DISCOVERY_LEDGER.md` via `CDE_LEDGER_RECONCILE.py`.
- Runner: `CDE_REAL_THERMOGRAPHY_V0.py`, che importa il core esistente senza
  modificarlo. Ogni divergenza dal core sarebbe una violazione di questa
  preregistrazione.
