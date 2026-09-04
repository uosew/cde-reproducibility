# Claim card — CDE_V8_AVVERSARIALE_SEMI_NUOVI_V0

**Verdetto:** REPLICA

**Data:** 2026-08-25
**Preregistrazione:** `PREREGISTRAZIONE_V8_AVVERSARIALE_2026_08_25.md`, committata
(`15626f1e`) prima di eseguire un solo seme. Driver sigillato `cfa36ef6`
(`a0199007`). Motore `4a2181b8dbeda428`, unica versione mai esistita nella
storia del repository, eseguito senza modifiche.
**Artefatti:** `cde_v8_avversariale_v0/risultati.json`, per-seme in
`cde_v8_avversariale_v0/seed_2*/` e `a2_seed_2*/`.

---

## Che cosa afferma

La claim `CONFERMATA` della scoperta weak-form V8 **regge su venti semi mai
visti** (201–220), scelti apposta per romperla, con le soglie congelate il
4 agosto e non ridiscusse.

| gate | risultato | soglia congelata |
|---|---|---|
| `S1` recupero esatto, rumore 0 | **20/20** su tutti e 4 i sistemi | ≥ 19/20 |
| `S2` recupero, rumore 10% | **20/20** su tutti e 4 i sistemi | ≥ 15/20 |
| `S3` falsi positivi sui nulli | **0/800 · FDR 0,0** | ≤ 0,05 |

Con i 20 semi della caratterizzazione, la claim ora regge su **40 semi**, di
cui 20 avversariali. Zero fallimenti su 160 combinazioni sistema×seme×gate.

## A2 — il confine, misurato per la prima volta *(descrittivo, senza soglie)*

Oltre il perimetro della claim (rumore > 10%), su 5 semi (201–205):

| sistema | 15% | 20% | 30% |
|---|:--:|:--:|:--:|
| Allen-Cahn | 5/5 | 5/5 | **5/5** |
| KdV | 5/5 | 5/5 | **5/5** |
| Fisher-KPP | 5/5 | 5/5 | 3/5 |
| Burgers | 5/5 | 4/5 | 3/5 |

Tre letture: **il margine reale è almeno 3× la claim dichiarata** — nessun
sistema cede sotto il 20%; **il confine è una zona stocastica, non una
soglia** — chi cade e a che livello cambia col seme; **Allen-Cahn e KdV non
sono mai caduti** nemmeno al 30%, quindi il loro punto di rottura resta non
misurato anche adesso.

## Fallimento tecnico dichiarato, e riparazione

Le prime cinque run di A2 sono morte all'import: la copia del motore con
`SIGMAS` estese stava fuori dalla directory dei moduli fratelli. **Zero
osservazioni prodotte** (tracce in `a2_seed_2*_fallita_import/`). Riparata
collocando la copia accanto ai fratelli (impronta `fe445ae0e4ed6538`,
registrata in `risultati.json` → `A2_riparazione`). A2 è descrittivo e senza
soglie (§5): la riesecuzione non riapre alcuna decisione. Riportato per §7.

## Le attese registrate: una giusta, una sbagliata

- **A1 = REPLICA: giusta.** Prima previsione registrata corretta dopo cinque
  campagne consecutive andate diversamente dall'attesa.
- **«KdV cede per primo in A2»: sbagliata.** KdV è imbattuto fino al 30%; a
  cedere sono Fisher-KPP e Burgers. La derivata terza non è il punto debole
  che credevo — il ragionamento «più derivate = più fragile» non regge sui
  dati, e il precedente sulle attese resta pessimo: 1 su 6.

## Che cosa NON afferma

- Non estende la claim oltre il 10% di rumore: A2 è descrittivo, la
  formulazione pubblica resta «fino al 10%».
- Non dice nulla su dati reali: `CDE_REAL_THERMOGRAPHY_V0` resta `REJECTED`
  e questo perimetro è tutto su soluzioni sintetiche.
- I conteggi A2 sono su 5 semi: bastano per «il margine è largo», non per
  stimare frequenze di rottura per livello.

## Provenienza

`runtime_guard` PASS · motore `4a2181b8dbeda428` verificato con arresto
bloccante · soglie **rilette dall'artefatto della campagna originale**, non
ricopiate · artefatti sigillati della campagna madre salvati, ripristinati e
verificati per impronta prima e dopo (**intatti** in entrambe le esecuzioni) ·
semi 201–220 disgiunti da tutti i semi mai usati (7, 11, 101–120) · nessun
seme ritentato · `.venv313`, Python 3.13.10 · durata A1 3,89 h + A2 ~1 h.
