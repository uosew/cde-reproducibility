# Preregistrazione — limite di risoluzione dichiarato per ogni CLAIM

**Data:** 2026-09-03, prima di qualunque run.
**Origine:** `CLAIM_CARD_V13_UNBLINDING_2026-09-03.md`: 14 claim false su 423, tutte *claim di
sotto-supporto* (termine vero `div_vv_x` a ~0,5 % della dinamica, sotto la risoluzione dei
cancelli). **Protocollo vincolante:** `FAST_EXPERIMENT_PROTOCOL_V1.md`.
**Pipeline:** discoverer termico V13 (`CDE_V13_BLIND_DISCOVERER_V0.py`, ladder v2.1, importata),
**non modificato**. Il limite è un'annotazione a valle: non cambia nessun verdetto.

## 0. Regola anti-riciclaggio, prima di tutto
Le 14 claim false della V13 **restano claim false** nello scoring della V13. Il limite di
risoluzione è una semantica nuova applicata **in avanti**, su un pannello nuovo; non serve a
riscrivere una campagna chiusa. Sulla V13 si esegue solo lo Stage 1 diagnostico, a verità aperta,
e il suo esito **non conta** come conferma.

## 1. Definizione, congelata

Dato un CLAIM con supporto S, coefficienti stimati ĉ, matrice A (feature pooled delle repliche
0-3, libreria `TERMS = (const, v, v2, v_x, v_xx, vv_x, div_vv_x)`) e b (termine temporale):

```
ρ      = ||A_S ĉ − b||₂                       residuo assoluto del modello affermato
X      = k · ρ / ||b||₂                        limite di risoluzione relativo
c_min(t) = k · ρ / ||A_t||₂   per t ∉ S        coefficiente minimo rilevabile del termine t
f_t    = |c_t| · ||A_t||₂ / ||b||₂             contributo relativo di un termine t
```

**Lettura del CLAIM annotato:** «legge S con coefficienti ĉ, **a meno di termini della libreria
con contributo relativo inferiore a X**». Un termine con f_t < X non è escluso dai dati: la
claim dichiara ignoranza invece di negarlo.

`k` è il solo numero: candidati **k = 1** (stretto) e **k = 2** (`FATTORE_IDENT`, già congelato
con lo stesso significato «entro fattore 2 dal residuo non è distinguibile»). Nessun altro
valore verrà provato.

## 2. Ipotesi

**H1 (soundness, primaria):** su ogni CLAIM di caso rappresentabile, ogni termine vero mancante
t ∈ S_vero \ S ha f_t(c_t^vero) < X. Zero violazioni.
**H2 (informatività):** X non è vacuo: mediana di X sui CLAIM ≤ 0,05 (il gate di fit; per
costruzione X ≤ k·0,05). Si riporta la distribuzione.
**H3 (innocuità):** l'annotazione non cambia alcun verdetto: si asserisce uguaglianza
caso per caso fra i verdetti del discoverer e quelli annotati.

**Atteso a priori:** k=1 violato da qualche caso (il modello assorbe parte del termine mancante
tramite colonne correlate, e ρ lo sottostima); k=2 sound. Se anche k=2 è violato, la
costruzione «residuo × fattore» è sbagliata e va cambiata natura, non numero.

Mappa parametri → coefficienti veri (usata **solo** dallo scorer, a verità aperta): dal
generatore V11, `rhs = ∇(D v_x) − β v`, `D = α(1 + γ v)` ⇒ `v_xx ↔ α`, `v ↔ −β`,
`div_vv_x ↔ α·γ`; ogni altro termine 0. I contributi usano valori assoluti: i segni non contano.

## 3. Stage 1 — diagnostico sulla V13 (verità aperta, NON confermativo)
Campione: **tutte le 14 claim false** + **30 claim corrette** estratte con seme 20260903
dalle 105. Per ciascuna: ricalcolo di A, b dal caso (stesse feature del discoverer),
X e c_min per k ∈ {1, 2}, f_t dei termini veri mancanti.
- Esito: `k*` = il più piccolo k con **0 violazioni** sulle 44. `PROMISING` se k* esiste;
  `NOT_PROMISING` se entrambi violano. Non esiste `UNCLEAR`: le 14 false garantiscono il test.
- Costo: ~40 s per caso → **~30 min**; tetto 45.

## 4. Stage 2 — blind-4, pannello nuovo, verità sigillata con sha (correzione E8-bis)
- Generatore: quello V13 (che importa la fisica V11) ristretto alle **classi rappresentabili
  A, B, C, F × 30 = 120 casi**, semi nuovi `SEME_MODELLO = 720000`, `SEME_DEGRADO = 730000`
  (mai usati). Nulli e non rappresentabili non servono: l'annotazione non tocca i verdetti (H3
  asserita) e la loro FP resta quella della V13 per costruzione.
- **Sigillo crittografico:** `sealed/truth.sha256` scritto dal generatore, sha nell'envelope,
  `truth.json` committato **prima** del run del discoverer, in un commit separato.
- Discoverer V13 **invariato** (stessa ladder v2.1 della V13, così il confronto è con la
  campagna che ha prodotto le 14 false), cieco; annotazione a valle con `k*`.
- Scorer separato, mutation test prima del verdetto, apre `sealed/` solo dopo l'hash delle
  predizioni.

**Verdetto (congelato):**
| verdetto | condizione |
|---|---|
| **CONFIRMED** | 0 violazioni di H1 su tutti i CLAIM rappresentabili con k*, **e** H3 (0 verdetti cambiati), **e** ≥ 30 CLAIM (regola del tre: tasso di violazione ≤ 10 %) |
| **REJECTED** | ≥ 1 violazione di H1 |
| **INCONCLUSIVE** | < 30 CLAIM |

Si riportano anche, invariati come definizione: claim false strette (supporto esatto, come V13)
e **copertura** = quota delle claim di sotto-supporto il cui termine mancante sta sotto X (se H1
regge è 100 % per costruzione; se regge *solo* per k=2, la copertura per k=1 dice quanto costa
la strettezza).

**Potere (§4 del protocollo):** dai tassi V13 (105 claim su 268 rappresentabili; 15 claim in
classe C su 67, 14 false) ci si attende **~47 CLAIM** di cui **~6-7 di sotto-supporto**. Zero
violazioni su 47 limita il tasso di violazione al 6,4 % (regola del tre). **Un CONFIRMED qui è
una prima replica, non un VALIDATED**: un limite sotto il 2 % richiede ≥ 150 CLAIM.

**Compute envelope:** generazione ~5 min; discovery 120 × 53 s ≈ **106 min**; annotazione ~20
min. Totale **~2 h 15**; arresto a +50 % (3 h 20) con dichiarazione. **Eccezione motivata** ai
20-40 min del protocollo: 120 casi sono il minimo per ~47 claim.

## 5. Cosa NON dimostra
- Nulla sui termini **fuori libreria** (surrogati di Taylor): f_t è definita solo per t nella
  libreria. Il limite copre l'ignoranza *dentro* la libreria; quella fuori resta al cancello di
  ampiezza e alla semantica `CLAIM_EFFETTIVO`.
- Nulla sulla pipeline PDE V1 (feature diverse): la definizione è indipendente dalla pipeline
  e può essere portata, ma va misurata lì.
- Nulla sulla recall: X non recupera claim, le qualifica.
- Con ~47 claim, il tasso di violazione è limitato al 6 %, non escluso.

## 6. Ledger
| data | voce |
|---|---|
| 2026-09-03 | creata prima di ogni run; k ∈ {1, 2} congelato; campione Stage 1 e semi Stage 2 dichiarati. |
| 2026-09-03 | Stage 1 eseguito (44 claim, 675 s): k=1 viola 2/14 (case_138, case_193), k=2 **0 violazioni**, copertura 14/14, X mediana 0,0252 → **k\* = 2, PROMISING**. Previsione a priori confermata. Blind-4 generato e sigillato (sha `e92ebf05…`, commit `e264506a`) prima del discoverer. |
| 2026-09-03 | **Blind-4 eseguito e sbendato**: 120 casi, 5.277 s; 59 CLAIM, 8 false strette (tutte C, sotto-supporto), **0 violazioni di H1 con k\*=2** (copertura 8/8, margine min 1,68×), 0 verdetti cambiati, X mediana 3,0 %. **CONFIRMED** (§4). Sigillo crittografico verificato, predizioni hashate prima dell'apertura. Claim card `CLAIM_CARD_BLIND4_LIMITE_RISOLUZIONE_2026-09-03.md`. Prima replica, non VALIDATED. |
