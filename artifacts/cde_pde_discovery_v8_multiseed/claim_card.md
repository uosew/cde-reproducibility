# Claim card — CDE_V8_MULTISEED_CHARACTERIZATION

**Verdetto:** CONFERMATA
**Data:** 2026-08-05 · **Guard:** PASS · **Semi:** 20 (101–120), 20/20 riusciti

**Preregistrazione:** `PREREGISTRAZIONE_V8_MULTISEED_2026_08_04.md`
(`ad35f6cb1ec7d990…`), congelata e committata (`f4164664`) **prima** che
qualunque seme girasse.
**V8 non modificato:** `4a2181b8dbeda428…`

---

## L'esito sui criteri congelati

| | criterio | valore | soglia | |
|---|---|---|---|---|
| **S1** | recupero esatto a σ = 0 | **20/20** su tutti e 4 i sistemi | ≥ 19/20 | **CONFERMATA** |
| **S2** | recupero a σ = 10% | **20/20** su tutti e 4 | ≥ 15/20 | PASS |
| **S3** | FDR sui nulli | **0** su **800** run | ≤ 0,05 | PASS |

    allen_cahn  20/20      fisher_kpp  20/20
    burgers     20/20      kdv         20/20

La claim originale era «recupero esatto» su due semi. Su venti semi freschi regge
alla lettera, e regge **anche al 10% di rumore** — che la preregistrazione non
chiedeva a quel livello.

---

## Ciò che rende il numero credibile

**I semi 7 e 11 non sono stati contati.** Sono i due che hanno prodotto la claim
originale: includerli avrebbe significato stimare la frequenza di un evento sui
casi che l'hanno fatto dichiarare. Sono riportati a parte — entrambi con recupero
esatto su tutti e quattro i sistemi — e restano fuori da `S1`, `S2` e `S3`.

**I venti semi sono consecutivi**, `101`–`120`, dichiarati in preregistrazione. Un
elenco «casuale» generato al momento sarebbe stato indistinguibile da uno scelto
fra diversi.

**V8 non è stato toccato.** Lo script scrive su percorso fisso e avrebbe
sovrascritto gli artefatti sigillati del seme 7; l'orchestratore ne ha verificato
i tre hash prima di partire, li ha messi in salvo e riverificati alla fine —
**intatti**.

---

## Il risultato che non era nella preregistrazione

**Il gate epistemico non è robusto quanto il recupero.**

    allen_cahn a sigma = 10%     support_exact  20/20
                                 gate_pass      11/20

Su Allen–Cahn al 10% di rumore il gate **rifiuta una risposta corretta in 9 semi
su 20**. Gli altri tre sistemi passano 20/20.

I semi 7 e 11 passano entrambi, ed è per questo che la nota affermava «nessun
livello di rottura raggiunto, `σ* > 10%` ovunque». **Quella frase è una proprietà
di due realizzazioni, non del protocollo, ed è stata ritirata dalla nota.**

La direzione dell'errore è quella sicura: il gate si rifiuta di certificare una
risposta giusta, non certifica una risposta sbagliata. Ma un tasso di falsi
negativi del **45%** ad alto rumore su un sistema è un costo reale, ed era
invisibile a due semi.

Va detto con precisione: questo **non** era un criterio preregistrato. `S4` era
dichiarato descrittivo, «si riporta, non si giudica». Lo riporto e non lo
trasformo in un criterio a posteriori.

---

## Errore sui coefficienti — mediana su 20 semi

| sistema | σ = 0 | σ = 1% | σ = 5% | σ = 10% |
|---|---:|---:|---:|---:|
| allen_cahn | 9,5·10⁻⁵ | 9,5·10⁻⁴ | 5,9·10⁻³ | 1,7·10⁻² |
| fisher_kpp | 1,3·10⁻⁴ | 6,1·10⁻⁴ | 4,2·10⁻³ | 7,4·10⁻³ |
| burgers | 4,1·10⁻⁵ | 2,6·10⁻⁴ | 1,6·10⁻³ | 2,8·10⁻³ |
| kdv | 1,3·10⁻⁵ | 3,5·10⁻⁴ | 1,6·10⁻³ | 1,9·10⁻³ |

`kdv` è il sistema **più** accurato, non il meno.

---

## L'attesa a priori era sbagliata

Avevo registrato: «`CONFERMATA` su `allen_cahn` e `fisher_kpp`, **incertezza reale
su `burgers` e `kdv`**», ragionando che la derivata terza di KdV fosse la più
esposta al rumore e che KdV fosse il sistema mai usato per la messa a punto.

Entrambi escono `20/20`, e KdV ha l'errore sui coefficienti più basso di tutti. Il
sistema che ha mostrato una fragilità è `allen_cahn` — quello che davo per sicuro
— e non nel recupero ma nel gate.

Resta agli atti.

---

## Che cosa questo NON chiude

Dei cinque limiti che la nota dichiara di se stessa, questa campagna ne chiude
**uno solo, e parzialmente**:

- **chiuso per i quattro sistemi V8**: caratterizzazione statistica su 20 semi;
- **aperto per KS**: il costo per seme rende 20 realizzazioni impraticabili qui,
  quindi il caso caotico poggia ancora su due semi;
- **aperti e invariati**: dati sintetici, contenimento della libreria, preflight
  oracolare, osservazione liscio/caotico.

Nessuna claim su dati sperimentali. Il perimetro resta quello della claim card
originale: PDE 1D periodiche lisce, solver spettrale, rumore gaussiano di misura.

---

## Artefatti

| | |
|---|---|
| `cde_pde_discovery_v8_multiseed/caratterizzazione.json` | esito sui criteri |
| `cde_pde_discovery_v8_multiseed/riepilogo.json` | esecuzione, hash del seme 7 prima/dopo |
| `cde_pde_discovery_v8_multiseed/seed_101..120/` | i venti `results.json` |
| `arxiv_note/main.tex`, `main.pdf` | nota aggiornata, frase ritirata, 0 overfull |
