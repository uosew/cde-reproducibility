# Preregistrazione — Blind-3: P1-LP8 contro P1 grezzo, verità sigillata

**Data:** 2026-09-03, prima della generazione del pannello.
**Stadio:** 2 (conferma), unico che può produrre un verdetto. Parte perché lo Stage 1
(`CLAIM_CARD_PREFLIGHT_P1_STAGE1_2026-09-03.md`) è `PROMISING` e ha scelto P1-LP8.
**Baseline:** V1 (tag `cde-v1-baseline-2026-09-02`) con preflight P1 grezzo.
**Candidato:** V1 con P1 calcolato sul campo passa-basso `|k| < Nx/8`. **Nient'altro cambia.**

## 1. Cecità
- Il generatore scrive `cases/case_NN.npz` (x, t, U, U2, U3) e `cases/public_manifest.json`
  (case_id, Nx, Nt, u_std): **nessuna famiglia, nessun coefficiente, nessun ruolo**.
- La verità va in `sealed/truth.json`, con `sealed/truth.sha256`, **prima** di ogni run.
- L'ordine dei casi è mescolato con rng (seme 9200): l'id non rivela il ruolo.
- Il runner non apre `sealed/`; lo scorer lo apre **solo dopo** aver scritto e hashato
  `predictions.json`. L'audit di cecità (sha attesi/attuali, nessun riferimento a
  `sealed` nel runner) è registrato nello scoring, come nel blind 2.
- Nx=192 è visibile nel manifesto per necessità (la pipeline legge la griglia). Il runner
  tratta ogni caso allo stesso modo.

## 2. Pannello — disgiunto da tutto (semi 9201-9240, mai usati)

| ruolo | celle | regola |
|---|---|---|
| leggi vere, σ=15 %, Nx=768 | 25 | 5 per famiglia (cubica, quadratica, Burgers, dispersiva, cubica+advezione), coefficienti dal seme |
| leggi vere, σ=2 %, Nx=768 | 5 | 1 per famiglia: **regressione a rumore basso** |
| controllo di risoluzione, Nx=192, σ=0 | 5 | 1 per famiglia: il candidato DEVE chiudere |
| decoy, σ=15 %, Nx=768 | 5 | sin(u), tanh(u), sin(u) a 1,4, tanh(u) a 1,4, sin(u) a 0,7 |

Rumore su tutte e tre le traiettorie. **40 celle.**

## 3. Appaiamento
Stesse feature per i due bracci; l'unica differenza è quale P1 apre il preflight. Se
almeno un braccio apre e P2/P3 < 0,05, la decisione V1 è calcolata **una volta** e
condivisa: la differenza fra bracci è esattamente e solo P1.

## 4. Metriche e verdetto — congelati (criteri dell'utente, 2026-09-02 §7)

Per braccio: `CLAIM_veri` = celle vere con verdetto assertivo, supporto esatto, errore < 5 %;
`CLAIM_falsi` = verdetti assertivi su decoy **o** su leggi vere con supporto sbagliato.

| verdetto | condizione (tutte) |
|---|---|
| **CONFIRMED** | `CLAIM_veri(B) − CLAIM_veri(A) ≥ 3` **e** `CLAIM_falsi(B) = 0` **e** supporto esatto identico in ogni cella dove entrambi affermano **e** 5 celle a σ=2 % con verdetti identici **e** 5/5 coarse chiuse da B |
| **REJECTED** | `CLAIM_falsi(B) > CLAIM_falsi(A)`, **oppure** una coarse aperta da B, **oppure** una regressione a σ=2 % |
| **INCONCLUSIVE** | tutto il resto (in particolare: nessun danno ma Δ < 3) |

Nulli: P1 non entra nel braccio nullo (`V1.braccio_nullo` non esegue il preflight): il
`fpr_nulli` è invariato **per costruzione**; lo scorer lo asserisce leggendo il codice
(il runner non tocca `braccio_nullo`).

Statistica: test dei segni sulle celle discordanti (B afferma correttamente dove A
chiudeva, contro il contrario). Riportato il p unilaterale: 3/3 → 0,125; 4/4 → 0,0625;
5/5 → 0,031. **Dichiarato ora:** con Δ = 3 il verdetto CONFIRMED poggia più sul vincolo
«0 falsi» che sulla significatività; un CONFIRMED con Δ < 5 va replicato prima di
diventare VALIDATED nel registry.

## 5. Potere (§4)
Fonte: due screening. FN di P1 grezzo a 15 %: 2/2 sulla famiglia quadratica, 0/8 sulle
altre. Atteso: ~5 FN, tutti quadratici; LP8 ha aperto 2/2 ma a 0,046 e 0,037, vicino al
gate → **discordanti attesi 3-5**. Effetto minimo distinguibile: 3. Il disegno può
dichiarare CONFIRMED solo se l'effetto è quasi tutto recuperato; altrimenti INCONCLUSIVE,
che è l'esito onesto di un effetto piccolo.

## 6. Compute envelope
~60 s per cella a 768 con decisione (misurato nello Stage 1), ~25 s a 192, ~15 s di
simulazione per caso. Stima: generazione **10 min**, run **37 min** → **~50 min**.
Arresto a +50 % (75 min): si ferma e si dichiara. È oltre i 20-40 min del protocollo:
**eccezione motivata** — 40 celle sono il minimo per il potere del §5.

## 7. Cosa NON dimostra
Nulla oltre il 15 %; nulla su rumore non gaussiano; nulla su P2/P3 (già ≈ fit). Se
l'effetto è solo quadratico, il CONFIRMED vale per quella famiglia e lo scoring lo dice.

## 8. Ledger
| data | voce |
|---|---|
| 2026-09-03 | creata prima della generazione. Nessun run. |
| 2026-09-03 | pannello generato (40 casi, 90 s) e sigillato; runner cieco 1634 s; scorer: **INCONCLUSIVE** (Δ +1, 0 falsi, guardie ok). Claim card `CLAIM_CARD_BLIND3_P1_LP8_2026-09-03.md`. |
| 2026-09-03 | **Decisione dell'utente:** claim boundary sul rumore fissata al 10 %; filone > 10 % chiuso per ora (`DECISIONE_CLAIM_BOUNDARY_RUMORE_10_2026-09-03.md`). |
