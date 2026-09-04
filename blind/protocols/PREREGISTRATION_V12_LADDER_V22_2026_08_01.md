# Preregistrazione — Ladder v2.2: recall delle claim vere a rischio invariato

Data: 2026-08-01. Stato: **PREREGISTRATO PRIMA DI QUALUNQUE MODIFICA ALLA
LADDER E PRIMA DELLA GENERAZIONE DELLA NUOVA CAMPAGNA CIECA.**

La ladder v2.1 resta congelata e non viene toccata: la v2.2 è una nuova
versione che dovrà battere la v2.1 sullo stesso metro, non una correzione
retroattiva della v2.1.

---

## 1. Obiettivo, congelato ora

**Primario.** Aumentare il recall delle claim vere sui casi rappresentabili.

**Vincolo, non negoziabile.** Nessuna claim falsa **osservata**. Il vincolo
domina: una v2.2 che raggiunge il target del recall producendo anche una sola
claim falsa è **respinta**, non discussa.

Formulazione corretta del vincolo, perché «tasso pari a zero» non è una
grandezza misurabile su un campione finito: *nessuna claim falsa osservata su
almeno 150 casi ciechi da rifiutare, con limite superiore approssimativo del
tasso reale pari al 2% (95%, regola del tre)*.

| grandezza | v2.1 (misurato) | soglia v2.2 |
|---|---|---|
| claim corrette su rappresentabili | 16/40 (40,0%) | **≥ 60,0%** |
| claim false osservate | 0 su 50 (limite 6%) | **0 su ≥150 (limite 2%)** |
| verdetti corretti sui casi da rifiutare | 50/50 (100%) | **≥ 98%** |

La terza riga è un'aggiunta necessaria: senza di essa la v2.2 potrebbe
raggiungere il target trasformando rifiuti corretti in astensioni generiche
senza produrre claim false, migliorando il numero primario senza migliorare
il sistema.

---

## 2. Perché 60% è un bersaglio onesto (analisi di raggiungibilità)

Fatta **prima** di congelare la soglia, sui 24 rifiuti prudenti della v2.1.
Non sono omogenei:

| gruppo | casi | recuperabile? |
|---|---|---|
| supporto **già esatto**, bloccato da un gate | **14** | sì |
| supporto **sbagliato** (termini spuri: `v2`, `vv_x`, `div_vv_x`) | 10 | **no** |

Il tetto massimo raggiungibile senza mai mentire è quindi **30/40 (75%)**, non
40/40: i 10 casi con supporto sbagliato sono rifiutati **correttamente**, e
rilassare i gate per recuperarli produrrebbe claim false per costruzione.

Il target di 24/40 richiede di recuperare **8 dei 14** recuperabili, cioè il
57% del pool disponibile. Non è né automatico né impossibile.

Dove sono bloccati i 14 recuperabili:

- **identifiability_gate: 8 casi di classe C**, con supporto identico al vero
  e residui di holdout fra 0,012 e 0,026, molto sotto la soglia del 5%. È il
  bersaglio più promettente e più concentrato.
- **numerical_preflight: 3 casi di classe A**, con supporto giusto ma holdout
  fra 0,058 e 0,074, cioè genuinamente marginali rispetto al gate.
- **transfer_gate, fit_gate, preflight: 3 casi di classe F.**

---

## 3. Contaminazione dichiarata, e cosa ne consegue

I 90 casi della campagna V11 **sono stati aperti**. Non solo il report di
unblinding: il 2026-08-01 è stata ispezionata caso per caso la verità dei 24
rifiuti, distinguendo quali avessero il supporto giusto e quali no. Quella
conoscenza è ora incorporata nell'analisi del §2.

**Conseguenza vincolante:** i 90 casi V11 diventano da questo momento e per
sempre un **development set**. Non possono più fondare una claim. Sviluppare
la v2.2 su di essi e poi dichiarare il risultato equivarrebbe a tarare sul
test — esattamente l'errore che questo programma esiste per impedire.

La richiesta ammetteva «stessa campagna o nuova campagna cieca comparabile».
La prima opzione **non è ammissibile** ed è esclusa qui. Lo si scrive prima di
conoscere l'esito, non dopo.

**Disegno in due tempi, congelato:**

1. **Sviluppo** sui 90 casi V11 (development). Tutti i tentativi, le varianti
   e le calibrazioni avvengono qui. I numeri di questa fase sono diagnostici e
   **non sono riportabili come risultato**.
2. **Validazione** su una **nuova campagna cieca V12**, generata dopo il
   congelamento della v2.2, con verità sigillata mai aperta prima
   dell'emissione di tutti i verdetti. Solo questi numeri contano.

---

## 4. Dimensione della nuova campagna e potenza statistica

Lo «zero claim false» della v2.1 è misurato su 50 casi da rifiutare. Per la
regola del tre, zero eventi su 50 prove è compatibile con un tasso vero fino
al **6%** al 95% di confidenza. È un limite debole, e va detto.

La campagna V12 avrà quindi:

- **≥ 150 casi da rifiutare**, che portano il limite superiore al 2%;
- **≥ 80 casi rappresentabili**, per stimare il recall con un errore standard
  sotto i 6 punti percentuali;
- **stessa distribuzione di classi e stessi assi di degradazione** della V11,
  con le soglie della camera virtuale invariate, così che i due risultati
  siano confrontabili;
- generatore che **non importa** il discoverer e viceversa, come in V11.

Il target sul recall è espresso in proporzione (**≥ 60%**), non in valore
assoluto, perché il denominatore cambia.

---

## 5. Cosa la v2.2 può cambiare, e cosa no

**Ammesso:**

- introdurre il verdetto `INSUFFICIENT_EXCITATION` come categoria distinta da
  `MISSPECIFIED`, con discriminatore dichiarato in anticipo: coerenza dei
  coefficienti fra traiettorie nonostante residuo alto;
- rivedere la soglia dell'`identifiability_gate` (swap relativo 2×), che
  blocca 8 dei 14 recuperabili;
- rivedere la costruzione del `numerical_preflight`, purché resti non-oracle;
- aggiungere gate, se rendono il sistema più selettivo.

**Vietato:**

- rimuovere o indebolire il gate di trasferimento su holdout;
- rendere la classificazione dipendente da informazioni non disponibili al
  discoverer al momento del giudizio;
- qualunque regola che usi il numero del caso, l'ordine di generazione o
  metadati non fisici;
- modificare la definizione di claim falsa, di supporto corretto o di caso
  rappresentabile. Queste tre definizioni sono **congelate** e identiche alla
  V11.

---

## 6. Anti-overfitting sul development set

- **Al massimo 6 varianti candidate** della ladder possono essere valutate sui
  90 casi di sviluppo. Ogni variante va registrata nel ledger **prima** di
  essere eseguita, con: formula esatta, parametri, casi ammessi, criteri di
  successo, criteri di rigetto, hash del codice, ordine di esecuzione.
- Superate le 6, il development set è considerato esaurito e serve una nuova
  campagna di sviluppo.
- Le varianti devono essere **modifiche mirate**, non rilassamenti generali.
- Una sola candidata finale viene promossa alla validazione cieca.

### 6.1 Le sei varianti ammesse

| # | variante | bersaglio |
|---|---|---|
| 1 | gate di identificabilità condizionato al supporto | gli 8 casi C |
| 2 | soglia adattiva basata sul margine residuo | i 3 casi A marginali |
| 3 | identificabilità locale sul supporto selezionato | gli 8 casi C |
| 4 | distinzione fra non-identificabilità e insufficiente eccitazione | tassonomia |
| 5 | consenso multi-seed del gate | stabilità |
| 6 | combinazione delle due regole migliori, preregistrata prima dell'esecuzione | — |

La variante 6 può essere definita solo **dopo** aver visto le prime cinque sul
development, e va registrata nel ledger prima di essere eseguita.

### 6.2 Regola di selezione, lessicografica

La candidata finale **non** si sceglie sul solo recall. Ordinamento, applicato
nell'ordine e senza compensazioni fra criteri:

1. **zero promozioni** dei 10 supporti errati;
2. **zero regressioni** sulle 16 claim già corrette in v2.1;
3. **massimo recupero** dei 14 supporti esatti oggi bloccati;
4. **massima accuratezza semantica** dei rifiuti (etichetta giusta, non solo
   rifiuto giusto);
5. **minima complessità** della modifica.

A parità piena vince la variante più semplice. La scelta è irrevocabile e va
fatta **prima** di generare la V12.

---

## 7. Metriche congelate

Calcolate dallo stesso codice già scritto,
`meta_governance/verification_horizon.py`, senza modifiche alla formula:

- `claim_corretta` = verdetto CLAIM **e** supporto esattamente uguale al vero;
- `claim_falsa` = CLAIM su caso non rappresentabile, su nullo, o con supporto
  diverso dal vero;
- `rifiuto_corretto` = qualunque verdetto di rifiuto su caso non
  rappresentabile o nullo;
- **orizzonte di accettazione** e **di rifiuto** ricalcolati sulla V12 con la
  stessa definizione: massimo quintile di difficoltà con utilità ≥ 80% e zero
  claim false.

Nessuna di queste definizioni può essere modificata dopo aver visto i
risultati. Se una definizione si rivelasse sbagliata, si dichiara l'errore e
si riparte con una nuova preregistrazione: non si aggiusta questa.

---

## 8. Esiti possibili, dichiarati in anticipo

| esito su V12 | lettura | azione |
|---|---|---|
| recall ≥ 60%, 0 claim false, rifiuti ≥ 98% | **PROMOSSA** | v2.2 sostituisce v2.1; orizzonte di accettazione misurabile per la prima volta |
| recall ≥ 60% **ma** ≥ 1 claim falsa | **RESPINTA** | il vincolo domina: v2.1 resta in vigore |
| recall ≥ 60%, 0 claim false, **ma** rifiuti < 98% | **RESPINTA** | il recall è stato comprato con rifiuti meno informativi |
| recall < 60% **e** 0 claim false | **NON RAGGIUNTO** | v2.1 resta; si riporta il recall ottenuto senza riformulare il target |
| recall < 40% (sotto la baseline) | **REGRESSIONE** | si indaga cosa la v2.2 ha rotto; nessuna promozione |

Quarta condizione, trasversale a tutte le righe: **nessuna modifica successiva
all'apertura della verità V12**. Aperta la V12, il risultato è quello che è.

L'esito «non raggiunto» **non è un fallimento del programma**: è la
misurazione di un limite, e va riportato con lo stesso rilievo di un successo.

---

## 9. Ledger

- **2026-08-01, apertura.** Preregistrazione creata dopo l'analisi di
  raggiungibilità dei 24 rifiuti prudenti, che ha stabilito il pool
  recuperabile a 14 e il tetto massimo a 30/40. La soglia di 24/40 è stata
  proposta dal committente e verificata come raggiungibile ma non automatica
  prima del congelamento.
- **2026-08-01, contaminazione.** I 90 casi V11 sono dichiarati development
  set permanente. Nessuna claim potrà più fondarsi su di essi.
- **2026-08-01, emendamento 01, prima di qualunque esecuzione.** Versione
  precedente sigillata `d6c6c854…`, nessuna run eseguita contro di essa.
  Modifiche, tutte irrigidimenti: (a) il vincolo passa da «tasso di claim
  false pari a zero», che su un campione finito non è misurabile, a «nessuna
  claim falsa osservata su ≥150 casi, limite superiore 2% per la regola del
  tre»; (b) aggiunte le sei varianti ammesse e i campi obbligatori di
  registrazione; (c) aggiunta la regola di selezione lessicografica a cinque
  criteri, che antepone «nessuna promozione dei 10 supporti errati» e «nessuna
  regressione sulle 16 corrette» al recall; (d) aggiunta la riga di esito
  «recall raggiunto ma rifiuti sotto il 98% = respinta»; (e) esplicitato che
  dopo l'apertura della V12 non sono ammesse modifiche.
- Ogni variante valutata sullo sviluppo va aggiunta qui, con data,
  motivazione, formula, parametri e hash del codice, **prima**
  dell'esecuzione.

### Varianti registrate (2026-08-01, prima dell'esecuzione)

Diagnosi che le motiva, dal codice della v2.1: `swap_rel` dichiara
NOT_IDENTIFIABLE se una qualunque sostituzione di un termine del supporto con
uno fuori supporto produce residuo `r < 2 · rel_base`. Il criterio **non ha
nozione del pavimento di rumore**: quando `rel_base` è 0,015, la soglia è
0,030, e a quel livello le alternative non sono distinguibili dal rumore. È
il meccanismo che blocca gli 8 casi di classe C.

Tutte le varianti agiscono **solo** sul livello `identifiability_gate`; gli
altri sette livelli della ladder restano identici alla v2.1. Nessuna variante
può trasformare un rifiuto in CLAIM su un caso il cui supporto selezionato
differisce dal vero: quella condizione è a monte del gate.

| # | formula | parametri | criterio di rigetto |
|---|---|---|---|
| **V1** condizionata al supporto | l'alternativa conta solo se sostituisce un termine con coefficiente non trascurabile: `\|c_j\| / max\|c\| ≥ κ` | κ = 0,05 | promuove anche un solo supporto errato |
| **V2** soglia adattiva sul margine | l'alternativa conta se `r < 2·rel_base` **e** `r − rel_base > ε · noise_floor` | ε = 0,5 | idem |
| **V3** identificabilità locale | swap ristretto ai termini della stessa famiglia differenziale del termine sostituito | famiglie: {const, v, v2}, {v_x, vv_x, div_vv_x}, {v_xx} | idem |
| **V4** eccitazione insufficiente | se il gate fallisce ma i coefficienti sono coerenti fra le 4 traiettorie (`CV < δ`), il verdetto è `INSUFFICIENT_EXCITATION` invece di `NOT_IDENTIFIABLE` | δ = 0,25 | cambia l'etichetta di un rifiuto corretto in CLAIM |
| **V5** consenso multi-seed | il gate fallisce solo se fallisce su ≥ m semi di selezione | semi {7, 11, 13, 17, 19}, m = 3 | idem |
| **V6** combinazione | le due migliori fra V1–V5 secondo la regola lessicografica, da registrare qui prima dell'esecuzione | — | — |

Ordine di esecuzione: V1, V2, V3, V4, V5, poi V6. Hash del codice
registrato nell'artifact di sviluppo.

**V4 non è una variante di recupero**: non può aumentare il recall, perché
cambia solo l'etichetta di un rifiuto. Entra nella regola lessicografica al
criterio 4 (accuratezza semantica dei rifiuti), non al 3.

---

Stato di partenza, per riferimento: v2.1, 16/40 claim corrette, 24 rifiuti
prudenti, 0 claim false su 90 casi ciechi, orizzonte di rifiuto 0,725,
orizzonte di accettazione non definito.

---

## Ledger — 2026-08-01: esito delle varianti sul development set

Eseguito `CDE_V12_LADDER_VARIANTS_DEV_V0.py` sui 90 casi V11. **Development
performance, non validazione.** La V12 non è stata generata né aperta.

| variante | recall | corrette | recuperati | regressioni | **claim false** |
|---|---|---|---|---|---|
| v2.1 riferimento | 0,400 | 16 | 0 | 0 | **0** |
| V3 locale | 0,400 | 16 | 0 | 0 | 0 |
| V4 eccitazione | 0,400 | 16 | 0 | 0 | 0 |
| V5 consenso | 0,400 | 16 | 0 | 0 | 0 |
| V1 condizionata (κ=0,05) | **0,600** | 24 | 8 | 0 | **2** |
| V2 adattiva (ε=0,5) | **0,600** | 24 | 8 | 0 | **5** |

**Nessuna variante soddisfa la preregistrazione.** L'ordinamento lessicografico
seleziona il riferimento, cioè *non modificare nulla*: V1 e V2 raggiungono il
bersaglio di recall ma violano il vincolo dominante, e §1 dice che una v2.2 che
produce anche una sola claim falsa è respinta, non discussa.

### Tre diagnosi che valgono più del risultato

**1. V3, V4 e V5 non hanno cambiato un solo verdetto.** V4 non ha mai attivato
la soglia δ=0,25 (`insufficient_excitation: 0`). Ne segue che il blocco degli 8
casi di classe C è **sistematico e stabile fra i semi**, non un artefatto di
rumore: le alternative che fanno scattare il gate appartenevano già alla stessa
famiglia differenziale (V3 inefficace) ed erano concordi su tutti e cinque i
semi (V5 inefficace). Il gate non sbaglia per caso: sbaglia per criterio.

**2. V1 e V2 recuperano esattamente gli stessi 8 casi.** Il pool recuperabile è
lo stesso; cambia solo il danno collaterale.

**3. Le claim false di V1 sono un sottoinsieme proprio di quelle di V2.**
V1 → {case_019, case_050}; V2 → {case_002, case_019, case_050, case_053,
case_058}. Il meccanismo di V1 è **strettamente migliore** di quello di V2, e
V2 può essere abbandonata senza ulteriore analisi.

---

## Variante V6, registrata prima dell'esecuzione

La definizione originale («combinazione delle migliori due») non è più
applicabile: solo un meccanismo funziona, e combinare V1 con varianti che non
cambiano nulla darebbe V1. V6 è quindi ridefinita, prima del run, come la
domanda che i risultati rendono decisiva.

**Formula.** Identica a V1 — il gate ignora un'alternativa entro 2× se il
coefficiente del termine sostituito è trascurabile — con κ **variabile** su una
griglia dichiarata ora:

```
κ ∈ {0,005; 0,01; 0,02; 0,03; 0,05; 0,075; 0,10; 0,15; 0,20; 0,30}
```

**Domanda.** Esiste un κ con `recuperati > 0` **e** `claim_false = 0`?

In altri termini: la statistica |c_drop| / max|c| **separa** gli 8 recuperi veri
dalle 2 promozioni errate, oppure le due popolazioni si sovrappongono?

**Criterio di selezione.** Il κ che massimizza `recuperati` sotto il vincolo
`claim_false = 0`. A parità, il κ più piccolo.

**Criterio di rigetto, congelato ora.** Se nessun κ della griglia soddisfa
entrambe le condizioni, **V6 è respinta** e la conclusione preregistrata è:
*il gate di identificabilità non è rilassabile lungo questo asse senza produrre
claim false, e il 40% di recall è il tetto di questa ladder.* In quel caso non
si cerca un terzo asse dentro questa campagna: si dichiara l'esito e ci si
ferma.

**Limite dichiarato prima di guardare.** Un κ scelto così è un iperparametro
**adattato sul development set**. Zero claim false su 10 casi a supporto errato
dà, per la regola del tre, un limite superiore del 30% — una garanzia molto
debole. Nessuna conclusione su V6 può essere presentata come evidenza: solo la
V12 cieca con ≥150 casi da rifiutare può sostenerla. Se V6 passa qui, ha
guadagnato il diritto di essere testata, non di essere creduta.

**Nota di implementazione.** Lo sweep richiede di ricostruire gli stati a monte,
~50 minuti. Lo script viene modificato per salvarli su disco e riusarli: la
modifica tocca solo la persistenza, nessun gate e nessuna soglia. Entrambi gli
hash del codice restano nel ledger.

---

## Ledger — 2026-08-01: esito V6 e difetto della griglia

| κ | corrette | recuperati | claim false | casi falsi |
|---|---|---|---|---|
| 0,005 – 0,075 | 24 | 8 | **2** | 019, 050 |
| 0,100 – 0,300 | 24 | 8 | **3** | 002, 019, 050 |

Verifica interna a κ=0,05 contro V1 (24 corrette, 8 recuperi, 2 false):
**coerente**. Il gate dello sweep è lo stesso di V1.

**Verdetto congelato: V6_RESPINTA.** Nessun κ della griglia recupera qualcosa
a zero claim false. Il criterio di rigetto era registrato prima del run e resta
vincolante.

### Ma la griglia non poteva rispondere alla domanda

Va detto perché è un difetto del mio disegno, non un risultato.

Per costruzione, **κ = 0 coincide esattamente con la v2.1**: la condizione
`|c_drop|/max|c| ≥ κ` diventa sempre vera, il gate torna a essere «nessuna
alternativa entro 2×», e il punteggio è 16 corrette / 0 false.

Al valore più basso della griglia, κ = 0,005, si osservano già 24 corrette,
8 recuperi e 2 claim false. **L'intera transizione fra il comportamento della
v2.1 e quello di V1 avviene quindi sotto il valore minimo della griglia**, in
un intervallo che non è stato campionato in nessun punto.

Ne segue che il run **non ha misurato la domanda preregistrata**. La domanda
era se |c_drop|/max|c| separi gli 8 recuperi veri dalle 2 promozioni errate;
la separazione, se esiste, vive in (0; 0,005), dove la griglia ha risoluzione
nulla. Sopra 0,005 le due popolazioni sono entrambe già passate, e osservarle
insieme non dice se siano separabili.

Nel linguaggio della ladder: l'esito corretto di questo run come *misura* è
**NOT_IDENTIFIABLE**, non REJECTED. Lo strumento non aveva risoluzione dove
sta la risposta.

**Cosa resta vero.** Il verdetto preregistrato V6_RESPINTA resta in vigore e
non viene riscritto: la griglia era dichiarata prima, e allargarla dopo aver
visto i numeri è esattamente ciò che la preregistrazione vieta.

**Cosa resta aperto.** La domanda scientifica non è risolta. Risolverla
richiede una **nuova preregistrazione** (V6-bis) con una griglia che racchiuda
la transizione — per esempio κ ∈ {1e-5 … 5e-3} in scala logaritmica — non un
emendamento a questa. La cache degli stati a monte è ora su disco, quindi il
costo di quel run è di secondi, non di cinquanta minuti: non c'è alcuna
pressione a decidere in fretta.

**Errore da non ripetere.** Una griglia di iperparametri va scelta in modo da
**racchiudere il comportamento di riferimento** ai suoi estremi. Se avessi
incluso κ = 0 nella griglia, l'assenza di risoluzione sarebbe stata visibile
prima del run invece che dopo.
