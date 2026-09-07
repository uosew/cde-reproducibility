# Claim card — seconda implementazione indipendente sulle stesse feature deboli

**Prereg:** `PREREGISTRAZIONE_BASELINE_INDIPENDENTE_JULIA_2026-09-07.md`, sha256 `e29c3316bfab89d4…`,
commit `eaba0001`, prima dell'installazione di Julia e dell'export. Emendamento §1-a (politica
sui nulli appaiata con PySINDy) dichiarato mentre l'export era in corso, prima di ogni risultato
(`c6c02313`). **Artefatti:** `cde_feature_export_out/` (60 matrici, manifesto con sha256),
`julia_baseline/{run_dde.jl,risultati_dde.json,scoring.json}`. Scorer con 8 mutation test mordenti.

## Verdetto: **CLASSE**

Il fallimento su campi nulli **non è di PySINDy: è della classe di metodi.**

| | DataDrivenSparse `STLSQ` (Julia) | PySINDy `STLSQ` (Python) |
|---|---|---|
| nulli rivendicati, politica appaiata | **40 / 40** | 40 / 40 |
| nulli rivendicati, **col nostro cancello** | **0 / 40** | 0 / 40 (riportato nella nota) |
| celle vere a supporto esatto | **20 / 20** | 14 / 20 |
| errori / celle non confrontabili | 0 | — |

**Ambiente:** Julia 1.12.7, `DataDrivenSparse` (SciML, MIT), matrici di disegno prodotte dal
motore congelato `CDE_PDE_DISCOVERY_V8` con seme 7 e i semi dei nulli già dichiarati. Unica
variabile: la regola di selezione. Via di chiamata **scoperta da una sonda** su un problema a
soluzione nota (`julia_baseline/probe_api.jl`), non indovinata.

## I tre numeri che contano

1. **40/40.** Con la soglia fissata sulla cella pulita — la stessa politica con cui furono
   contati i nulli di PySINDy — la seconda implementazione rivendica un modello su **ogni**
   campo nullo, selezionando in mediana tutti e 7 i termini. Nessuna delle due implementazioni
   ha un criterio che preferisca il modello vuoto.
2. **0/40 col cancello.** Il residuo relativo dei nulli sta fra 0,798 e 0,998; quello delle
   celle vere al supporto esatto arriva al massimo a 4,1·10⁻². La separazione è un fattore **19**,
   e il cancello al 5 % ci sta dentro comodamente. **Il cancello trasferisce a una seconda
   implementazione, in un altro linguaggio.**
3. **20/20 contro 14/20.** Sulle stesse celle vere, la selezione indipendente sulle *nostre*
   feature recupera il supporto esatto ovunque, mentre PySINDy sulle *proprie* feature ne
   recupera 14. Poiché l'ottimizzatore è della stessa famiglia in entrambi i casi, la differenza
   è attribuibile all'operatore weak. È un sostegno **indipendente** alla decomposizione causale
   già affermata nella nota: il rifiuto dei nulli viene dallo strato epistemico, la robustezza al
   rumore dalla qualità dell'operatore validato.

## Il numero che va riportato contro di noi
Con la politica **oracolo** — la più favorevole al concorrente, cioè scegliendo per ogni caso la
soglia che si astiene se esiste — le rivendicazioni scendono a **10/40**: su 30 nulli su 40 la
griglia *contiene* una soglia che si astiene (per PySINDy erano 33/50). Detto altrimenti: non è
che la selezione sparsa non possa mai astenersi, è che **non ha un criterio per decidere quando
farlo**, e un professionista che non sa di avere in mano un nullo non ha quell'oracolo. Il
cancello sul residuo è precisamente quel criterio.

## Cosa NON dimostra
- **Non confronta le pipeline.** Le feature deboli sono le nostre in tutti i bracci: non dice
  nulla sull'operatore di `DataDrivenDiffEq`, e il 20/20 contro 14/20 non è un verdetto sulla
  loro libreria ma sulla combinazione feature+ottimizzatore.
- **Non è cieco:** la verità dei nulli è nota per costruzione (nessuna dinamica).
- **Non include KS**, escluso per mantenere l'appaiamento; su KS PySINDy faceva 9/10.
- Due implementazioni non sono la classe: sono due. La frase corretta è «due implementazioni
  indipendenti, in due linguaggi, si comportano allo stesso modo», non «tutti i metodi sparsi».
- Nessuna misura di tempo.
