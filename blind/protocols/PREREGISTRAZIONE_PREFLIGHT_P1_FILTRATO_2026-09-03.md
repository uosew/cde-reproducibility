# Preregistrazione — P1 del preflight su campo filtrato

**Data:** 2026-09-03, prima di qualunque run.
**Baseline:** V1 (tag `cde-v1-baseline-2026-09-02`) con il preflight di
`CDE_BLIND_PDE_RUNNER_V0.py` (P1/P2/P3, gate 0,05 ciascuno).
**Protocollo vincolante:** `FAST_EXPERIMENT_PROTOCOL_V1.md`.

## 0. Cosa il dato ha già detto (diagnostico, non confermativo)

Dallo screening del gate di ampiezza (semi 9001-9008) e dalla produzione V1:

1. **P3 ≈ residuo di fit sparso**: rapporto P3/fit fra 0,80 e 1,22 su 40 celle. Il
   sospetto «il preflight denso è più severo della discovery sparsa» è **falsificato**:
   P2 e P3 misurano il pavimento di rumore del fit e chiudono dove il fit chiuderebbe.
2. **P1 chiude un fit eccellente**: quadratica σ=15 %: P1 = 0,063, P3 = 0,004. P1 cresce
   linearmente col rumore (0,020 → 0,044 → 0,063 a 5/10/15 %).
3. **P1 rileva davvero la sotto-risoluzione**: a Nx=192 (pulito) vale 0,91 (quadratica) e
   0,44 (Burgers) contro 0,05: margine 9-18×. Non va tolto, va **de-confuso**.
4. Verifica di osservabilità (un solo caso, quadratica 9002, σ=15 %): P1 grezzo 0,057,
   P1 su campo filtrato (|k| < Nx/8) 0,037; a Nx=192 il filtrato resta 0,9078.

**Il caso quadratica 9002 è diagnostico: non entra nel pannello.**

## 1. Ipotesi

H1: P1 (differenza Simpson-trapezio delle colonne deboli) confonde il rumore di misura
con l'errore di quadratura. Calcolato sulla parte passa-basso del campo, mantiene la
sensibilità alla sotto-risoluzione e perde quella al rumore, riducendo le chiusure
di preflight su leggi vere che la discovery recupererebbe.

**Atteso a priori:** `PROMISING` per il taglio 1/8; il taglio 1/4 sospettato di non
ridurre abbastanza il rumore.

## 2. Candidati — nessuna soglia nuova

Il gate resta 0,05. Cambia solo il campo su cui P1 è calcolato.

| | regola | numero e origine |
|---|---|---|
| **P1-LP8** | `rel_col_diff` su `U_lp`, filtro passa-basso spaziale `|k| < Nx/8` | 1/8 già congelato in `CDE_GATE_AMPIEZZA_CANDIDATI_V0.py` (stimatore di rumore) |
| **P1-LP4** | idem con `|k| < Nx/4` | il doppio del precedente: un secondo punto, non una taratura |

P2, P3, e tutto il resto della pipeline: **identici** per costruzione.

## 3. Pannello — disgiunto da tutto (semi 9101-9108, mai usati)

| ruolo | celle | scopo |
|---|---|---|
| leggi vere, 5 famiglie, σ ∈ {10 %, 15 %}, Nx=768 | 10 | contrasto primario |
| **controllo di risoluzione**: le stesse 5 leggi, Nx=192, σ=0 | 5 | il candidato DEVE chiudere |
| decoy, 3 famiglie, σ=15 % | 3 | il candidato non deve aprire ciò che poi afferma |

Per ogni cella il runner registra P1 grezzo, P1-LP8, P1-LP4, P2, P3 **e la decisione V1
eseguita a prescindere da P1** (P2/P3 restano applicati): è il controfattuale che dice
cosa la discovery avrebbe fatto. Rumore su tutte e tre le traiettorie, come in produzione.

**Compute envelope:** ~50 s per cella a 768, ~10 s a 192 → **~10 min**. Tetto 15, stop a 22.

## 4. Metriche — congelate

- **Primaria:** `Δ_FN = FN_P1 − FN_cand` sulle 10 celle vere, con FN = P1 (o candidato)
  ≥ 0,05 **e** decisione controfattuale = CLAIM corretto (supporto esatto, errore < 5 %).
- **Guardia A (risoluzione):** il candidato deve chiudere **5/5** celle a Nx=192.
  Una sola apertura → `NOT_PROMISING`.
- **Guardia B (decoy):** nessuna cella decoy in cui il candidato apre e la decisione
  controfattuale è assertiva. Una sola → `NOT_PROMISING`.
- **Guardia C (regressione):** nessuna cella vera aperta da P1 e chiusa dal candidato.
- **Guardia D (asserzione):** P2, P3 e la decisione controfattuale identiche fra bracci.

## 5. Esiti (§3) e potere (§4)

Dallo screening precedente P1 ha chiuso 1/5 leggi vere a 15 % e 0/5 a 10 % (una a 0,044).
**FN_P1 attesi ≈ 1-2 su 10.** Direzionale: distingue «aiuta senza danno» da «danneggia».

| esito | condizione |
|---|---|
| `PROMISING` | Δ_FN ≥ 1 e guardie A-D rispettate |
| `NOT_PROMISING` | una guardia violata, oppure Δ_FN ≤ 0 |
| `UNCLEAR` | FN_P1 = 0: un solo raddoppio, σ=20 % sulle stesse 5 leggi (dichiarato qui) |

## 6. Scelta e seguito
Fra i `PROMISING`: il maggiore Δ_FN; a parità **P1-LP8** (numero già congelato). Un solo
candidato al blind-3, con i criteri di successo dell'utente già congelati nella prereg
del 2026-09-02 §7 (più CLAIM veri, 0 falsi, supporto invariato, nessuna regressione a
rumore basso, nulli invariati) **più** la guardia A ripetuta su un controllo di
risoluzione nuovo.

## 7. Cosa NON dimostra
Nulla su P2/P3 (già mostrati ≈ fit: non sono il collo di bottiglia, e questo è un
risultato di questa linea, negativo e dichiarato). Nulla oltre il 15 % salvo raddoppio.
Nulla su rumore correlato o non gaussiano. Un taglio spettrale fisso non è ottimo per
ogni famiglia: Burgers ha contenuto ad alto k che è segnale.

## 8. Ledger
| data | voce |
|---|---|
| 2026-09-03 | creata; osservabilità verificata su un caso diagnostico; nessun run. |
| 2026-09-03 | Stage 1 eseguito: 18 celle, 889 s (stima 600 sbagliata del +48 %, sotto l'arresto). **PROMISING** per P1-LP8 e P1-LP4 (Δ_FN +1, 5/5 coarse chiuse, 0 decoy, 0 regressioni); scelto **P1-LP8**. Claim card `CLAIM_CARD_PREFLIGHT_P1_STAGE1_2026-09-03.md`. Prossimo: prereg del blind-3. |
| 2026-09-03 | blind-3 eseguito: **INCONCLUSIVE**. P1-LP8 non entra in produzione. La previsione «effetto quadratico» era sbagliata: la quadratica cade sul test di scambio. |
| 2026-09-03 | **Decisione dell'utente:** claim boundary sul rumore fissata al 10 %; filone > 10 % chiuso per ora (`DECISIONE_CLAIM_BOUNDARY_RUMORE_10_2026-09-03.md`). |
