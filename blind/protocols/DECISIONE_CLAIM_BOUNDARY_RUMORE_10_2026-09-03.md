# Decisione — claim boundary sul rumore: 10 %

**Data:** 2026-09-03. **Decisore:** utente. **Stato:** in vigore fino a revoca scritta.
**Pipeline di riferimento:** V1, tag `cde-v1-baseline-2026-09-02` (non modificata da questa decisione).

## La decisione

Il CDE dichiara scoperte **fino al 10 % di rumore gaussiano iid** relativo a std(U), su
PDE 1D periodiche lisce da solver spettrale, con le tre traiettorie (principale, transfer,
secondo regime di ampiezza) tutte rumorose. **Oltre il 10 % il CDE non afferma**: si astiene,
e l'astensione è il comportamento voluto, non un difetto da correggere. Il filone «alzare
il tetto di rumore» è **chiuso per ora**.

## L'evidenza su cui poggia

| misura | risultato | fonte |
|---|---|---|
| produzione V1, 4 sistemi × 0-10 % | 19/20 CLAIM corretti, 0 falsi, 0/40 nulli | `cde_produzione_v1_out/` |
| pannello nuovo, 5 famiglie × 5-10 % | 9/9 CLAIM corretti, 0 decoy passati | `cde_gate_ampiezza_out/screening.json` |
| blind-3 a 15 %, 25 leggi vere | 11 CLAIM (A) / 12 (B), 0 falsi, 14 chiusure su 4 cancelli | `cde_blind3_out/scoring.json` |
| gate di ampiezza noise-aware, 3 candidati | NOT_PROMISING | claim card 2026-09-03 |
| P1 su campo filtrato | Stage 1 PROMISING, blind-3 INCONCLUSIVE | claim card blind-3 |

Sotto il 10 % il sistema è **misurato e robusto**; a 15 % ogni cancello (P3, fit, transfer,
ampiezza, scambio) sta sul proprio pavimento di rumore intorno a 0,03-0,05 e le chiusure
sono una **cascata**, non un collo di bottiglia. Due tentativi preregistrati di alzare il
tetto agendo sui cancelli hanno dato zero danni e zero effetto utile.

## Cosa chiude e cosa no

- **Chiuso:** nuove varianti di cancello (soglie, misurandi) per il regime > 10 %.
- **Non chiuso, non programmato:** interventi **a monte** dei cancelli (denoising delle
  feature deboli, finestre più larghe, test function diverse). Riaprirebbero il filone
  solo con preregistrazione e con i criteri di successo congelati il 2026-09-02 §7.
- **Non toccato:** l'unica astensione fra 0 e 10 % (Allen-Cahn 10 %, ampiezza 0,0536 contro
  0,05) resta un falso negativo noto e dichiarato, dentro il confine. Non giustifica da
  solo un cambio di soglia.

## Effetto sulla comunicazione delle claim

Ogni claim card, nota e riepilogo scrive il confine così: **«validato fino al 10 % di
rumore; oltre, astensione per costruzione»**. Non «fino al 10 % circa», non «robusto al
rumore». Il numero è misurato, il comportamento oltre è dichiarato.
