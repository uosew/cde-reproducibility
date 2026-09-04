# Preregistrazione — Stage 3B: discriminazione del surrogato su traiettoria singola

**Data:** 2026-08-24
**Commit di congelamento:** `79cbfe70`
**Tentativo precedente citato:** Stage 3A, `NOT_PROMISING`

---

## 1. La domanda primaria

> Il drift dei coefficienti e' sistematicamente **ordinato** con l'ampiezza nei
> surrogati fuori libreria, ma non nelle leggi vere, **a parita' di dominio
> osservato e rumore**?

Lo stage 3A ha misurato la **magnitudine** del drift e ha fallito il proprio
criterio congelato. Questo stage misura la **monotonia**: adimensionale, e
insensibile al livello di rumore — che era la tensione irrisolta fra le due
statistiche possibili in 3A (normalizzare cancella il segnale, non normalizzare
lo confonde con la difficolta' di fit).

`CLAIM_EFFETTIVO` e la pipeline di produzione **non vengono toccati** durante
questo stage.

---

## 2. Il pannello: 8 sistemi, disgiunto dallo stage 3A

| caso | classe | legge | fuori libreria |
|---|---|---|---|
| `case_01` | SURROGATO | `0.060 u_xx + 0.70 sin(u)` | `u - u³/6` |
| `case_02` | SURROGATO | `0.070 u_xx + 0.60 tanh(u)` | `u - u³/3` |
| `case_03` | SURROGATO | `0.065 u_xx + 0.65 u/(1+u²)` | `u - u³ + u⁵` |
| `case_04` | SURROGATO | `0.075 u_xx + 0.35 sinh(u)` | **`u + u³/6`** |
| `case_05` | CONTROLLO_NONLIN | `0.060 u_xx + 0.95 u − 0.85 u³` | — |
| `case_06` | CONTROLLO_NONLIN | `−uu_x + 0.070 u_xx` | — |
| `case_07` | CONTROLLO_LIN | `0.065 u_xx − 0.45 u` | — |
| `case_08` | CONTROLLO_LIN | `−0.55 u_x + 0.075 u_xx` | — |

`sinh` e' incluso apposta: la sua correzione cubica ha **segno opposto** alle
altre tre. E' una predizione falsificabile che una statistica di sola
magnitudine non potrebbe verificare.

---

## 3. L'appaiamento, imposto e non sperato

E' il difetto che ha reso 3A non pulito: le sue sonde coprivano rapporti di
ampiezza fra 1.07 e 1.94, e un drift-per-ampiezza fra range cosi' diversi non
e' confrontabile.

| dimensione | come viene imposta |
|---|---|
| **range di ampiezza** | banda `[m/√1.5, m·√1.5]` attorno alla mediana di ciascun sistema: rapporto alto/basso **esattamente 1.5 per tutti, per costruzione** |
| **SNR** | stesso rumore relativo `σ = 0.005` per tutti; livella anche la difficolta' di fit, perche' il residuo diventa dominato dal rumore |
| **numero di finestre** | 600 generate, poi **esattamente 180** sottocampionate in banda per ogni sistema |
| **difficolta' di fit** | misurata; se i residui mediani dei due gruppi differiscono di oltre **10×**, l'appaiamento e' fallito |
| **condizione iniziale** | stessa famiglia (3 modi) e stessa finestra temporale per tutti |

---

## 4. Cosa e' congelato

| oggetto | valore |
|---|---|
| commit | `79cbfe70` |
| python / numpy / scipy | 3.13.10 / 2.5.1 / 1.18.0 |
| generatore | sha256 `5c4daf361d947b28beb4ad3e8a3b47ecf17ecd6e5292f251111f996ec5007a90` |
| runner | sha256 `f76bc11b0ee966cb83f7bea4ae57c57b80d64b90171c88edaec9a5a6f9af4eea` |
| scorer | sha256 `851b6c7a0a2a66cb981148b277be86c497879e4d6316ceadff5c5c7d599e6590` |
| pannello | sha256 `ab4cf65fe010c05ec700f1c387ce6b964603da61d87692eebf4ace89adb8f244` |

Parametri: `K_RAW=600`, `RAPPORTO_BANDA=1.5`, `N_BIN=6`, `N_MIN_BANDA=180`,
`R_PERM=300`, `R_BOOT=300`, `SEME=55000`, `wx=1.0`, `wt=0.30`, `σ=0.005`.
Libreria invariata (7 termini). Selezione del supporto: stability selection
v1.1 invariata.

---

## 5. Statistica primaria, e il nullo

**ρ_max** = massimo sui coefficienti selezionati di `|Spearman(ampiezza media
del bin, β̂)|` su **6 bin equinumerosi** ordinati per ampiezza.

**Il nullo e' interno al sistema**, non teorico: le stesse finestre vengono
assegnate ai bin **a caso**, con gli stessi conteggi, 300 volte. Con 6 punti la
formula asintotica di Spearman non e' affidabile, e un nullo interno controlla
anche il condizionamento specifico di quel sistema. Il p-value e' empirico:
`p = (1 + #{null ≥ osservato}) / (1 + n_null)`.

**Stabilita'**: bootstrap entro bin, 300 ricampionamenti, CI95 su ρ_max.

---

## 6. Criteri, congelati

### Verifica di appaiamento, che precede tutto

`NOT_OBSERVABLE` se anche una sola condizione cade:

- **A1** ogni sistema produce una statistica (stato `OK`);
- **A2** ogni sistema ha ≥ 180 finestre nella banda comune;
- **A3** il rapporto fra i residui mediani di surrogati e controlli ≤ **10**.

`NOT_OBSERVABLE` **non** e' una risposta negativa alla domanda scientifica: e'
la dichiarazione che questo pannello non la interroga.

### Criterio primario

```
PROMISING  ⟺  tutti i surrogati hanno p ≤ 0.05
          AND tutti i controlli hanno p > 0.05
          AND min(ρ_max surrogati) > max(ρ_max controlli)
```

Altrimenti **NOT_PROMISING**.

### Endpoint secondario, dichiarato NON decisivo

Il ρ firmato di `sinh(u)` dovrebbe avere segno opposto a quello dei tre
surrogati con correzione cubica negativa. **Se il primario fallisce, questo non
lo salva**: viene riportato come osservazione, mai come verdetto. E' la regola
che lo stage 3A ha reso necessaria — li' il drift assoluto separava di tre
ordini di grandezza e il criterio congelato diceva `NOT_PROMISING`, e ha vinto
il criterio.

---

## 7. Cosa questo stage NON potra' dimostrare

- **Non e' una conferma.** E' uno screening: `PROMISING` autorizza a progettare
  un blind confermativo (Stage 3C) su casi nuovi, **non** a integrare la
  capacita' nella pipeline.
- **Non stabilisce un tasso.** Otto sistemi, quattro per gruppo: con `α=0.05`
  per test e quattro test per lato, il criterio e' una congiunzione, non una
  stima, e non e' corretto per molteplicita'.
- **Non generalizza oltre il rapporto di banda 1.5.** Con una banda piu'
  stretta il drift atteso e' minore; con una piu' larga il pannello non sarebbe
  appaiabile su tutti i sistemi.
- **Non riguarda i dati reali**, ne' piu' dimensioni spaziali, ne' condizioni al
  contorno non periodiche.
- **Non tocca `CLAIM_EFFETTIVO`.** Qualunque sia l'esito, il comportamento
  ufficiale del CDE resta quello congelato in
  `SEMANTICA_VERDETTI_CDE_2026-08-24.md`.

---

## 8. Regole di esecuzione

1. Dopo questo commit non si toccano codice, soglie, semi o criteri.
2. Nessuna reinterpretazione post-hoc: se il criterio primario fallisce, il
   verdetto e' negativo anche se emergono metriche alternative interessanti.
3. Se `PROMISING`, **non** si integra: si progetta lo Stage 3C confermativo su
   casi nuovi.
4. Qualunque verdetto chiude lo stage.
