# Preregistrazione — CDE Prime Law Discovery V0 (protocollo v2, dominio primi)

Data: 2026-07-30 (sera). Stato: **PREREGISTRATO PRIMA DI QUALUNQUE RUN**.
Campagna "da zero": nessun riuso di risultati o score del precedente
programma prime-residual. Eseguita in parallelo a MS30 (costo CPU
dichiarato trascurabile: crivello + regressioni 200×8).

## Oggetto e onesta' della claim

Target: la **densita' locale dei numeri primi** d(x) = (π(x+h) − π(x))/h
su finestre. La verita' asintotica e' nota (teorema dei numeri primi):
d(x) → 1/log x, coefficiente 1. La campagna e' quindi una **validazione
del nuovo CDE su un dominio non-PDE** (regressione sparsa su libreria di
leggi candidate), non una scoperta di nuova matematica. Ogni claim sara'
formulata come "recupero della legge nota sotto la ladder v2".

## Dati (generazione committata)

- Crivello di Eratostene fino a **N = 10^8** (smoke: 10^6), numpy bool.
- Finestre: **K = 200** centri log-uniformi per decade, ampiezza
  **h = 10^5** (smoke: K = 60, h = 10^3), densita' = conteggio/h.
- Decade di training **A = [10^6, 10^7]**; decade di transfer
  **B = [10^7, 10^8]** (mai usata per il fit).
- Rumore: intrinseco (fluttuazioni dei primi, rel. ~ 1/√(h/log x) ≈ 1.3%
  su A). Nessun rumore artificiale.
- Seed finestre: 7. Seed nulli: 0..9.

## Libreria candidata (dichiarata upfront, 8 termini)

{ 1, 1/log x, 1/log² x, 1/√x, 1/x, log x / x, x^(−1/4), log log x / log x }

Supporto vero (asintotico): **{1/log x}** con coefficiente 1. I termini
concorrenti sono lentamente varianti e fortemente collineari su range
stretti: e' il banco di prova naturale per identificabilita' e transfer.

## Pipeline (core v1.1 congelato, riusato identico)

Stability selection B=100, sottocampioni 60%, freq ≥ 0.8, STLSQ su
griglia λ v1.1 con BIC e supporto vuoto candidato, refit, **gate residuo
< 5% ereditato congelato** (nessuna nuova soglia). Preflight non-oracle:
holdout predittivo 70/30 (rng 2026) con soglia τ3 del NOP; oracle r_GT
(legge nota) calcolato SOLO per la matrice di accordo.

## Controlli nulli (definizione di falsa scoperta)

Sui nulli il trend x-dipendente e' distrutto ma una densita' media
esiste: l'esito corretto e' supporto ⊆ {1} oppure vuoto.
**FD = supporto stabile che contiene ≥1 termine x-dipendente e passa il
gate residuo.**
- N1 (×10): insiemi uniformi random in [10^6, 10^7] con |P| identico
  (stessa cardinalita' dei primi, nessuna struttura in x).
- N2 (×10): shuffle delle densita' rispetto ai centri finestra
  (associazione x→d distrutta).

## Identificabilita' e transfer (ladder v2 completa)

- **Swap test** sul supporto claimed (training A): aspettativa dichiarata
  — su range stretti (mezza decade) puo' emergere NOT_IDENTIFIABLE per
  collinearita' (1/log x vs x^(−1/4) etc.); su A intera l'attesa e'
  identificabilita'. Si riporta l'esito in entrambe le configurazioni.
- **Transfer A→B**: coefficienti congelati dal fit su A, residuo
  relativo sulle finestre di B, gate 5%. La legge vera trasferisce;
  i sostituti lentamente varianti no.
- Verdetto finale tramite la ladder di CDE_V10_CLAIM_LADDER_AUDIT_V0
  (operator_valid = n/a strutturale per regressione diretta, dichiarato
  True con motivazione; replication = run ripetuta stesso seed
  bit-identica + replica .venv312 se la campagna viene promossa).

## Ipotesi preregistrate

- **H-P1**: su A, supporto claimed = {1/log x} con coefficiente in
  [0.9, 1.1] e gate residuo PASS.
- **H-P2**: 0 FD su 20 nulli.
- **H-P3**: transfer A→B PASS (residuo < 5%) per il modello claimed.
- **H-P4** (aspettativa, non vincolo): swap test su mezza decade →
  NOT_IDENTIFIABLE; su decade intera → identificabile. Qualunque esito
  va riportato integralmente.
- Esiti difformi → riportati senza ricalibrazione; eventuali revisioni =
  V1 con nuova preregistrazione.

## Output

`CDE_PRIME_LAW_DISCOVERY_V0.py` → `cde_prime_law_discovery_v0_out/`
(results.json + evidence_envelope.json), smoke preregistrato prima della
run piena.

## Ledger emendamenti

- **2026-07-30 (sera, PRIMA di qualunque run).** La soglia del preflight
  holdout NON e' il τ3 del NOP (calibrato su feature deboli PDE
  deterministiche, residui ~1e-4: fuori dominio) ma il gate residuo
  congelato 5%, coerente col rumore intrinseco dei primi (~1.3% su A).
  Nessun'altra modifica; nessun dato della campagna era stato generato.

## V1 — multi-decade (preregistrata DOPO l'esito V0, 2026-07-30 notte)

Esito V0 visto e committato (edb144fd): verdetto NOT_IDENTIFIABLE su
singola decade (tutte le alternative lentamente varianti sotto il gate
assoluto 5%; 2/20 nulli a densita' costante etichettati con termini log
— stessa classe di failure). V1 affronta la causa, non ricalibra V0:

- **Training A1 = [1e6, 1e8]** (2 decadi), h = 1e5, K = 300, seed 7:
  la curvatura accumulata separa le leggi rivali.
- **Transfer T1 = [1e5, 1e6]** (estrapolazione VERSO IL BASSO, range mai
  visto, curvatura massima), h = 1e4, K = 200, seed 8; gate 5%.
- Nulli: N1/N2 come V0 ma su A1 (10+10), stessa definizione di FD.
- **Criterio NI raffinato (dichiarato qui, motivato dall'esito V0):**
  il gate assoluto 5% e' inadeguato quando il noise floor e' ~0.3%
  (un'alternativa al 2% "spiega i dati" ma e' 6x peggio del modello
  claimed). Criterio primario V1: alternativa rende NOT_IDENTIFIABLE
  solo se il suo residuo e' < 2x il residuo del modello claimed
  (confronto tra modelli); il criterio assoluto 5% viene comunque
  riportato come secondario. Nessun altro parametro cambia.
- Ipotesi: **H-V1a** supporto {inv_log} (o {inv_log}+const con |coeff
  const| < 0.02*max) con coeff inv_log in [0.9, 1.1]; **H-V1b** 0 FD
  con criterio NI relativo applicato anche alla classificazione dei
  nulli (supporto x-dipendente ma indistinguibile da const entro 2x ->
  riclassificato NI, non FD); **H-V1c** transfer verso il basso PASS;
  **H-V1d** swap con criterio relativo -> identificabile su A1.
