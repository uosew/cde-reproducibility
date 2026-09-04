# Preregistrazione — Blind Challenge V1 + envelope combinato + sweep A

Data: 2026-07-31. Stato: **PREREGISTRATO PRIMA DI QUALUNQUE RUN V1**.
La V0 resta intatta (truth set, verdetti, scoring, report: nessuna
modifica retroattiva). La V1 risponde ai tre difetti architetturali
emersi: (1) preflight che conflaziona dati/modello; (2) envelope
single-axis insufficiente sotto degradazioni congiunte; (3) frontiera
di identificabilita' della diffusione pura ignota.

## 1. Ladder v2.1 — split del preflight (verdetto MISSPECIFIED)

Nuovo ordine dei livelli (`CDE_V11_BLIND_DISCOVERER_V1.py`):

  operator_valid -> data_adequacy -> library_adequacy -> support_stable
  -> fit_gate -> transfer_gate -> identifiability_gate -> replication

- **data_adequacy** (SOLO qualita' numerica dei dati): P1 (accordo
  quadratura) <= tau1 e P2' <= tau2, dove P2' = |r_bumpA - r_bumpB| /
  max(r_bumpA, r_bumpB) e' il DISACCORDO RELATIVO tra famiglie di test
  function (insensibile all'adeguatezza del modello, a differenza del
  P2 assoluto della V0). Fallimento -> REJECTED_PREFLIGHT.
- **library_adequacy**: holdout predittivo full-library r_hold < 5%
  (gate ereditato). Fallimento CON dati sani -> **MISSPECIFIED**
  (verdetto di primo livello: "nessun modello della libreria spiega
  dati numericamente adeguati"; per i nulli e' l'esito naturale e
  conta come rifiuto corretto).
- Livelli successivi invariati (v1.1 core, transfer, swap relativo 2x).

Calibrazione tau1/tau2: sui 10 dataset NON-blind del dress rehearsal V2
GO (rigenerati deterministicamente dal codice committato b084b084),
tau = 3x il massimo osservato, congelate prima della run blind.

## 2. Run V1 sul dataset sigillato V0

Stessi cases/*.npz e sealed/truth.json (sigillo gia' committato
4c2a0e3e, hash invariato). Output: verdicts_v1.json (committato prima
dell'unblinding V1), unblinding_report_v1.json.

Scoring V1 (denominatori separati, dichiarati ORA):
- G1 zero false claim (invariato: CLAIM su non-rappresentabile/nullo o
  supporto errato). G4 zero CLAIM sui nulli. G5 err mediano < 5%.
  G6 holdout >= 90% delle claim vere.
- **G2' recovery rappresentabili** = CLAIM esatte / (rappresentabili
  con data_adequacy PASS); target >= 90%.
- **G3' misspec detection** = (MISSPECIFIED o NI o ABSTAIN o
  REJECTED_TRANSFER) / non-rappresentabili; target >= 90%.
- **G8 preflight false rejection** = REJECTED_PREFLIGHT sui
  rappresentabili / rappresentabili; target <= 10%.
- **G9 MISSPECIFIED precision** (frazione dei verdetti MISSPECIFIED che
  sono davvero non-rappresentabili o nulli) >= 80%; **recall** su
  D/E/G/I riportato (target esplorativo >= 60%).
- Potenza riportata SEPARATAMENTE per classe (A, B, C, F e fuori
  libreria); esiti difformi riportati integralmente.

## 3. Envelope combinato (`CDE_V11_COMBINED_ENVELOPE_V0.py`)

Assi interagenti dalla V0: moto M {0, 0.25, 0.5}, nonunif U {0, 0.015,
0.03}, deriva R {0, 0.5, 1.0}, dead D {0, 0.02, 0.05}. Tutte le 6
coppie in griglia 3x3 (54 config) + 2 triple (M,U,R) a (mid,mid,mid) e
(max,max,max). Base = spec V11; pipeline pooled; per ogni config si
registrano verdetto e limite violato (claim-limit vs preflight-limit).
Superficie di accettazione = config con CLAIM & err(alpha)<5%; envelope
operativo = superficie con margine 2x per coordinata. Regola congelata.

## 4. Sweep classe A (`CDE_V11_CLASSA_SWEEP_V0.py`)

Base: alpha = 9.7e-5, beta = 0, camera = spec base V11. OFAT + coppie
selezionate (14 config congelate): ampiezza IC x{1,2}; n_traiettorie
{5,8}; finestra temporale {[10,70],[10,110]} s; WX {0.08,0.12} m; NETD
{0.1,0.3}; beta {0, 0.005} (una piccola perdita AIUTA
l'identificabilita'? — ipotesi dalla V0: B 9/10 vs A 2/10); coppie
(ampiezza2+WX0.12), (durata110+n8). Obiettivo dichiarato: descrivere la
frontiera di identificabilita' di A, non farla passare a tutti i costi.

## Ledger emendamenti

- **2026-07-31 (sera) — LADDER v2.1 CONGELATA.** Decisione presa DOPO la
  lettura congiunta di envelope combinato (bcc90b8e: 43/56 CLAIM,
  frontiera identificabilita' = deriva 1.0C e moto>=0.25px combinato
  con deriva>=0.5) e sweep A (b5da724e: floor sistematico, alpha
  accurato 0.1-1% nonostante residuo 12-15%). La v2.1 resta valida nel
  comportamento conservativo (zero claim indebite in tutto il
  programma); la tassonomia diagnostica e' dichiaratamente incompleta:
  su campi a eccitazione insufficiente emette MISSPECIFIED dove la
  categoria semanticamente corretta e' INSUFFICIENT_EXCITATION.
  Nessuna riclassificazione retroattiva. Il verdetto
  INSUFFICIENT_EXCITATION (discriminatore candidato: coerenza dei
  coefficienti tra traiettorie nonostante residuo alto) e la regione
  operativa combinata nel preflight sono rimandati alla ladder v2.2,
  da validare alla cieca con Blind Challenge V2 sotto NUOVA
  preregistrazione.
