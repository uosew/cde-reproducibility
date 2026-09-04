# Preregistrazione protocollo v2.0 — Campagna CDE V10 (Fase A)

Data: 2026-07-30. Autore: Valentino Berardi-Montesi (con Claude, LB Project).
Stato: **PREREGISTRATO PRIMA DI QUALUNQUE RUN V10**. Questo file viene
committato prima dell'implementazione; ogni modifica successiva al primo run
completo richiede un emendamento datato nel ledger in fondo.

Obiettivo: rispondere ai quattro punti deboli ad alta priorità della nota
arXiv v1 (preflight oracle circolare; libreria sempre contenuta; 2 soli seed;
gate calibrato su una separazione enorme) con evidenza sintetica assert-abile,
senza toccare la v1 congelata.

## 0. Core congelato e disciplina

- Il **core di selezione v1.1 resta congelato e identico**: stability
  selection B=100, sottocampioni 60%, freq ≥ 0.8, STLSQ su griglia
  λ ∈ {0.02, 0.05, 0.1, 0.2, 0.4} con BIC e supporto vuoto tra i candidati,
  refit sul supporto stabile, gate residuo fit < 5%, gate errore coefficienti
  < 5%, K = 200 finestre, finestre V8 1.0×0.30 (KS: 12×7.5). Fonte:
  `CDE_PDE_DISCOVERY_V8.py` (v1.1) e `CDE_KS_DISCOVERY_V9.py`, commit di
  riferimento congelato `8ecc3f85`.
- Ambienti: `.venv313` primario con runtime guard strict + evidence envelope;
  replica `.venv312` dove dichiarato. Python di sistema vietato.
- Ogni script V10 esegue prima uno **smoke test** preregistrato, poi la run
  completa. Artifact in `cde_v10_*_out/` (results.json + envelope), committati.
- Seed preregistrati: **multi-seed = 100..129** (30 seed); breakdown su
  **100..109**; i seed 7 e 11 (già usati in v1) sono esclusi dalle nuove
  statistiche e usati solo dove indicato (WLC, per pairing con la v1).

## 1. NOP — Preflight non-oracle v1 (`CDE_V10_NONORACLE_PREFLIGHT_V0.py`)

Sostituto del preflight oracle r_GT: decide se un dataset è adeguato
all'operatore **senza conoscere i coefficienti veri**.

Componenti (tutte calcolabili dai soli campioni):

- **P1 — Accordo di quadratura.** Feature deboli (A, b) calcolate con
  Simpson vs trapezio sulle stesse finestre.
  Metrica: `d_quad = ||b_S − b_T|| / ||b_S||` e il massimo analogo sulle
  colonne di A (normalizzate). Un dataset quadrature-limited (i due rifiuti
  storici) deve mostrare disaccordo elevato.
- **P2 — Accordo tra famiglie di test function.** Famiglia A = bump v1.1;
  famiglia B = bump con shape/esponente diverso, dichiarata nel codice prima
  del run. Metrica di cross-consistenza: `c_A = argmin ||A_A c − b_A||`
  (libreria piena, LS), poi `r_cross = ||A_B c_A − b_B|| / ||b_B||`, e
  simmetrico; si usa il massimo dei due.
- **P3 — Holdout predittivo sulle finestre.** Split preregistrato 70/30
  delle K finestre (rng dedicato, seed 2026). Fit LS libreria piena sul
  train; metrica `r_hold = ||A_hold c_train − b_hold|| / ||b_hold||`.
- **P4 — (diagnostica, non decisionale in v1)** residuo LS a risoluzione
  sottocampionata ×2, riportato ma escluso dalla decisione.

Decisione NOP: **OPEN** ⟺ P1 ≤ τ1 ∧ P2 ≤ τ2 ∧ P3 ≤ τ3.

**Calibrazione/valutazione (anti-circolarità).**
- Set di calibrazione: i 4 dataset V8 a σ=0, seed 7 (AC, FKPP, Burgers,
  KdV@Nx=1024) — tutti con decisione oracle nota OPEN. Le soglie sono
  fissate come `τ_i = M · max(metrica_i sul set di calibrazione)` con
  margine **M = 3** dichiarato qui, poi **congelate**.
- Set di valutazione (decisioni oracle note, mai usate per le soglie):
  1. KdV bassa risoluzione (Nx=512, la risoluzione "default" V7 alla quale
     il preflight oracle falliva storicamente con r_GT ~ 1e-2; generatore
     KdV V8 committato con solo Nx ridotto) → atteso REFUSE;
  2. KS a campionamento V8-standard (Nx=1024, frame 0.25, finestre 8×5,
     r_GT ~ 8e-2, rifiuto storico documentato in V9) → atteso REFUSE;
  3. KS full (Nx=2048, frame 0.1, finestre 12×7.5) → atteso OPEN;
  4. Burgers braccio FD4/RK45 (solver esterno) → atteso OPEN;
  5. Fisher–KPP braccio FD4/RK45 → atteso OPEN.
- **Criterio di successo (assert):** matrice di accordo NOP/oracle **5/5**
  sul set di valutazione, con i due rifiuti storici riprodotti. Un accordo
  parziale va riportato come tale (nessuna ricalibrazione post-hoc delle
  soglie: eventuali revisioni = NOP v2 con nuovo set di valutazione).

## 2. WLC — Wrong-library challenge (`CDE_V10_WRONG_LIBRARY_V0.py`)

Pipeline v1.1 identica; cambia solo la libreria candidata. Seed 7 (pairing
con v1). Esiti classificati per ogni run:
- `ABSTAIN_EMPTY`: supporto stabile vuoto (astensione);
- `ABSTAIN_GATE`: supporto non vuoto ma residuo ≥ 5% → nessuna claim;
- `FALSE_SUBSTITUTE`: supporto non vuoto e residuo < 5% → **claim errata**.

**2a. Leave-one-true-term-out.** Per ogni sistema, rimozione di un termine
vero alla volta dalla libreria: AC {u_xx, u, u^3}, FKPP {u_xx, u, u^2},
Burgers {u_xx, uu_x}, KdV {u_xxx, uu_x}, KS {u_xx, u_xxxx, uu_x} →
13 configurazioni × σ ∈ {0, 0.05} = **26 run**.
Metrica primaria: **structural FDR = #FALSE_SUBSTITUTE / 26**.
Ipotesi preregistrata H-WLC1: structural FDR = 0 (il gate residuo respinge i
fit monchi). Qualunque esito > 0 viene riportato integralmente.

**2b. Libreria sovradimensionata.** Termini extra fisicamente plausibili e
calcolabili dai soli campioni (forma debole senza derivate dei dati):
`u^4` (algebrico), `u_xxxx` (identità D4 già validata), `u_xxxxx`
(via (−1)^5 ∫ u ψ⁽⁵⁾, **richiede validazione identità D5 in stile track D4
PRIMA dell'uso** — gate componentwise preregistrato), `u^2·u_x`
(= (u^3)_x / 3 → −(1/3) ∫ u^3 ψ_x).
Libreria: v1.1 ∪ {u^4, u_xxxx, u_xxxxx, u^2 u_x} per i 4 sistemi V8;
TERMS9 ∪ {u^4, u_xxxxx, u^2 u_x} per KS. Ladder σ standard, seed 7 →
**25 celle**. Successo per cella: supporto esatto invariato + gate PASS.
Ipotesi H-WLC2: 0 termini spurii su 25 celle.

## 3. MS30 — Multi-seed e curva di breakdown (`CDE_V10_MULTISEED_V0.py`)

- **Ladder standard:** seed 100..129 × 5 sistemi × σ ∈ {0,1,2,5,10}%, con
  braccio nullo v1.1 (5 shuffle + 5 surrogate per sistema/seed) →
  **750 celle discovery + 1500 run nulli**.
- **Breakdown:** seed 100..109 × 5 sistemi × σ ∈ {15,20,30,40}% (solo
  discovery, senza nulli aggiuntivi) → 200 celle.
- Metriche preregistrate: recovery rate per (sistema, σ) con CI Wilson 95%;
  CI bootstrap percentile (10k ricampionamenti, rng seed 2026) su
  coef_rel_err_max; distribuzione di σ* (primo fallimento); FDR nulli
  aggregata con CI Clopper–Pearson 95%.
- Ipotesi preregistrate: **H-MS1** recovery 30/30 per ogni cella della
  ladder standard; **H-MS2** FDR nulli = 0/1500; **H-MS3** almeno un sistema
  mostra σ* ≤ 40% (curva di rottura osservabile); se nessuna rottura entro
  il 40%, si riporta "breakdown > 40%" senza estendere la scala post-hoc.
- Esecuzione: **checkpoint per-seed** su file con resume automatico (lezione
  OOM/exit-137), un seed in memoria alla volta, run notturna in background.
- Replica `.venv312`: seed 100..102 completi, attesa bit-identica.

## 4. DG — Gate distribuzionale (`CDE_V10_GATE_DISTRIBUTIONAL_V0.py`)

Analisi (candidata v2.1, **non applicata retroattivamente** alle claim):
- distribuzione empirica dei residui nulli MS30 (n=1500): min, p1, p5;
- P(residuo nullo < 0.05) con CI Clopper–Pearson; overlap con la
  distribuzione dei residui veri (max, p95, p99);
- proposta di gate percentile `g* = p1(nulli)/10` con analisi di
  sensibilità (fattori 2–20), riportata come raccomandazione per v2.1.

## 5. Ordine di esecuzione e criteri di stop

1. NOP (calibrazione → valutazione congelata) — se l'accordo è < 5/5 si
   riporta il disaccordo e si prosegue comunque con 2–4 (il NOP è additivo,
   non blocca la campagna).
2. WLC (validazione D5 → leave-one-out → overcomplete).
3. MS30 notturna con checkpoint; al termine DG.
4. Sintesi: `CDE_V10_SUMMARY_*.md` generata da script con assert, stile
   research note.

## 6. Ledger emendamenti

- **2026-07-30 (sera) — Addendum ITG (sezione 7).** Aggiunto DOPO aver
  visto: risultati WLC completi (structural FDR 4/26, tutti su Fisher–KPP,
  residui 3.8–4.9%; overcomplete 25/25), la sonda Allen–Cahn seed 100
  (gate residuo fallito a σ=10% con supporto esatto fino a 40%), e NESSUN
  risultato MS30 (campagna in corso, non consultata). L'addendum è
  ADDITIVO: nessuna soglia o ipotesi delle sezioni 1–4 viene modificata.
  H-WLC1 resta respinta e va riportata come tale (22/26 astensioni, 4/26
  false substitution concentrate su FKPP, con analisi causale della
  collinearità); H-MS1 verrà valutata nella formulazione originale senza
  reinterpretazioni post-hoc.
- **2026-07-30 (sera) — Distinzione σ*_claim / σ*_support.** Si dichiara
  PRIMA dell'aggregazione MS30: oltre a σ* (primo fallimento del gate,
  già definito), il report distinguerà σ*_support = primo σ con supporto
  NON esatto. Ipotesi (dalla sonda AC): σ*_claim < σ*_support — il
  breakdown epistemico (il protocollo smette di autorizzare la claim)
  precede il breakdown del supporto. Entrambi calcolabili dai checkpoint
  già registrati (campo support_exact), nessun re-run.

- **2026-07-30 (notte) — Estensioni additive DG e replica MS30.** Dichiarate
  PRIMA che DG o la replica girino e senza consultare i risultati MS30
  (1 solo seed completato, non letto): (a) DG riporterà, oltre alla
  sezione 4, la geometria delle CINQUE popolazioni di residui (claim vere,
  claim vere revocate dal gate, nulli, sostituti wrong-library, transfer
  failure ITG) e una mappa di trade-off tau -> (potenza sulla ladder
  standard, FDR nulli, detection dei sostituti) su griglia di soglie —
  nessuna soglia "ottima" viene adottata; (b) la replica MS30 su .venv312
  copre i seed 100..102 (breakdown incluso) in directory checkpoint
  separata (flag --replica312), confronto numerico campo-per-campo;
  (c) l'aggregazione MS30 riporterà sigma*_claim e sigma*_support come da
  emendamento precedente, ricalcolati dai checkpoint a fine campagna.

## 7. Addendum ITG — Identifiability & Transfer Gate (V10b)

Diagnosi dei 4 fallimenti WLC: su un campo liscio e quasi-stazionario
(FKPP, u∈(0,1) che rilassa verso 1) le colonne u² e u³ sono quasi
collineari SULLA TRAIETTORIA osservata: un sostituto può spiegare la
singola traiettoria sotto il 5%. Abbassare il gate all'1% respingerebbe i
sostituti ma anche discovery vere a rumore moderato: la risposta corretta
è un secondo asse, ortogonale al residuo di fit.

`CDE_V10_IDENTIFIABILITY_GATE_V0.py`:

- **T1 — Transfer cross-traiettoria.** Il modello claimed (coefficienti
  CONGELATI dal fit di training) viene valutato su una traiettoria NUOVA
  dello stesso sistema: (a) condizione iniziale indipendente (seed 23,
  stesso generatore committato), (b) per FKPP anche una traiettoria a
  bassa ampiezza (IC range (0.02, 0.30) — intervallo di u non presente
  nel training; copia parametrizzata del generatore V7 con fidelity
  assert). Rumore: stesso σ della cella. Metrica:
  `r_transfer = ||A'_S c_S − b'|| / ||b'||` sulle finestre della nuova
  traiettoria. Gate: r_transfer < 5% (stessa soglia del gate residuo,
  nessuna nuova soglia libera).
- **T2 — Diagnostica di identificabilità (riportata).** Sul training:
  matrice di correlazione delle colonne normalizzate (attesa:
  |corr(u²,u³)| su FKPP >> altri sistemi), κ(A_S), distinguibilità
  d_j = residuo di proiezione della colonna j sullo span delle altre.
- **T3 — Swap test (rilevatore NOT_IDENTIFIABLE).** Per ogni claim con
  libreria standard: per ogni j∈S, k∉S, refit di S\{j}∪{k}; se un
  supporto alternativo spiega anch'esso i dati sotto il 5%, l'esito
  corretto è `NOT_IDENTIFIABLE` (dichiarato, non scelto arbitrariamente).
  Aspettativa dichiarata: il swap test PUÒ flaggare la stessa FKPP vera
  come non identificabile a livello 5% sulla singola traiettoria — se
  accade, si riporta, ed è il transfer (T1) a rompere il pareggio.

Criteri di validazione preregistrati (assert nel summary):
- **V-ITG1:** tutti e 4 i FALSE_SUBSTITUTE di WLC falliscono T1
  (r_transfer ≥ 5%) su almeno una delle due traiettorie di transfer.
- **V-ITG2:** le 25 claim vere della v1 (4 sistemi × 5σ + KS × 5σ, seed 7,
  coefficienti dai results.json committati) passano TUTTE T1 sulla
  traiettoria different-seed (nessuna perdita di potenza).
- Esiti parziali → riportati integralmente, nessuna ricalibrazione.
