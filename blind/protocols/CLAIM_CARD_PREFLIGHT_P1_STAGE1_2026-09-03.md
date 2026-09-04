# Claim card — P1 del preflight su campo filtrato, Stage 1

**Prereg:** `PREREGISTRAZIONE_PREFLIGHT_P1_FILTRATO_2026-09-03.md`, sha256 `97ff647e255d…`,
commit `29693e5f`, prima di ogni run. **Artefatti:** `cde_preflight_p1_out/screening.json`
(18 celle, 889 s), `esito_stage1.json`. Analizzatore con 7 mutation test, tutti mordenti.

## Esito: **PROMISING** (P1-LP8 e P1-LP4). Scelto **P1-LP8** (§6, parità → numero già congelato).

| | FN su 10 leggi vere | controllo risoluzione (deve chiudere) | decoy aperti e affermati | regressioni |
|---|---|---|---|---|
| P1 grezzo | 1 | 5/5 | — | — |
| **P1-LP8** | **0 (Δ +1)** | **5/5** | 0 | 0 |
| P1-LP4 | 0 (Δ +1) | 5/5 | 0 | 0 |

Il falso negativo recuperato: quadratica 9102, σ=15 %, P1 0,0688 → LP8 0,0464; la
decisione controfattuale è CLAIM con supporto esatto ed errore 2,51 %. Sulle 5 griglie
sotto-risolte il filtro **non cambia P1 di un decimale** (0,25-0,91): la sensibilità che
serve è intatta.

## Da dichiarare
- **Stima di tempo sbagliata:** 889 s contro 600 dichiarati (+48 %), sotto l'arresto a
  +50 % per 31 s. Il costo per cella a 768 è ~60 s, non 50: le due varianti aggiungono
  quattro calcoli di feature. Va ridichiarato per il blind-3.
- **Entrambi i falsi negativi visti finora (9002 e 9102) sono della famiglia quadratica**
  (offset 0,5, ampiezza 0,2: colonne u², u³ dominate dall'offset). L'effetto potrebbe
  essere specifico di famiglia. Il blind-3 riporta per famiglia.
- LP8 e LP4 quasi identici (0,0464 / 0,0468): la parte di P1 sensibile al rumore sta
  in gran parte **sotto** Nx/8. Il filtro toglie ~1/3, non 3/4. Informazione, non esito.
- **E7 (nuovo, per l'audit):** il runner blind usa 0,05 piatto su P1/P2/P3; il NOP
  originale calibrava tau_P1 = 0,27 e tau_P2 = tau_P3 = 0,00044 (3×max su σ=0). Un
  numero scritto a mano, 5× più severo di P1 calibrato e 100× più lasco di P2/P3.

## Cosa NON dimostra
Vedi prereg §7. Uno Stage 1 non promuove: serve il blind-3 con verità sigillata.
