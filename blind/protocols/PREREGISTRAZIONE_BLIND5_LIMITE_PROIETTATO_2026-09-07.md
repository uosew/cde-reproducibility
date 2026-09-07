# Preregistrazione — Blind-5: limite di risoluzione proiettato, k = 1

**Data:** 2026-09-07, prima della generazione. **Origine:** `NOTA_FORMALIZZAZIONE_LIMITE_RISOLUZIONE_2026-09-07.md`
(proposizione: `c_min(t) = ‖(I−P_S)y‖/‖(I−P_S)a_t‖`; diagnostica su 22 casi aperti: 0 violazioni,
margine min ≈ 1,9×). **Pipeline:** discoverer termico V13 invariato; annotazione a valle.

## 0. Anti-riciclaggio
I 22 casi della diagnostica sono a verità aperta e **non contano**. Il blind-4 (k = 2 euristico)
resta CONFIRMED nel suo scoring; questa campagna confronta **sullo stesso pannello nuovo** il
limite v1 (euristico k = 2, in produzione) e il limite v2 (proiettato k = 1).

## 1. Ipotesi
**H1 (soundness v2):** su ogni CLAIM di caso rappresentabile, ogni termine vero mancante `t`
soddisfa `|c_t^vero| < c_min^v2(t)`. Zero violazioni.
**H2 (strettezza):** il margine mediano `c_min^v2/|c_t|` è inferiore a quello del v1 (5,8×
atteso dalla diagnostica per k=2 proiettato… per v1 euristico k=2: 2,65×). Nota: v2 k=1 e v1 k=2
euristico hanno margini simili per costruzione (`‖ã_t‖/‖a_t‖ ≈ 0,45 ≈ 1/2,2`): H2 non è un
test di superiorità, è la misura di quanto la proiezione **spiega** il fattore 2.
**H3 (innocuità):** nessun verdetto cambia (asserito).
**H4 (selezione, non rumore):** frazione delle claim di sotto-supporto in cui `|ĉ_t| > 2·se`
(termine statisticamente visibile): atteso ≈ 100 %. Riportata, non gate.

**Atteso a priori:** H1 vera; H2: margini v2 ≈ v1; H4 ≈ 100 %. Se H1 fallisce con k = 1, si
riporta la violazione e si verifica se `‖ẽ‖ ≤ ‖r‖` (condizione (c) della nota) la spiega.

## 2. Pannello (semi 740000/750000, mai usati)
120 casi rappresentabili A, B, C, F × 30, generati con `CDE_BLIND4_GENERATOR_V0.py`
parametrizzato (stessa fisica V11, stessa camera). Verità sigillata con sha nell'envelope,
committata **prima** del run del discoverer, in commit separato.

## 3. Verdetto (congelato)
| verdetto | condizione |
|---|---|
| **CONFIRMED** | 0 violazioni di H1 su tutti i CLAIM rappresentabili, ≥ 30 CLAIM, 0 verdetti cambiati |
| **REJECTED** | ≥ 1 violazione di H1 |
| **INCONCLUSIVE** | < 30 CLAIM |
Si riportano: violazioni e margini per v1 e v2, H4, e per ogni violazione se (c) vale.

## 4. Potere e costo
Dal blind-4: ~59 CLAIM, ~8 sotto-supporto attesi. Zero violazioni su ~59 limita il tasso al 5 %
(regola del tre). Costo ~90 min (discovery 120 × 38 s + annotazione). Eccezione motivata.

## 5. Cosa NON dimostra
Nulla sui termini fuori libreria; nulla sul pavimento di selezione (§4 della nota, non
implementato); una sola replica; solo pipeline termica.

## 6. Ledger
| data | voce |
|---|---|
| 2026-09-07 | creata prima della generazione; diagnostica sui 22 casi aperti allegata come motivazione, non come evidenza. |
| 2026-09-07 | **Blind-5 eseguito e sbendato**: 120 casi, 5.462 s; 50 CLAIM, 7 sotto-supporto, **0 violazioni di H1 con k=1 proiettato**, 0 verdetti cambiati, X mediana 1,4 %. H2: margini v2 k=1 (3,49×) ≈ v1 k=2 (3,07×), come previsto. H4: 7/7 termini statisticamente visibili. **CONFIRMED**. Claim card `CLAIM_CARD_BLIND5_LIMITE_PROIETTATO_2026-09-07.md`. |
