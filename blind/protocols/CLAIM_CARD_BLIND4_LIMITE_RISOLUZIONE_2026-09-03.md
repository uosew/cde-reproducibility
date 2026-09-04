# Claim card — Blind-4: limite di risoluzione dichiarato per ogni CLAIM

**Prereg:** `PREREGISTRAZIONE_LIMITE_RISOLUZIONE_CLAIM_2026-09-03.md`, sha256 `95cef22f538f…`,
commit `84ccb4b3`, prima di ogni run. **Stage 1** (diagnostico, verità aperta, V13): k=1 viola
2/14, k=2 sound 44/44 → **k\* = 2** (`0e3aaf3e`). **Pannello:** 120 casi rappresentabili (A, B, C,
F × 30), semi 720000/730000, verità sigillata con sha `e92ebf05…` e **committata prima del
discoverer** in commit separato (`e264506a`). **Discoverer:** V13 invariato (ladder v2.1),
cieco (nessun riferimento a `sealed/` nel sorgente, verificato dallo scorer). **Predizioni**
hashate (`38cfaf7a…`) prima dell'apertura della verità. Scorer con 5 mutation test mordenti.

## Verdetto: **CONFIRMED** (§4)

| | |
|---|---|
| CLAIM | **59** (≥ 30 richiesti) — 51 corrette, 8 false strette |
| false strette | tutte **classe C**, tutte sotto-supporto `{v, v_xx}` per `{v, v_xx, div_vv_x}`: la stessa classe della V13 |
| **violazioni di H1** (termine mancante con contributo ≥ X) | **0 / 8** — copertura 8/8 |
| verdetti cambiati dall'annotazione (H3) | **0** |
| X mediana sulle claim | 3,0 % (corrette 3,8 %, q90 7,8 %, max 9,5 %; false 2,0 %) |
| margine X / contributo mancante sulle 8 false | 1,68× … 4,40× (mediana 2,7×) |
| coefficiente minimo rilevabile `c_min(div_vv_x)` sulle false | 1,4·10⁻⁶ contro α·γ vero 4,7·10⁻⁷: il limite **dice** che quel termine non era risolvibile |
| errore coefficiente mediano (v_xx) sulle corrette | 1,25 % |
| tasso di violazione, regola del tre | ≤ 3/59 = **5,1 %** |

## Cosa afferma, esattamente
Con k = 2, la dichiarazione «legge S a meno di termini della libreria con contributo relativo
inferiore a X» è risultata **vera su tutte le 59 claim** di un pannello sigillato, comprese le
8 in cui il sistema aveva perso un termine vero. Il fallimento della V13 non sparisce: quelle
8 claim restano **false strette** per la definizione a supporto esatto (riportata invariata).
Cambia ciò che il sistema *dice*: non «questa è la legge», ma «questa è la legge fino a X», e
X era, ogni volta, sopra il termine che mancava. Una menzogna diventa una claim con ambito.

## Cosa NON dimostra (prereg §5, più quanto emerso)
- Nulla sui termini **fuori libreria**: `f_t` esiste solo per termini della libreria. Il
  surrogato di Taylor resta materia del cancello di ampiezza e di `CLAIM_EFFETTIVO`.
- Il margine minimo osservato è **1,68×** (case_083): con k=2 il limite tiene, ma non per
  molto; un termine mancante più forte di così lo violerebbe. Un CONFIRMED su 59 claim limita
  il tasso di violazione al 5 %, non lo azzera: **prima replica, non VALIDATED**.
- La recall resta bassa (51/120): X qualifica le claim, non ne aggiunge. Classe C: 9 CLAIM e
  21 NOT_IDENTIFIABLE su 30 — il termine αγ è al confine della risolvibilità per costruzione.
- Nulla sulla pipeline PDE V1: definizione portabile, misura da rifare lì.
- Tempo: 5.277 s contro i ~7.500 stimati; stima prudente, dentro il tetto.

## Stato dell'ipotesi
H1 (soundness con k=2): **CONFIRMED** su pannello sigillato; nel registry corrisponde a
`SUPPORTED`, non a `VALIDATED`: serve una replica (≥ 150 claim per un limite sotto il 2 %) e,
prima ancora, la decisione se adottare l'annotazione nella semantica dei verdetti.
