# Claim card — riga `Exact support recovery` della capability matrix V10

**Verdetto:** NOT_TESTABLE

La riga resta `PARTIAL`, e questo documento spiega perche' non puo' diventare
`SUPPORTED` con il pannello attuale — non perche' il CDE fallisca, ma perche' la
domanda non e' misurabile con 26 casi.

| | |
|---|---|
| riga | `Exact support recovery`, oggi `PARTIAL` |
| regola che la governa | `CDE_V10_CAPABILITY_MATRIX_V0.py:85` — `PARTIAL if fdr > 0 else SUPPORTED` |
| evidenza sorgente | `cde_v10_wrong_library_v0_out/results.json` |
| analisi | `CDE_V10_FDR_OBSERVABILITY_V0.py`, deterministica: due esecuzioni, hash `d07cac9c81ea44fc` entrambe |
| runtime | `.venv313`, Python 3.13.10, numpy 2.5.1, runtime guard superato |

---

## 1. Cosa affermerebbe la riga se fosse vera

> Posto davanti a una libreria che **non contiene** i termini veri, il CDE
> rifiuta tutti i sostituti: nessun termine spurio scende sotto il gate di fit.
> FDR strutturale zero, non soltanto basso.

E' la formulazione implicita nella regola che calcola lo stato: `fdr > 0` basta a
declassare la riga, quindi `SUPPORTED` significa **esattamente zero**.

---

## 2. Perche' non e' misurabile

Il test e' un leave-one-out: si toglie un termine vero dalla libreria e si osserva
se il motore si astiene o inventa un sostituto. Oggi: **4 sostituti falsi su 26
casi**, FDR 0.1538.

**La stima attuale e' larga.** Intervallo esatto di Clopper-Pearson:
`[0.0436, 0.3487]`. Su questo pannello non sappiamo con precisione nemmeno quanto
sia grave adesso.

**Il bersaglio non e' raggiungibile.** Se dopo un miglioramento osservassimo
**zero** sostituti su n casi, l'FDR vero massimo compatibile al 95% sarebbe:

| n | FDR vero ≤ |
|---|---|
| **26** (pannello attuale) | **10.9%** |
| 50 | 5.8% |
| 100 | 3.0% |
| 300 | 1.0% |

Con i 26 casi disponibili, **un risultato perfetto lascerebbe l'FDR vero fino al
10.9%** — peggiore del limite inferiore dell'intervallo attuale. L'esperimento
non potrebbe distinguere il successo dal fallimento.

Per soglie sensate servirebbero **~59 casi** (FDR ≤ 5%), **~149** (≤ 2%), **~299**
(≤ 1%).

---

## 3. Perche' il pannello non si puo' ampliare senza cambiarlo

I 26 casi sono **13 combinazioni (sistema, termine vero rimosso) × 2 livelli di
rumore**:

| sistema | termini veri rimovibili |
|---|---|
| allen_cahn | `u`, `u^3`, `u_xx` |
| fisher_kpp | `u`, `u^2`, `u_xx` |
| burgers | `u_xx`, `uu_x` |
| kdv | `u_xxx`, `uu_x` |
| ks | `u_xx`, `u_xxxx`, `uu_x` |

Il numero di combinazioni e' fissato dai termini veri delle cinque equazioni.
**Aggiungere livelli di rumore gonfia il denominatore senza aggiungere
informazione**: i due sigma attuali danno esiti identici su tutte e 13 le
combinazioni. Sarebbe pseudo-replicazione — lo stesso errore che H003 esisteva per
evitare, dove 5 permutazioni non trasformavano 64 dataset in 320 unita'.

Arrivare a 59 casi richiede **altre equazioni**, cioe' un pannello diverso e un
esperimento diverso.

---

## 4. Il risultato che l'FDR aggregato nascondeva

**Tutti e quattro i fallimenti stanno su `fisher_kpp`**, su due soli termini —
`u^2` e `u_xx` — e a **entrambi** i livelli di rumore.

| sistema | casi | fallimenti |
|---|---|---|
| allen_cahn | 6 | 0 |
| **fisher_kpp** | 6 | **4** |
| burgers | 4 | 0 |
| kdv | 4 | 0 |
| ks | 6 | 0 |

Le altre quattro equazioni si astengono **22 volte su 22**. Il numero 4/26 non
descrive una tendenza del motore a inventare sostituti: descrive che su FKPP,
togliendo `u^2` o `u_xx`, esiste un sostituto che passa il gate — in modo
deterministico, con e senza rumore.

**E' un fenomeno localizzato e riproducibile, non un tasso.** Un FDR aggregato lo
nascondeva dietro una media.

---

## 5. Cosa questo NON dimostra

- **Non dimostra che l'FDR sia accettabile.** 4/26 resta un fallimento reale, e
  l'intervallo arriva al 35%.
- **Non dimostra che il sostituto su FKPP sia inevitabile.** Che `u^2` e `u_xx`
  abbiano un sostituto genuinamente indistinguibile e' un'ipotesi suggerita da
  questi dati, mai testata.
- **Non dice nulla sulle altre quattro equazioni** oltre al fatto che qui non
  falliscono: 22 astensioni su 22 con un pannello cosi' piccolo sono compatibili
  con un FDR vero non trascurabile.
- **Non riguarda i dati reali**: il leave-one-out gira su sistemi sintetici.

---

## 6. Cosa farei dopo, e perche' non l'ho fatto qui

La domanda che vale non e' «quanto vale l'FDR» ma **«perche' FKPP»**: se si
dimostrasse che quei due termini hanno un sostituto indistinguibile con la
libreria data, la riga chiuderebbe con un limite **spiegato** invece che
quantificato — e varrebbe piu' di un FDR abbassato allargando il denominatore.

E' un esperimento nuovo, con un suo pannello e una sua preregistrazione. Aprirlo
dentro questa chiusura significherebbe confondere due domande.

---

## 7. Nota sugli artefatti

Il ciclo prevede runner e analyzer separati con mutation test. Qui **non e' stato
eseguito alcun esperimento**: la chiusura avviene al passo 2, quando il controllo
di osservabilita' stabilisce che nessun esito potrebbe dimostrare la claim. Gli
artefatti sono percio' quattro invece di cinque — analisi, claim card, voce di
ledger, commit — e l'assenza del runner non e' una scorciatoia ma la conseguenza
di non aver avuto nulla da eseguire.

---

## 8. Ledger

| data | voce |
|---|---|
| 2026-08-24 | riga chiusa `NOT_TESTABLE` per la formulazione «FDR zero»: con 26 casi anche un risultato perfetto lascerebbe l'FDR vero fino al 10.9%. Il pannello e' limitato a 13 combinazioni dai termini veri di 5 equazioni; ampliarlo col rumore sarebbe pseudo-replicazione. Stato nella matrix invariato a `PARTIAL`. Localizzazione registrata: 4/4 fallimenti su fisher_kpp, termini `u^2` e `u_xx`, entrambi i sigma. |
