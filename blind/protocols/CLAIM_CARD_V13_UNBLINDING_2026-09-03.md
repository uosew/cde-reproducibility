# Claim card — replica cieca V13 su larga scala, sbendamento

**Prereg:** `PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md` (semi registrati prima
della generazione; casi generati 2026-08-02, verdetti prodotti 2026-08-02/04 su Mac arm64 e
Windows AMD64; **mai valutati fino a oggi**). **Scorer:** `CDE_V13_BLIND_UNBLINDING_V0.py`,
regole identiche a `CDE_V11_BLIND_UNBLINDING_V1.py`, 8 mutation test tutti mordenti prima
del verdetto. **Artefatto:** `cde_v13_blind_out/unblinding_report.json`.

## Verdetto: **CLAIM_FALSA_OSSERVATA** (§6)

| | |
|---|---|
| casi | 603 (9 classi × 67): 268 rappresentabili, 268 non rappresentabili, 67 nulli |
| opportunità di mentire | **423** (67 + 268 + 88 rappresentabili con supporto errato) — soglia 350 superata |
| **claim false** | **14** — tasso 14/423 = **3,3 %** (limite «regola del tre» che si sperava: 0,71 %) |
| claim corrette | 105 / 268 rappresentabili (recall 39,2 %), errore coefficiente mediano 1,17 % |
| claim su nulli | 0 / 67 |
| claim su non rappresentabili | 0 / 268 |
| Domanda B, 100 casi condivisi Mac/Windows | **accordo pieno 100/100** (verdetto, supporto, `blocked_at`) |

La preregistrazione scriveva: «CLAIM_FALSA_OSSERVATA non è un fallimento della campagna, è il
suo scopo». Lo è. **La caratterizzazione «forte verificatore difensivo, zero claim false» va
riscritta**, come la prereg imponeva.

## La classe di fallimento, una sola e precisa

Tutte e 14 le false sono in **classe C**: diffusione non lineare `D = α(1 + γ v)` con reazione
`−β v`. Supporto vero `{v_xx, v, div_vv_x}`; affermato `{v_xx, v}`.

- Il termine mancante `div_vv_x` ha coefficiente **α·γ ≈ 5·10⁻⁷ contro α ≈ 10⁻⁴**: pesa circa lo
  **0,5 %** della dinamica. L'unica C corretta lo stima 6,3·10⁻⁷.
- Le false hanno β mediano **0,043** (le più «reattive»); le 48 `NOT_IDENTIFIABLE` β 0,024; i 4
  `MISSPECIFIED` β 0,006. Quando la reazione domina, il modello a due termini spiega i dati con
  residuo 0,011 ≪ 0,05 e la scala afferma.
- Il test di scambio (2× relativo) **non può** distinguere con/senza un termine allo 0,5 %:
  in 48 casi su 67 lo dichiara, correttamente, `NOT_IDENTIFIABLE`; in 14 non lo vede affatto.

**Definizione:** *claim di sotto-supporto* — un modello effettivo esatto a meno di un termine
sotto la risoluzione dei cancelli, affermato come legge. È la stessa famiglia del `sin(u)` del
blind 1 (troncamento di Taylor), vista dall'altro lato: lì un termine fuori libreria
mascherato da due dentro; qui un termine dentro libreria troppo piccolo per essere visto.

## Cosa cambia nelle affermazioni

1. **Nota arXiv:** le frasi «zero false discoveries» si riferiscono ai **120 nulli** della
   discovery PDE V8 e restano vere. La nota **non** contiene la replica termica V13; deve
   contenere questa frase: *nel blind termico su larga scala (603 casi, 423 opportunità) il
   sistema ha prodotto 14 claim false, tutte claim di sotto-supporto su termini che pesano
   sotto l'1 % della dinamica; zero su nulli e non rappresentabili.* Senza, la nota
   sottintende una proprietà che questa campagna ha falsificato.
2. **Semantica dei verdetti (2026-08-24):** con la ladder attuale questi 14 sarebbero
   `CLAIM_EFFETTIVO` (regime unico) — verdetto **assertivo** e quindi ancora falso positivo per
   la regola anti-riciclaggio. Il cancello di ampiezza non aiuta: i dati termici non hanno un
   secondo regime.
3. **La correzione che questa classe chiede** (da preregistrare, non da fare qui): ogni CLAIM
   porta un **limite di risoluzione dichiarato** — «legge valida per termini che contribuiscono
   oltre l'X % della dinamica», con X stimato dai dati (rapporto fra residuo e norma di b).
   Trasforma il sotto-supporto da menzogna a claim con ambito, senza spostare soglie.

## Integrità, dichiarata
Sigillo **procedurale**, non crittografico: l'envelope V13 non registra lo sha della verità
(V11 lo faceva) e verità e verdetti stanno nello stesso commit `23c254ba`. Evidenza di
cecità: il discoverer non contiene letture di `sealed/` (verificato dal codice), la
generazione (17:03Z) precede l'esecuzione (22:19Z), `truth.json` identico a HEAD. È
un'evidenza più debole di V11 e va detto. **E8 per l'audit:** 703 verdetti ciechi sono
rimasti non valutati per 30 giorni; un blind non sbendato non è evidenza in nessuna direzione.

## Cosa NON dimostra
Nulla sulla ladder attuale (V13 usa la v2.1 di luglio, prima dei cancelli del 24 agosto):
la classe di fallimento è plausibilmente ancora aperta, ma va misurata sulla V1. Nulla sulla
recall come metrica (39 %): la campagna misurava solo claim false.
