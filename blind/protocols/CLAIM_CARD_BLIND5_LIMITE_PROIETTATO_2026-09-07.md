# Claim card — Blind-5: limite di risoluzione proiettato, k = 1

**Prereg:** `PREREGISTRAZIONE_BLIND5_LIMITE_PROIETTATO_2026-09-07.md`, sha256 `7d72ce3ddfe1…`,
commit `69625086`, prima della generazione. **Motivazione teorica:**
`NOTA_FORMALIZZAZIONE_LIMITE_RISOLUZIONE_2026-09-07.md`.
**Cecità:** verità sigillata (sha `8359aa64…` nell'envelope) e committata prima del run
(`dae60839`); discoverer V13 invariato, nessun riferimento a `sealed/` nel sorgente;
predizioni hashate (`55e78c54…`) prima dell'apertura; scorer con 5 mutation test mordenti,
committato durante il run e prima di leggere una predizione (`495761e5`).
**Artefatti:** `cde_blind5_out/{sealed,verdicts_mac.json,verdicts_annotati.json,scoring.json}`.

## Verdetto: **CONFIRMED**

| | |
|---|---|
| casi | 120 rappresentabili (A, B, C, F × 30), semi 740000/750000 mai usati |
| CLAIM | **50** (≥ 30 richiesti) — 43 esatte, 7 false strette |
| false strette | tutte sotto-supporto, stessa classe C dei blind precedenti |
| **violazioni di H1** (coefficiente vero ≥ c_min proiettato) | **0 / 7** |
| verdetti cambiati (H3) | **0** |
| X mediana | 1,4 % |
| durata | 4.666 s discovery + 796 s annotazione |

## Il confronto che la campagna doveva fare

| limite | violazioni | margine mediano | margine minimo |
|---|---|---|---|
| v1 euristico, `‖r‖/‖a_t‖`, **k = 2** (in produzione) | 0 / 7 | 3,07× | 1,69× |
| **v2 proiettato, `‖r‖/‖ã_t‖`, k = 1** | **0 / 7** | 3,49× | 1,85× |

**Su questo pannello entrambi i limiti sono sound**: il blind-5 non discrimina sulla soundness.
Discrimina su ciò che H2 prevedeva e che è il punto della formalizzazione: **il v2 raggiunge la
stessa copertura con k = 1**, cioè senza fattore di sicurezza inspiegato, e con margini
comparabili (3,49× contro 3,07×). Il fattore 2 dell'euristica non era una scelta prudente:
era `1/√(1 − ρ_t²) ≈ 2,2`, la collinearità del termine mancante con il supporto, compensata a
mano. La proiezione la mette dove appartiene, nel denominatore.

## H4: la risoluzione della claim è di selezione, non di rumore
Su **7 termini mancanti su 7** la regressione parziale dà `|ĉ_t| > 2·se`: i dati vedevano il
termine. A scartarlo è stata la regola di selezione (soglia relativa, frequenza di stabilità),
non il rumore. Replica il 22/22 della diagnostica sui casi aperti. Conseguenza per il paper:
`c_min` va presentato come **inviluppo del residuo**, non come intervallo di confidenza, e la
formalizzazione completa somma due pavimenti (selezione e rumore) di cui qui è implementato
solo il secondo.

## Cosa NON dimostra
- Solo termini **dentro la libreria**: un surrogato fuori libreria non ha `f_t` e resta materia
  del cancello di ampiezza.
- 0 violazioni su 50 claim limita il tasso al **6 %** (regola del tre): seconda replica
  sigillata del limite, non una proprietà validata. Nel registry: `SUPPORTED`.
- Il pavimento di selezione (§4 della nota) non è implementato né misurato.
- Solo pipeline termica; sulla pipeline PDE la formula è identica ma la soundness non è misurata.
- Il pannello ha 7 casi di sotto-supporto: pochi. Un pannello arricchito in classe C darebbe
  più potere allo stesso costo.
