# Audit del processo di scoperta del CDE — 2026-09-02

**Oggetto:** `CDE_PDE_DISCOVERY_V8.py` (motore congelato), `CDE_PDE_PIPELINE_GATED_V0.py`
(pipeline di produzione), `CDE_BLIND_PDE2_RUNNER_V0.py` (codice validato dal blind 2),
`CDE_V8_AVVERSARIALE_V0.py` (campagna «0/800 nulli»), `CDE_V13_BLIND_GENERATOR_V0.py`.
**Metodo:** lettura integrale + verifica empirica di ogni sospetto prima di chiamarlo errore.
**Esito:** 6 errori CONFERMATI (riproducibili), 4 rischi SOSPETTI (richiedono campagna).
Le correzioni strutturali sono in `CDE_PDE_PIPELINE_GATED_V1.py`; **nessuna soglia cambia**.

---

## A. Errori confermati

### E1 — La pipeline di produzione non è il codice validato (ordine dei cancelli)
- **Dove:** `CDE_PDE_PIPELINE_GATED_V0.py:183-206` contro `CDE_BLIND_PDE2_RUNNER_V0.py:142-156`.
- **Fatto:** il blind 2 (PASS, 4 falsi positivi → 0) valida l'ordine *ampiezza → scambio*.
  La V0, «integrazione senza toccare V8», applica *scambio → ampiezza*.
- **Conseguenza:** quando entrambi falliscono, il verdetto cambia nome: il validato dice
  `ABSTAIN_AMPIEZZA`, la produzione `NOT_IDENTIFIABLE`. Riprodotto nell'autotest V1
  (colonne correlate a 0,99983, fit 0,036).
- **Perché conta:** la semantica congelata distingue i due verdetti; la matrix legge i
  falsi positivi dagli artefatti del blind 2, cioè da un codice **diverso** da quello
  che gira. Il PASS del blind 2 non copre la V0.
- **Correzione (V1, F1):** ordine allineato al validato.

### E2 — Seme di sottocampionamento fisso per ogni caso
- **Dove:** `CDE_PDE_PIPELINE_GATED_V0.py:137,154` (`seme: int = 7`); il blind 2 usa
  `seme + 7` per caso (`CDE_BLIND_PDE2_RUNNER_V0.py:119`).
- **Conseguenza:** in produzione ogni caso usa lo stesso disegno di 100 sottocampioni;
  le «frequenze di stabilità» sono confrontabili fra casi solo per coincidenza, e un
  disegno sfortunato si ripete ovunque. Secondo punto in cui la V0 diverge dal validato.
- **Correzione (V1, F3):** seme obbligatorio, per caso.

### E3 — Colonna nulla → `max_corr = NaN` → cancello aperto in silenzio
- **Dove:** `CDE_PDE_PIPELINE_GATED_V0.py:99-103`, `CDE_BLIND_PDE2_RUNNER_V0.py:99`.
- **Verifica:** colonna `u_xxx` a zero → `max_corr = nan`, `nan >= 0.9999` è `False`.
- **Scenario:** feature identicamente nulla (campo costante in x, o bump troncato):
  il condizionamento non viene mai valutato e la pipeline procede al fit.
- **Correzione (V1, F2):** colonne nulle escluse e dichiarate; `assert` di finitezza.

### E4 — Gli «800 nulli» condividono 10 flussi casuali
- **Dove:** `CDE_PDE_DISCOVERY_V8.py:405-410` (`default_rng(1000 + 97*ns …)`,
  `default_rng(555 + ns)`: costanti, indipendenti da `seed`);
  `CDE_V8_AVVERSARIALE_V0.py:207` somma `nulls.n_runs` di `run_system` → 20 semi × 4
  sistemi × 10 nulli = 800.
- **Conseguenza:** su 20 semi «mai visti», permutazioni temporali, fasi dei surrogati e
  sottocampioni della selezione sono **identici**; varia solo il campo `U`. Il «0 su 800»
  è vero come conteggio, ma i nulli non sono 800 prove indipendenti del braccio nullo:
  sono 80 campi × 10 disegni fissi. Viola lo spirito del §5 del protocollo
  («cinque permutazioni non trasformano 64 dataset in 320 osservazioni»).
- **Correzione (V1, F5):** `braccio_nullo(…, seme)` con flussi derivati dal seme di
  campagna. V8 resta congelato; le campagne future usano V1.

### E5 — Un tasso di falsi positivi chiamato FDR
- **Dove:** `CDE_PDE_DISCOVERY_V8.py:428` (`fdr = false_discoveries / n_runs`), ripetuto
  nella docstring (riga 26) e nel titolo della campagna avversariale.
- **Fatto:** il denominatore sono le run nulle, non le scoperte. È un FPR sui nulli
  (errore di tipo I), non un *false discovery rate*. La riga «FDR observability» della
  matrix è già `NOT_TESTABLE` per questo motivo; il nome però resta negli artefatti e
  nella nota arXiv.
- **Correzione (V1, F5):** il campo si chiama `fpr_nulli` con nota esplicita.

### E6 — Due margini diversi per la stessa soglia, misurati su un solo pannello
- **Dove:** `CDE_PDE_PIPELINE_GATED_V0.py:72` («margine 2,2e-05») contro
  `CDE_BLIND_PDE2_RUNNER_V0.py:76-79` («0,999871, cioè 1,3e-04 sotto»).
- **Fatto:** `SOGLIA_CORR = 0,9999` è stata scelta prima del blind 2 e ha retto per un
  margine dell'ordine di 1e-4 su **un** decoy identificabile. Non esiste una
  distribuzione misurata di `max_corr` su decoy identificabili e non: la soglia non è
  osservabilmente calibrata (violazione della regola «congelare una soglia senza aver
  verificato che sia osservabile»).
- **Correzione:** dichiarata in V1 (`MARGINE_SOGLIA_CORR_DICHIARATO`), **non** corretta:
  cambiarla richiede una campagna con pannello nuovo.

---

## B. Rischi sospetti (richiedono campagna preregistrata; NON corretti qui)

### S1 — Finestre sovrapposte: la stability selection non sottocampiona unità indipendenti
- **Misurato:** K=200, wx=1, wt=0,3 su [0,2π)×[0,2]: **50,8 %** delle coppie di finestre
  si sovrappone (10 113 su 19 900); area finestra / dominio = 0,21.
- **Rischio:** B=100 sottocampioni al 60 % di righe fortemente correlate sovrastimano
  la frequenza di selezione; la soglia 0,8 potrebbe essere permissiva. Effetto non
  misurato. V1 riporta la frazione (F6) come diagnostica.

### S2 — Il cancello di ampiezza non è mai stato provato oltre il 2 % di rumore
- **Fatto (corretto il 2026-09-02, dopo un grep sul generatore sbagliato):** il pannello
  del blind 2 contiene rumore su alcuni casi (`sigma` 0,01 e 0,02, `CDE_BLIND_PDE2_GENERATOR_V0.py:204-224`);
  nessun caso a 5-10 %. Il gate confronta un residuo relativo con 0,05 fisso.
- **Rischio:** una legge **vera** a rumore 5-10 % può superare 0,05 sul secondo regime e
  finire `ABSTAIN_AMPIEZZA` (falso negativo), e la semantica dichiara già che un
  surrogato a ampiezza *minore* passa (falso positivo). Da misurare per stadi.

### S3 — Soglia di collinearità: vedi E6, la parte sperimentale
- Serve la distribuzione di `max_corr` su decoy identificabili e degeneri, pannello
  nuovo, prima di dire che 0,9999 è una soglia e non un numero.

### S4 — Libreria fissa a 7 termini
- La classe di fallimento del blind 1 (`sin u` fuori libreria) resta aperta per
  costruzione: il gate di ampiezza la sposta, non la chiude (semantica §6). Non è un bug,
  è il confine della claim; va tenuto scritto accanto a ogni `CLAIM`.

---

## C. Cosa è stato fatto in questa sessione

| artefatto | contenuto |
|---|---|
| `CDE_PDE_PIPELINE_GATED_V1.py` | F1-F6; soglie importate dalla V0 e verificate con `assert`; autotest 13/13, inclusi i due che dimostrano E1 ed E3 sulla V0 |
| `CDE_PIPELINE_REPLAY_BLIND2_V0.py` | regressione V0 e V1 sul pannello sigillato del blind 2, caso per caso, contro il braccio `corretto` |
| questo documento | |

**Cosa NON è stato fatto, e perché:** nessuna soglia toccata; nessuna campagna nuova
(S1-S3 richiedono preregistrazione hashata prima delle run, e potere calcolato prima
delle soglie, come da `FAST_EXPERIMENT_PROTOCOL_V1.md`). La matrix **non cambia** con
questa sessione: le due righe PARTIAL restano tali finché una campagna blind nuova non
usa la V1 come braccio di produzione.

## D. Ordine proposto per il seguito
1. Replay blind 2: V1 deve riprodurre il braccio validato 23/23 (in corso).
2. Stage 1 (screening, ≤15 min) su S2: legge vera con rumore 1-10 % contro gate di ampiezza.
3. Stage 1 su S3: distribuzione di `max_corr` su 30 decoy nuovi.
4. Solo dopo: campagna blind 3 con V1 in produzione → le due righe PARTIAL possono muoversi.

---

## E. Esito del replay sul pannello sigillato del blind 2 (752 s)

| pipeline | divergenze dal braccio `corretto` validato |
|---|---|
| V0 (produzione) | **0 / 22** |
| V1 | **0 / 22** |

Tutti e 22 i verdetti riprodotti da entrambe (10 CLAIM, 4 NOT_IDENTIFIABLE, 6
astensioni fra ampiezza e preflight, 2 preflight chiusi). Lettura onesta:

- **E1 ed E2 sono latenti su questo pannello**: nessun caso fa fallire insieme il test
  di scambio e il cancello di ampiezza, e il seme fisso non ha cambiato alcun supporto.
  La divergenza è reale (autotest), ma il PASS del blind 2 **non la esclude**: la esclude
  solo perché il pannello non la sollecita. Un pannello nuovo può farlo.
- **La V1 non altera nessun verdetto validato**: le correzioni F1-F6 sono a costo zero
  sulla evidenza esistente e possono sostituire la V0 in produzione senza riaprire il
  blind 2.
- **S1 confermato anche sui casi reali**: frazione di finestre sovrapposte fra 0,48 e
  0,55 su tutti i 19 casi che arrivano alla selezione (`replay_pipeline_V0_V1.json`).

---

## F. Prima run di produzione con la V1 (`CDE_PRODUZIONE_V1_RUN_V0.py`, 1197 s)

Regressione dichiarata, non cieca: 4 sistemi a verità nota × 5 livelli di rumore, rumore
su **tutte e tre** le traiettorie, preflight non-oracolo, decisione V1, nulli a semi
indipendenti (`cde_produzione_v1_out/claim_card.md`).

| | CLAIM corretti | falsi positivi | astensioni | nulli |
|---|---|---|---|---|
| totale | **19 / 20** | **0** | 1 | **0 / 40** |

Ogni CLAIM ha supporto esatto; errore massimo sui coefficienti 1,56 % (KPP al 10 %).
KdV, il sistema di transfer, regge fino al 10 % con errore 0,95 %.

**L'unica astensione è il falso negativo S2, materializzato.** Allen-Cahn al 10 %:
supporto esatto, errore 2,15 %, residuo di fit 0,019 e di transfer 0,012, ma residuo sul
secondo regime **0,0536 contro il gate 0,05**: la legge vera respinta per il 7 % di
margine. Il gate di ampiezza confronta un residuo che cresce col rumore contro una soglia
che non ne tiene conto. Sbaglia nella direzione prudente, ma sbaglia, e ora è misurato.
La correzione (soglia di ampiezza relativa al residuo di fit, o calibrata sul rumore
stimato) è una **modifica di soglia** e quindi passa da una preregistrazione, non da
questo documento.

---

## G. Aggiunte del 2026-09-03

### E7 — Soglie del preflight scritte a mano, scollegate dalla calibrazione
- **Dove:** `CDE_BLIND_PDE_RUNNER_V0.py:65-67` (`GATE_P1 = GATE_P2 = GATE_P3 = 0.05`) contro
  `cde_v10_nonoracle_preflight_v0_out/results.json` (`taus`: P1 0,271, P2 0,00044, P3 0,00045,
  calibrate come 3×max su σ=0 secondo la prereg del protocollo v2).
- **Fatto:** il runner blind usa un unico 0,05 piatto: **5× più severo** del tau_P1
  calibrato e **100× più lasco** dei tau_P2/P3. Il commento dice «come termografia»: il
  numero viene dal preflight sui dati reali, non da una calibrazione su questo dominio.
- **Conseguenza misurata:** P1 a 0,05 chiude leggi vere a 15 % di rumore che il fit
  recupererebbe (Stage 1 P1: 1/10; blind-3: vedi claim card). Non corretto qui: cambiare
  la soglia è materia di preregistrazione.

### Falsificato: «il preflight denso è più severo della discovery sparsa»
P3/fit fra 0,80 e 1,22 su 40 celle. P2 e P3 misurano il pavimento di rumore del fit e
chiudono dove il fit chiuderebbe. Registrato come negativo.

### Linea P1 su campo filtrato
Stage 1 `PROMISING` (Δ_FN +1, controlli 5/5), blind-3 **`INCONCLUSIVE`**: Δ CLAIM veri +1
su 25 celle, 0 falsi, tutte le guardie rispettate, ma 3 dei 4 casi che il filtro riapre
vengono poi chiusi da transfer, ampiezza o scambio. P1 non era il collo di bottiglia che
sembrava: a 15 % il sistema ha **più cancelli che chiudono insieme**, e riaprirne uno
sposta la chiusura al successivo. Vedi `CLAIM_CARD_BLIND3_P1_LP8_2026-09-03.md`.

### E8 — 703 verdetti ciechi non valutati per 30 giorni
- **Dove:** `cde_v13_blind_out/verdicts_{mac,win}.json` (2026-08-04) senza scorer fino al
  2026-09-03. **Conseguenza:** per un mese la caratterizzazione «zero claim false» ha poggiato
  su 60 opportunità mentre ne esistevano 423 già calcolate; sbendate, mostrano **14 claim
  false** (classe C, sotto-supporto). Un blind non sbendato non è evidenza in nessuna direzione.
- **Regola da aggiungere al protocollo:** una campagna cieca non è chiusa finché lo scorer non
  ha girato; il ledger non accetta verdetti senza sbendamento entro la campagna stessa.
- **Sigillo debole (E8-bis):** l'envelope V13 non registra lo sha della verità e verità/verdetti
  stanno nello stesso commit. Ogni generatore deve scrivere `truth_sha256` nell'envelope e la
  verità va committata **prima** dei verdetti, in un commit separato (V11 lo faceva).

### Seguito di E8 (2026-09-03): il limite di risoluzione dichiarato
La classe di fallimento della V13 (claim di sotto-supporto) ha una risposta misurata: ogni
CLAIM porta X = 2·ρ/‖b‖ e un coefficiente minimo rilevabile per termine. Blind-4 sigillato
(sha in envelope, verità committata prima del run: E8-bis corretto): 59 claim, 8 sotto-supporto,
**0 violazioni**, 0 verdetti cambiati → CONFIRMED come prima replica. La regola dell'audit:
una claim senza limite di risoluzione dichiarato afferma più di quanto i dati sappiano.
