# Preregistrazione — la ricerca sui primi guadagna passando da coppie a k=3?

**Data:** 2026-08-25
**Commit di apertura:** `514390b6`
**Origine:** risultato collaterale dello Stadio A QUBO
(`reports/QUBO_FEASIBILITY_STAGE_A_2026-08-25.md`), **con la sua correzione**

**Stato:** questione APERTA, non ancora congelata per l'esecuzione. Mancano i
tre atti elencati in §7.

---

## 1. Da dove nasce, e da quale errore

Lo Stadio A ha misurato che l'esaustivo fino a `k = 3` da' residuo `0,15507`
contro `0,16680` delle sole coppie — il **7%** che il report annunciava come
guadagno.

**Quel numero non significava quello che sembrava.** L'insieme dei sottoinsiemi
con `k ≤ 3` **contiene** quello con `k ≤ 2`: il minimo non puo' essere
peggiore, e la misura era in-sample. Il guadagno era garantito per costruzione,
cioe' una tautologia.

Rimisurato fuori campione:

| | train | test |
|---|---|---|
| `k ≤ 2` | 0,166797 | 0,196340 |
| `k ≤ 3` | 0,155075 | **0,192153** |
| guadagno | +7,03% (garantito) | **+2,13% (reale)** |

Il segnale fuori campione esiste. Ma viene da **una sola misura**: uno scope,
uno split, nessun seme, nessun controllo nullo. Questa preregistrazione esiste
perche' `+2,13%` da una misura sola non e' un risultato.

---

## 2. La domanda, falsificabile

> Sulla **metrica di selezione dell'arena** — mediana sui semi di
> `spearman + 0.5·(pairwise−0.5) + 0.15·max(r2,0) − 0.01·complexity`, calcolata
> sul **test** — un supporto a tre termini batte il migliore a due, su piu'
> scope e piu' semi?

Ha un esito che la smentisce, e non e' improbabile: **la metrica penalizza la
complessita'**. Un terzo termine paga `−0.01` e deve guadagnare piu' di cosi'
in accuratezza fuori campione. Il `+2,13%` misurato sul residuo **non** si
traduce automaticamente in un punteggio migliore.

---

## 3. Perche' l'arena non va modificata

`scripts/prime_symbolic_residual_arena_v06.py`
(sha256 `872294b4ad3a20b8d015239b2273849959ff44ae9ba2f28fdd3be37bff60e4e9`)
e' importato da **13 campagne CDE committate**, i cui claim card e hash sono
nel ledger. Cambiarne la cardinalita' di ricerca altererebbe retroattivamente
il codice di risultati gia' registrati.

La campagna dovra' quindi usare un **modulo nuovo**, con l'arena importata in
sola lettura — la stessa regola applicata a `CDE_PDE_DISCOVERY_V8.py` quando
sono stati integrati i cancelli.

---

## 4. Il confronto e' appaiato, e il baseline non si riscrive

Ogni scope viene valutato due volte **sulle stesse feature e sugli stessi
semi**: una con la ricerca attuale (`k ≤ 2`), una con `k ≤ 3`. Le feature si
calcolano una volta sola e si condividono, cosi' l'appaiamento e' esatto e non
c'e' rumore di semi fra i bracci.

Il braccio di controllo **importa** la funzione di ricerca esistente invece di
riscriverla.

---

## 5. Cosa va misurato prima di congelare (osservabilita')

Non si fissano soglie prima di sapere se l'effetto e' rilevabile. Da misurare
su un pannello di prova **fuori** da quello confermativo:

1. **la varianza del punteggio fra semi** — se la dispersione seme-a-seme e'
   dello stesso ordine del `+2,13%`, il disegno non puo' distinguere l'effetto
   e la campagna non va eseguita;
2. **quanti scope sono disponibili** — `PATTERNS` ne definisce un numero
   finito, e piu' semi sullo stesso scope non sono unita' indipendenti: sarebbe
   la pseudo-replicazione che H003 esisteva per evitare;
3. **il costo**: l'esaustivo a `k = 3` su 62 termini e' 1,58 s per scope-seme,
   quindi il pannello e' economico. Non e' il tempo il vincolo, e' il numero di
   unita' indipendenti.

---

## 6. Cosa questa campagna NON potra' dimostrare

- **Non dira' nulla su Hardy-Littlewood, primi gemelli, k-tuple o Riemann.**
  Valgono integralmente le *forbidden claims* di
  `cde_prime_residual_revalidation_v2_out/claim_card.md`.
- **Non stabilira' che k=3 sia la cardinalita' giusta.** Confronta 3 contro 2;
  `k = 4` sarebbe un'altra domanda con un'altra penalita' di complessita'.
- **Non risolvera' l'indeterminatezza della selezione.** Il margine fra primo e
  secondo candidato e' `0,000000` con pareggi esatti
  (`reports/prime_residual_conditioning_probe.json`): con k=3 lo spazio dei
  candidati cresce e i pareggi possono aumentare, non diminuire. **Questa
  campagna non e' il rimedio a quel problema** e non va citata come tale.
- **Non e' un miglioramento del segnale.** Il segnale e' quello di
  `REVALIDATION_V2`; qui si chiede solo se una ricerca piu' larga lo esprima
  meglio.

---

## 7. Cosa manca per congelare

1. la misura di osservabilita' del §5, con esito dichiarato;
2. il modulo di campagna nuovo, con l'arena importata in sola lettura;
3. le soglie di promozione, scritte **dopo** la §5 e **prima** della run.

Finche' i tre atti non sono compiuti, questa e' una questione aperta e non una
campagna. Il `+2,13%` resta un'osservazione singola, non un risultato.
