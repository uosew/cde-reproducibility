# Preregistrazione — CDE V11 Virtual Instrument Qualification (fase 1)

Data: 2026-07-31. Stato: **PREREGISTRATO PRIMA DI QUALUNQUE RUN V11**.
Obiettivo: non piu' verificare la legge del calore ideale, ma simulare
cio' che una camera termica reale puo' fare male e derivare, PRIMA
dell'acquisto, la specifica hardware minima quantitativa (mappa di
tolleranza strumentale -> hardware specification envelope).

## Base congelata

Configurazione GO del dress rehearsal V2 (commit b084b084): braccio
lineare (alpha=9.7e-5, beta=0.02), 5 IC a spot largo, analisi [10,70] s,
WX=0.08 m, 5 Hz, oggetto di riferimento nel frame, fit pooled IC0..3 +
holdout IC4, ladder v2 con swap relativo 2x. I 5 campi ideali sono
simulati UNA VOLTA (Nx=800) e riusati per ogni configurazione di
degradazione (solo la degradazione cambia).

## Assi di degradazione (gemello digitale) e valori di sweep — CONGELATI

Ogni asse varia da solo, il resto resta alla specifica base
(160 px, 5 Hz, NETD 0.3 C, quant 0.1 C, drift 0.2 C con riferimento,
PSF 0, jitter 0, dead 0, nonunif 0, moto 0, scala esatta, no sat):

| Asse | Valori di sweep |
|---|---|
| A1 pixel sul campione | 40, 80, 120, 160, 240, 320 |
| A2 PSF gaussiana [px] | 0, 1, 2, 4, 8 |
| A3 NETD/rumore [C] | 0.05, 0.1, 0.3, 0.5, 1.0 |
| A4 quantizzazione [C] | 0.01, 0.1, 0.5, 1.0 |
| A5 frame rate [Hz] | 0.5, 1, 2, 5, 8.7 (WT adattata: min(max(4, 22/Hz), 25) s, dichiarato) |
| A6 jitter timestamp [ms] | 0, 20, 50, 100, 200 (tempi veri jitterati, pipeline usa i nominali) |
| A7 deriva [C] (con riferimento; 10% differenziale non corretto) | 0, 0.2, 0.5, 1.0, 2.0 |
| A8 pixel morti [%] (ingestion: interpolazione lineare, dichiarata) | 0, 0.5, 2, 5 |
| A9 non-uniformita' emissivita' spaziale [%] | 0, 1, 3, 5, 10 |
| A10 moto lento campione/camera [px] | 0, 0.5, 1, 2 |
| A11 errore scala px/m [%] | 0, 1, 3, 5 (attesa analitica: alpha scala come (1+e)^2) |
| A12 saturazione clip [C] | nessuna, 60, 40 |

## Scenari combinati — CONGELATI

C1 rumore 0.5 + PSF 2; C2 deriva 1.0 + emissivita' nonunif 3%;
C3 2 Hz + jitter 100 ms; C4 moto 1 px + dead 2%;
C5 PSF 2 + quant 0.5 + rumore 0.5 (worst plausibile).

## Metriche per configurazione

Verdetto ladder pooled (CLAIM / NOT_IDENTIFIABLE / ABSTAIN_* /
REJECTED_*), errore relativo su alpha, supporto esatto {v, v_xx},
residuo holdout, preflight open (5/5 IC), nulli (2 per configurazione,
FD attesa 0).

## Regola di derivazione della specifica (dichiarata ORA)

Per ogni asse: soglia di qualifica = ultimo valore dello sweep con
verdetto CLAIM **e** |err alpha| < 5% **e** supporto esatto. La scheda
tecnica applica poi un margine di sicurezza 2x nella direzione
conservativa (es. NETD_max_spec = NETD_soglia / 2). Nessuna soglia
scelta a posteriori guardando i prezzi delle camere.

Output: `cde_v11_virtual_instrument_v0_out/results.json`
(tolerance_map per asse + combined) e `HARDWARE_SPEC_ENVELOPE.md`
generato con assert dagli stessi risultati.

## Fasi successive (dichiarate, non parte di questa run)

(2) blind synthetic challenge con generatore separato e modelli non
dichiarati; (3) emulatore del percorso dati (file radiometrici,
manifest, QC, parser) sulla pipeline definitiva; (4) procurement
acceptance test automatico (HARDWARE_ACCEPTED/CONDITIONAL/REJECTED);
(5) piano fisico congelato; poi preregistrazione hardware-agnostica
finale e, solo dopo, l'acquisto con addendum limitato a modello/lente/
seriale/parametri misurati.

## Ledger emendamenti

- (vuoto alla preregistrazione, 2026-07-31)
