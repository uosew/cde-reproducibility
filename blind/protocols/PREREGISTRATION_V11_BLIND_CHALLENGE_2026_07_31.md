# Preregistrazione — CDE V11 Blind Thermal Challenge V0

Data: 2026-07-31. Stato: **PREREGISTRATO PRIMA DI QUALUNQUE RUN**.
Obiettivo: verificare che il CDE distingua modelli termici diversi SENZA
conoscere il generatore — in particolare che non riconduca dinamiche
diverse alla legge del calore standard.

## Separazione obbligatoria

- `CDE_V11_BLIND_GENERATOR_V0.py`: conosce i modelli; scrive
  `cde_v11_blind_out/cases/case_NNN.npz` (array: x_pipe, t, V0..V4 per
  le 5 IC), `public_meta.json` (SOLO: parametri camera campionati
  nell'envelope, hz, px — informazioni note nella realta') e
  `sealed/truth.json` (classe, supporto vero, coefficienti). L'envelope
  del generator registra lo sha256 della verita'; dataset+verita' vengono
  COMMITTATI PRIMA di ogni run del discoverer (sigillo = hash + ordine
  dei commit, verificato all'unblinding).
- `CDE_V11_BLIND_DISCOVERER_V0.py`: legge SOLO cases/ e public_meta;
  NON importa il generator ne' legge sealed/; pipeline = ingestion ->
  preflight non-oracle -> selezione v1.1 pooled IC0..3 -> holdout IC4 ->
  swap relativo 2x -> ladder v2; emette `verdicts.json`.
- `CDE_V11_BLIND_UNBLINDING_V0.py`: verifica hash e ordine commit,
  incrocia verdetti/verita', calcola metriche e gate. NESSUNA
  reinterpretazione post-unblinding.

## Classi cieche (coefficienti campionati dai range preregistrati)

| Classe | Dinamica (variabile v, forma divergenza) | Rappresentabile |
|---|---|---|
| A ×10 | v_t = alpha v_xx; alpha in [5e-5, 2e-4] | si: {v_xx} |
| B ×10 | A + perdita -beta v; beta in [0.005, 0.05] | si: {v, v_xx} |
| C ×10 | (alpha(1+gamma v) v_x)_x - beta v; gamma in [0.003, 0.008] | si: {v, v_xx, div_vv_x} |
| D ×10 | alpha(x) = alpha0 (1 + 0.25 sin(3pi x/L + phi)) | NO |
| E ×10 | B + sorgente residua S(x) e^(-t/15), ampiezza [0.3, 1] C/s | NO |
| F ×10 | bulk v_t = alpha v_xx, forte leakage SOLO ai bordi (Robin) | si (bulk): {v_xx} |
| G ×10 | composito: alpha2/alpha1 in [1.8, 2.5], interfaccia in [0.15, 0.25] m | NO |
| H ×10 | nulli: shuffle temporale (pari) / surrogato di fase (dispari) di un campo A | NULL |
| I ×10 | B + avvezione tempo-variante w(t) v_x, w0 in [0.002, 0.005] m/s | NO |

90 casi × 5 IC = 450 traiettorie. Seed preregistrati: caso k -> seed
5000+k. Degradazioni strumentali campionate DENTRO l'envelope di
procurement (px {160,240,320}, hz {2,5,8.7}, NETD [0.05,0.25], quant
{0.1,0.5}, PSF [0,4], jitter [0,100] ms, deriva [0,0.5], dead [0,2%],
nonunif [0,1.5%], moto [0,0.25 px], scala [0,0.5%]); alcuni casi cadono
per costruzione vicino ai limiti.

## Scoring (dichiarato ORA)

- Esiti accettabili per classe: A/B/C/F -> CLAIM col supporto vero
  (CLAIM_EXACT); D/E/G/I -> qualunque esito NON-CLAIM (ABSTAIN_GATE,
  NOT_IDENTIFIABLE, REJECTED_TRANSFER, ABSTAIN_EMPTY) = misspecification
  rilevata; H -> non-CLAIM = nullo respinto.
- **Falsa claim = verdetto CLAIM su classe non rappresentabile o nullo,
  oppure CLAIM con supporto diverso dal vero.** Metrica regina:
  P(CLAIM errata).
- REJECTED_PREFLIGHT conta come rifiuto dati (riportato a parte, non
  come detection).

## Gate di successo (congelati)

G1 zero false claim esatte; G2 support recovery >= 95% su A/B/C/F;
G3 misspecification detection >= 90% su D/E/G/I; G4 zero FD sui nulli H;
G5 errore mediano coefficienti < 5% sulle claim vere; G6 holdout pass
su >= 90% delle claim vere; G7 nessuna reinterpretazione post-unblinding
(esiti difformi riportati integralmente; revisioni = challenge V1 con
nuova preregistrazione).

## Ledger emendamenti

- (vuoto alla preregistrazione, 2026-07-31)
