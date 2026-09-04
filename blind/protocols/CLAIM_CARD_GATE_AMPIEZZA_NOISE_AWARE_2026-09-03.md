# Claim card — cancello di ampiezza consapevole del rumore (Stage 1)

**Preregistrazione:** `PREREGISTRAZIONE_GATE_AMPIEZZA_NOISE_AWARE_2026-09-02.md`,
sha256 `74d3d1ab0fc7c517a948abf62eda25429ff00775c32850c254bcf3439cf90717`, committata
(`fdc6afcc`) prima di ogni run.
**Baseline:** V1, tag `cde-v1-baseline-2026-09-02`.
**Artefatti:** `cde_gate_ampiezza_out/screening.json` (16 celle, 854 s),
`screening_raddoppio.json` (8 celle a σ=15 %, 263 s, unico raddoppio ammesso da §5),
`esito_stage1.json`. Analizzatore con 6 mutation test, tutti mordenti prima della lettura.

## Verdetto: **NOT_PROMISING** per tutti e tre i candidati. Nessun blind-3. La V1 resta la produzione.

| | FN leggi vere | FP decoy | esito §5 |
|---|---|---|---|
| **V1** (baseline) | 1 / 24 celle | **0** | — |
| C1 rumore stimato (`0,05 + σ̂`) | 0 (Δ +1) | **1 (Δ +1)** | NOT_PROMISING (guardia 1) |
| C2 relativo al fit (`max(0,05; 2·fit)`) | 1 (Δ 0) | 0 | NOT_PROMISING (inerte) |
| C3 calibrato (`g* = 0,0515`) | 1 (Δ 0) | 0 | NOT_PROMISING (inerte) |

Il caso previsto a priori si è verificato alla lettera: C1, il candidato più permissivo,
recupera l'unico falso negativo (cubica, σ=15 %, errore 1,92 %) **e fa passare un decoy**
(`sin(u)` fuori libreria, σ=15 %). Per il criterio dettato dall'utente e congelato in §4
questo è un peggioramento, a prescindere dal recupero. C2 e C3 non toccano nulla.

## Cosa dice il dato, oltre il verdetto

1. **Sui pannelli nuovi la V1 non ha falsi negativi fino al 10 %** (9/9 leggi vere CLAIM,
   errori ≤ 1,6 %, nessun decoy). Allen-Cahn 10 % della produzione (r_amp 0,0536) era
   un'eccezione, non un sintomo: sulle leggi vere nuove r_amp al 10 % vale 0,025-0,031.
2. **A σ=15 % il collo di bottiglia non è il cancello di ampiezza: è il preflight.**
   3 leggi vere su 5 si fermano a `ABSTAIN_PREFLIGHT` prima di ogni decisione; una quarta
   (cubica+advezione, errore 0,60 %) finisce `NOT_IDENTIFIABLE` per il test di scambio.
   Il gate di ampiezza vede una sola legge vera su cinque.
3. **Il problema del cancello, dove esiste, è una zona di ampiezza ~1,1×** (0,0536 e la
   cubica 15 % contro 0,05), e i decoy più facili stanno a 0,0605-0,086: lo spazio fra
   veri e surrogati a rumore alto è troppo stretto per una soglia scalare. Confermato
   da g\* = 0,0515: la calibrazione onesta sposta la soglia del 3 %.

## Ipotesi archiviata, non falsificata
H1 resta `HYPOTHESIS` con questa evidenza allegata (protocollo §3: NOT_PROMISING ≠
REJECTED). Un futuro tentativo dovrebbe cambiare **natura** del discriminante (non
scalare: per esempio confrontare la forma del residuo di ampiezza fra regimi), non il
suo numero. E dovrebbe partire dal preflight, che a rumore alto decide prima di tutti.

## Cosa questo esperimento NON dimostra
Vedi prereg §8. In più: 10 celle vere e 1 solo FN nella V1 sono un campione minuscolo;
il verdetto è una decisione di non spendere, presa con criteri scritti prima.
