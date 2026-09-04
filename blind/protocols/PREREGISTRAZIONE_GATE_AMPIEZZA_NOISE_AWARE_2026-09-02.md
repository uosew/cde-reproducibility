# Preregistrazione — cancello di ampiezza consapevole del rumore

**Data:** 2026-09-02, prima di qualunque run.
**Baseline congelata:** `CDE_PDE_PIPELINE_GATED_V1.py`, sha256 `faedaa183a94a7dd…`,
tag `cde-v1-baseline-2026-09-02` (commit `d44deedd`).
**Protocollo vincolante:** `FAST_EXPERIMENT_PROTOCOL_V1.md`.

## 0. Il problema, circoscritto

La prima run di produzione della V1 (`cde_produzione_v1_out/`) dà 19/20 CLAIM corretti,
0 falsi positivi, 0/40 nulli. L'unica astensione è Allen-Cahn al 10 % di rumore: supporto
esatto, errore 2,15 %, ma residuo sul secondo regime 0,0536 contro il gate fisso 0,05.
Il cancello confronta un residuo che cresce col rumore con una soglia cieca al rumore.

**Allen-Cahn 10 % è un caso GIÀ VISTO: è diagnostico, non confermativo.** Nessun
candidato viene scelto o scartato perché lo recupera; non entra in nessun pannello;
il suo esito viene riportato a parte, come informazione, e non conta nei criteri.

## 1. Ipotesi

H1: esiste un cancello di ampiezza che riduce i falsi negativi delle leggi vere a rumore
alto **senza** aumentare i CLAIM su surrogati (decoy) e senza toccare nulli, supporto,
coefficienti e transfer.

**Atteso a priori:** almeno un candidato `PROMISING`; il candidato più permissivo (C1)
sospettato di far passare decoy a rumore basso.

## 2. I tre candidati — numeri congelati ORA, nessuno derivato da Allen-Cahn

Tutti agiscono **solo** sulla riga `r_amp < GATE_AMPIEZZA` della V1. Tutto il resto
(condizionamento, selezione, fit, transfer, scambio, nulli) resta identico per costruzione.

| | regola | numeri e loro origine |
|---|---|---|
| **C1** rumore stimato | `r_amp < 0.05 + σ̂_rel` | `σ̂_rel` = std del residuo di passa-basso spaziale (taglio `|k| ≥ Nx/8`) diviso std(U), stimato sulla traiettoria principale senza verità; coefficiente **1**, dichiarato, non tarato |
| **C2** relativo al fit | `r_amp < max(0.05, 2 · resid_fit)` | il fattore **2** è `FATTORE_IDENT`, già congelato nella pipeline con lo stesso significato («entro fattore 2 dal residuo migliore non è distinguibile») |
| **C3** calibrato | `r_amp < g*`, con `g*` = media geometrica di (max `r_amp` leggi vere, min `r_amp` decoy) su un **set di calibrazione disgiunto**; se non separati, C3 = `NON_APPLICABILE` | set di calibrazione: 3 leggi vere + 3 decoy, semi 8001-8006, σ = 10 % |

Nota su C2 e Allen-Cahn 10 %: `2 · 0,0186 = 0,037 < 0,0536`, quindi C2 **non** recupera
il caso diagnostico. È scritto qui apposta: dimostra che il fattore non è stato scelto
guardando quel caso.

## 3. Pannello dello Stage 1 — disgiunto da tutto

Generatore: `simula` di `CDE_BLIND_PDE2_GENERATOR_V0.py` (stesso codice dei pannelli
ciechi). Semi **9001-9008**, mai usati (blind 1/2: altri semi; produzione: 7, 8).

| ruolo | n | famiglie (coefficienti estratti dal seme, in libreria) |
|---|---|---|
| leggi vere | 5 | reazione cubica, reazione quadratica, Burgers, dispersiva, cubica+advezione |
| decoy | 3 | `sin(u)` + diffusione, `tanh(u)` + diffusione, `sin(u)` ad ampiezza 1,4 |

Ogni caso a σ ∈ {5 %, 10 %} su tutte e tre le traiettorie → **16 celle**. Semi per
cella: 1 (§1). Ogni cella: V1 baseline + C1 + C2 + C3 sulle **stesse** feature
(appaiamento esatto: la decisione differisce solo nella riga del cancello).

**Compute envelope:** dalla run di produzione, ~45 s per cella senza nulli + ~15 s di
simulazione per caso → stima **14 min** screening + **5 min** calibrazione C3.
Tetto dichiarato 20 min; oltre +50 % (30 min) si ferma e si dichiara la stima sbagliata.

## 4. Metriche — congelate

- **Primaria (contrasto):** `Δ_FN = FN_V1 − FN_cand` sulle celle di leggi vere, dove FN =
  cella con supporto esatto e errore coefficienti < 5 % ma verdetto `ABSTAIN_AMPIEZZA`.
- **Guardia 1 (decoy):** `FP_dec_cand − FP_dec_V1`, con FP = verdetto assertivo su decoy.
  **Qualunque aumento > 0 rende il candidato `NOT_PROMISING`**, a prescindere da Δ_FN.
- **Guardia 2 (nulli):** il cancello è a valle di supporto e fit; i nulli si astengono a
  monte. L'analizzatore **asserisce** che nessun candidato cambia un verdetto nullo; se
  accade è un bug, non un risultato.
- **Guardia 3 (regressione):** su ogni cella di legge vera in cui V1 dice CLAIM, il
  candidato deve dire CLAIM con supporto e coefficienti **identici** (la riga del
  cancello non li tocca: si asserisce).

## 5. Criteri di uscita (§3) e potere (§4), dichiarati onestamente

Potere: dalla produzione, FN di V1 ≈ 1 su 4 celle al 10 %, ≈ 0 al 5 % → **FN attesi in
V1 ≈ 1-2 su 10 celle vere**. Il disegno **non può** classificare fra candidati con
precisione: può solo distinguere «aiuta senza danno» da «danneggia» o «inerte». Lo
Stage 1 è **direzionale**, e il suo esito non promuove nulla.

| esito | condizione |
|---|---|
| `PROMISING` | Δ_FN ≥ 1 **e** guardia 1 = 0 **e** guardie 2-3 rispettate |
| `NOT_PROMISING` | guardia 1 > 0, **oppure** Δ_FN ≤ 0 |
| `UNCLEAR` | FN_V1 = 0 sul pannello (nessuna cella su cui migliorare): un solo raddoppio ammesso, con σ = 15 % aggiunta, dichiarato qui |

Soglia di rilevanza: 1 cella. Con conteggi così piccoli il CI90 è degenere; si riporta
il conteggio esatto delle celle discordanti (test dei segni), non un intervallo finto.

## 6. Regola di scelta PRIMA del blind-3

Un solo candidato va al blind-3. Fra i `PROMISING`: il maggiore Δ_FN; a parità, ordine
di priorità **C2 > C1 > C3** (dal minor numero di numeri nuovi al maggiore). Se nessuno
è `PROMISING`, il blind-3 non si fa e la V1 resta la produzione.

## 7. Blind-3 — criteri di successo, congelati ora (dettati dall'utente)

Pannello disgiunto da Stage 1, calibrazione, blind 1/2 e produzione. Confronto appaiato
V1 contro il candidato scelto. Il candidato **migliora il CDE** se e solo se, insieme:

1. **più CLAIM veri** di V1;
2. **0 CLAIM falsi** (un aumento da 0 a un qualunque numero è peggioramento);
3. **supporto esatto invariato** cella per cella;
4. **nessuna regressione a rumore basso** (celle a σ ≤ 2 %: verdetti identici a V1);
5. nulli: `fpr_nulli` invariato (asserito per costruzione, verificato).

Esempio dichiarato: 19/20 → 20/20 sui veri con 2/40 nulli o 1 decoy in più = **peggioramento**.

## 8. Cosa questo esperimento NON potrà dimostrare

- Che il cancello scelto sia ottimo: i tre candidati sono tre punti, non una famiglia.
- Nulla su PDE lineari (semantica §6: il test fuori regime è vacuo) né su dati reali.
- Nulla sul rumore non gaussiano o correlato: σ è gaussiano iid, come in tutta la linea.
- Con 10 celle vere non distingue candidati vicini: quello lo farà il blind-3.

## 9. Ledger
| data | voce |
|---|---|
| 2026-09-02 | preregistrazione creata; V1 congelata (tag); nessun run eseguito; Allen-Cahn 10 % dichiarato diagnostico. |
| 2026-09-03 | Stage 1 eseguito (16 celle, 854 s) → FN_V1 = 0 → `UNCLEAR`; raddoppio dichiarato a σ=15 % (8 celle, 263 s). Esito finale: **NOT_PROMISING** per C1 (recupera 1 FN ma +1 decoy), C2 e C3 (inerti). Nessun blind-3. V1 resta la produzione. Claim card `CLAIM_CARD_GATE_AMPIEZZA_NOISE_AWARE_2026-09-03.md`. Difetto dell'analizzatore corretto prima del raddoppio (celle fermate al preflight saltavano i candidati); non cambia l'esito dello Stage 1. |
| 2026-09-03 | **Decisione dell'utente:** claim boundary sul rumore fissata al 10 %; filone > 10 % chiuso per ora (`DECISIONE_CLAIM_BOUNDARY_RUMORE_10_2026-09-03.md`). |
