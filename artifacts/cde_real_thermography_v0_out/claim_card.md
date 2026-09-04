# Claim card — CDE_REAL_THERMOGRAPHY_V0

**Verdetto:** REJECTED

Dati inadeguati alla libreria dichiarata. Data: 2026-08-07. Preregistrazione:
`PREREGISTRAZIONE_REAL_THERMOGRAPHY_2026_08_07.md`, congelata prima
dell'esecuzione. Esito previsto ed elencato in §4 fra i quattro legittimi.

## Cosa è stato fatto

Prima applicazione del CDE a **dati sperimentali reali**, misurati da terzi:
termografia pulsata su piastre CFRP/GFRP 300×300×2 mm, Mendeley Data
`10.17632/v4knrwgj9y.2` (CC BY 4.0), 2000 frame 512×512 in °C a 120/145 Hz.
Integrità: sha256 di tutte le sequenze verificati contro quelli pubblicati.

10 sequenze confermative su 5 piastre indipendenti (esclusa la traiettoria di
calibrazione dichiarata `CFRP-006 Front` e la sua gemella di lato), 5 tagli 1D
per sequenza su griglia fissa = **50 dataset**.

Core di selezione v1.1 **non modificato**: il runner importa
`CDE_THERMAL_DRESS_REHEARSAL_V0` e sostituisce solo il generatore con un loader.

## Verdetti preregistrati

| ID | Ipotesi | Esito | Numeri |
|---|---|---|---|
| R-P1 | il preflight apre i dati | **RESPINTA** | 0/10 sequenze, 0/50 tagli |
| R-S1 | supporto `{v, v_xx}` | non valutabile | 0 sequenze oltre il gate |
| R-S2 | segni fisici | non valutabile | 0 controlli possibili |
| R-T1 | transfer cross-piastra | **RESPINTA** | 0/32 coppie sotto il gate |
| R-N1 | nulli senza false discovery | **CONFERMATA** | **0 FD su 100** |
| R-I1 | identificabilità | non valutabile | 0 sequenze oltre il gate |
| R-M1 | α per materiale | non valutabile | nessun α stimato |

## Il limite, quantificato

Il gate di preflight è `P3 < 0.05` (holdout), ereditato e mai ricalibrato.

| statistica su 50 tagli | valore |
|---|---|
| P3 minimo (il taglio migliore) | **0.0780** |
| P3 mediano | 0.1519 |
| P3 massimo | 0.5751 |

Il taglio migliore manca il gate di un fattore **1.6×**; il mediano di 3.0×.
Residui di fit (senza gate) 0.116–0.689; residui di transfer 0.118–2.653.

Causa fisica misurata: dopo il flash il contrasto **spaziale** lungo i tagli è
0.06–0.17 °C, contro un rumore di camera di ~0.12 °C (deviazione standard del
frame pre-flash). Il segnale è dominato dal rilassamento attraverso lo spessore,
che in un modello 1D-in-x è puro decadimento; la diffusione **nel piano** —
l'unico termine che renderebbe il modello non banale — è sotto il rumore.

## Il risultato che vale più del verdetto

Senza il gate di preflight, la selezione avrebbe restituito supporti
**strutturalmente sbagliati con residui bassi**: `{v, v²}` in 6 sequenze su 10,
e in 4 casi supporti con 3–6 termini che includono `(v v_x)_x` e `v_x`.
Nessuno di questi contiene la coppia `{v, v_xx}` attesa dalla fisica.

È la prima volta che questa classe di falsa scoperta viene osservata **su dati
misurati** anziché iniettata in simulazione. La riproduce esattamente
l'ablation V10 del gate di preflight, che su dati sintetici riapriva
«2 config sottorisolte»: qui la stessa ablation avrebbe prodotto 10 leggi false
su 10 dataset reali.

In parallelo, i nulli restano puliti su dati reali rumorosi: **0 false
discovery su 100** (shuffle temporale + surrogati di fase, 10 per sequenza).

## Perimetro e claim vietati

- **Non** è una smentita della termografia pulsata né del dataset: quei dati
  sono stati misurati per rilevare difetti sottosuperficiali, non per
  identificare una PDE nel piano. L'inadeguatezza è rispetto al **nostro**
  scopo dichiarato.
- **Non** autorizza nessuna affermazione su diffusività, materiali, difetti,
  o su altre geometrie, spessori e regimi di eccitazione.
- **Non** è una validazione del CDE su dati reali: la capability matrix resta
  `NOT_TESTED` per la voce «validazione su dati sperimentali reali», ora però
  con un limite quantificato (fattore 1.6× sul preflight) invece che vuoto.
- Un secondo tentativo su questi stessi dati richiede una **nuova**
  preregistrazione che dichiari questo esito: riaggiustare finestre o soglie
  ora sarebbe una violazione della §4.

## Riproducibilità

- Ambiente: `.venv313` (py 3.13.10, numpy 2.5.1); replica su `.venv312`
  (py 3.12.12, numpy 2.5.1). Runtime guard superato (canary elisione numpy).
- Artifact: `results.json`, `results_py313.json`, `results_py312.json`,
  `evidence_envelope.json` (con sha256 dei risultati e di tutti gli zip sorgente).
- Dati grezzi non ridistribuiti: scaricabili dal DOI, verificabili con
  `data_real_thermography/FILE_INDEX.json`.

**Revisione umana richiesta: sì.**
