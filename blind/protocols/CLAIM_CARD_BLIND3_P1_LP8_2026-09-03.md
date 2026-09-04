# Claim card — Blind-3: P1-LP8 contro P1 grezzo

**Prereg:** `PREREGISTRAZIONE_BLIND3_P1_LP8_2026-09-03.md`, sha256 `773f524c63cb…`, commit
`88db4a8a`, prima della generazione. **Cecità:** sigillo intatto (`0ba8300b…`), runner senza
riferimenti a `sealed/`, predizioni hashate (`8b78ae36…`) prima dell'apertura. **Artefatti:**
`cde_blind3_out/{sealed,predictions.json,scoring.json}`; i 40 `.npz` (243 MB) non sono in git e
si rigenerano dal generatore (deterministico dai semi 9201-9240). Scorer con 7 mutation test.

## Verdetto: **INCONCLUSIVE**

| | CLAIM veri | CLAIM falsi | coarse chiuse | regressioni σ=2 % | supporto diverso |
|---|---|---|---|---|---|
| A — P1 grezzo | 16 | 0 | — | — | — |
| **B — P1-LP8** | **17 (Δ +1)** | **0** | **5/5** | **0** | **0** |

Discordanti 1 pro / 0 contro, p dei segni 0,5. Il CONFIRMED richiedeva Δ ≥ 3 con 0 falsi:
il candidato **non fa danno** (tutte le guardie rispettate) ma **aiuta poco**. Tempo 1634 s
contro 2220 stimati: stima prudente, sotto il tetto.

## Perché l'effetto non c'è: la cascata

Il filtro riapre 4 casi che P1 grezzo chiudeva. Uno diventa CLAIM corretto (Burgers,
case_20). Gli altri tre vengono chiusi dal cancello successivo: quadratica → test di scambio
(NOT_IDENTIFIABLE), due decoy `tanh(u)` → transfer e ampiezza, **correttamente**. P1 grezzo
stava fermando i decoy per caso (il termine fuori libreria porta contenuto ad alto k), e
il filtro li consegna ai cancelli fatti per loro, che li fermano.

Sulle 25 leggi vere a 15 %, il braccio A chiude 14 celle su **quattro cancelli diversi**:

| cancello | celle | esempio |
|---|---|---|
| preflight (P1 o P3) | 6 | Burgers: 4/5, P3 = 0,044-0,053, cioè il pavimento di rumore sul gate |
| test di scambio | 3 | quadratica 3/5: supporto `{u, u²}` con u ∈ [0,3; 0,7], colonne quasi collineari |
| ampiezza | 3 | cubica 2/5 (0,05 fisso, come in produzione) |
| transfer | 2 | |

**La previsione della prereg era sbagliata su un punto**: i falsi negativi quadratici
visti negli screening (2/2) erano P1; qui la quadratica cade 3/5 sullo scambio. Con
offset 0,5 e ampiezza 0,2 la famiglia è **al confine dell'identificabilità**, e
NOT_IDENTIFIABLE è verosimilmente la risposta corretta, non un falso negativo. Lo scoring
lo conta come mancato CLAIM per regola congelata; la lettura resta a margine.

## Cosa si è imparato, in ordine di peso

1. **A σ = 15 % il CDE non ha un collo di bottiglia: ha una cascata.** Ogni cancello sta
   sul pavimento di rumore (P3, fit, transfer, ampiezza ≈ 0,03-0,05 tutti insieme) e
   sbloccarne uno sposta la chiusura al successivo. Un intervento che alza il tetto di
   rumore deve agire **a monte** (feature deboli con denoising, finestre più larghe) o
   accettare il confine dichiarato (10 %), che oggi è misurato e robusto.
2. **P1-LP8 è un miglioramento innocuo**: 0 danni su 40 celle cieche, +1 recupero, controlli
   di risoluzione intatti. Non entra in produzione con questo verdetto: l'evidenza è
   insufficiente per la regola scritta prima, e la regola vale più del gradimento.
3. **I decoy sono fermati due volte** (P1 per caso, poi transfer/ampiezza per disegno):
   ridondanza utile, da non contare come merito di P1.

## Stato dell'ipotesi
H1 resta `HYPOTHESIS`, evidenza allegata: Stage 1 PROMISING, blind-3 INCONCLUSIVE.
Replica possibile con pannello a rumore 12 % (dove P1 morde e gli altri cancelli non
ancora): va preregistrata; non è programmata.

## Cosa NON dimostra
Vedi prereg §7. In più: 1 discordante non è un effetto; 25 celle a un solo σ non
descrivono la curva P1(σ) per famiglia.
