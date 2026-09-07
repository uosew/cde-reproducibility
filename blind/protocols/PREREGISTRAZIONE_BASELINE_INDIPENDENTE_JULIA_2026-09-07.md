# Preregistrazione — seconda implementazione indipendente sulle stesse feature deboli

**Data:** 2026-09-07, prima di installare Julia e prima di ogni run.
**Domanda:** l'affermazione su campi nulli è una proprietà di **una libreria** (PySINDy) o della
**classe di metodi** (selezione sparsa a soglia senza criterio di evidenza)?

## 0. Perché questa campagna esiste
La nota afferma che PySINDy (WeakPDELibrary + STLSQ con soglia scelta da oracolo) rivendica un
modello su 49 campi nulli su 50, e che un cancello sul residuo porta il conto a 0/50. Un revisore
chiederà se il 49/50 dipende dall'implementazione. `DataDrivenDiffEq.jl` (SciML, MIT, attivo) è
una **implementazione indipendente, di un altro gruppo, in un altro linguaggio**. Il confronto
qui è **appaiato sull'ottimizzatore**: stessa matrice di disegno, diversa regola di selezione.

## 1. Disegno, congelato

- **Feature:** le matrici `A` (7 termini weak) e la colonna `b` sono quelle del motore congelato
  `CDE_PDE_DISCOVERY_V8.py`, rigenerate con seme 7 e i semi dei nulli già dichiarati
  (`1000 + 97·ns + 0|7`), esportate in `.npz` con sha256 nel manifesto **prima** di installare Julia.
- **Sistemi:** i 4 della V8 (Allen–Cahn, Fisher–KPP, Burgers, KdV). **KS è escluso**: il suo
  motore è la V9 con una griglia diversa, e mescolarlo renderebbe il confronto non appaiato.
  Riferimento PySINDy sugli stessi 4 sistemi, dagli artefatti: **40/40 nulli rivendicati**,
  **14/20 celle a supporto esatto**.
- **Celle:** 20 celle vere (4 sistemi × 5 livelli di rumore) e **40 nulli** (4 × 5 semi × 2 tipi:
  permutazione temporale e surrogato di fase).
- **Bracci sulle stesse `A`, `b`:**
  1. `LB` — selezione del motore congelato (stability selection B=100, BIC con il supporto vuoto
     fra i candidati, frequenza ≥ 0,8) + cancello sul residuo 0,05;
  2. `DDE` — `DataDrivenDiffEq.jl` con `STLSQ` su una griglia di soglie, **scelta da oracolo**
     per cella come fu concesso a PySINDy (vantaggio pro-baseline, dichiarato);
  3. `DDE+gate` — lo stesso, con il nostro cancello sul residuo applicato a valle.
- **Rivendicazione su un nullo** = supporto selezionato non vuoto. **Supporto esatto** su una
  cella vera = insieme dei termini identico a quello noto.

## 2. Esiti dichiarati in anticipo

| esito | condizione | significato |
|---|---|---|
| **CLASSE** | `DDE` rivendica su ≥ 30 dei 40 nulli | il fallimento è della classe di metodi, non di PySINDy: il cancello serve a tutti, e la frase della nota si rafforza |
| **IMPLEMENTAZIONE** | `DDE` rivendica su ≤ 10 dei 40 | l'implementazione conta più di quanto la nota lasci intendere; **la nota va corretta** dichiarando che il 49/50 è di PySINDy e non della classe |
| **INTERMEDIO** | fra 11 e 29 | nessuna delle due frasi è sostenibile; si riporta il conteggio e basta |
| **NON_CONFRONTABILE** | l'API non permette di imporre la stessa matrice di disegno, oppure fallisce su ≥ 5 celle | si dichiara e si chiude senza numeri |

Atteso a priori: **CLASSE**. È la previsione che rende la campagna un test: se esce
IMPLEMENTAZIONE, indebolisce una nostra affermazione già pubblicata, e va scritto.

Secondo esito, riportato sempre: `DDE+gate` sui 40 nulli. Se il cancello porta anche questa
implementazione a 0, la trasferibilità del cancello è mostrata due volte.

### Emendamento §1-a, dichiarato prima di ogni risultato (2026-09-07)

Scrivendo lo scorer mi sono accorto di un'asimmetria che avrebbe reso il confronto non
appaiato: sceglievo per i nulli di `DDE` la soglia **più favorevole** (quella che si astiene se
esiste), mentre i nulli di PySINDy furono contati con la **soglia fissa** selezionata sulla
cella a rumore zero. Il verdetto usa quindi la **politica fissa**, identica a quella di
PySINDy; la politica oracolo viene riportata accanto, perché una rivendicazione anche sotto la
regola più generosa è la forma forte del risultato. Nessun'altra soglia o criterio cambia, e
nessun risultato è stato letto: l'export delle feature era ancora in corso.

## 3. Cosa NON dimostra
Non confronta le pipeline: le derivate deboli sono le nostre in tutti i bracci, quindi non dice
nulla sulla qualità dell'operatore di `DataDrivenDiffEq`. Non è cieco: la verità dei nulli è nota
per costruzione (nessuna dinamica). Non tocca KS. Non misura tempi.

## 4. Ledger
| data | voce |
|---|---|
| 2026-09-07 | creata prima dell'installazione di Julia e dell'export delle feature. |
| 2026-09-07 | **Eseguita.** Export 60 matrici (670 s), Julia 1.12.7 + DataDrivenSparse, 60 celle. Esito: **CLASSE** — 40/40 nulli rivendicati con la politica appaiata (10/40 con la politica oracolo), **0/40 col cancello**, 20/20 celle vere a supporto esatto, 0 errori. Claim card `CLAIM_CARD_BASELINE_INDIPENDENTE_JULIA_2026-09-07.md`. |
