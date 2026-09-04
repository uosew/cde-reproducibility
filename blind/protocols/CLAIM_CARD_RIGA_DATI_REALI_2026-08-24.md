# Claim card — riga `Validazione su dati sperimentali reali` della matrix V10

**Verdetto:** NOT_TESTABLE

| | |
|---|---|
| riga | `Validazione su dati sperimentali reali`, oggi `NOT_TESTED` |
| unico dataset reale nel perimetro | termografia pulsata CFRP/GFRP, DOI `10.17632/v4knrwgj9y.2`, 5.6 GB, gitignored con sha256 in `data_real_thermography/FILE_INDEX.json` |
| campagna gia' eseguita su quel dataset | `CDE_REAL_THERMOGRAPHY_V0.py`, preregistrata il 2026-08-07 |
| esito di quella campagna | **REJECTED** — preflight chiude 10/10 |
| stato della matrix | invariato a `NOT_TESTED` |

---

## 0. Due claim distinte, e i loro due verdetti

E' la distinzione da cui dipende tutto il resto, e va fatta prima.

| | claim | verdetto |
|---|---|---|
| **specifica** | il CDE recupera la legge di diffusione da **questo** osservabile termografico | **REJECTED** |
| **generale** (la riga) | il CDE recupera una legge di governo da **dati misurati reali** | **NOT_TESTABLE** |

La campagna termografica ha falsificato la prima. Non ha testato la seconda,
perche' il preflight — il cancello che accerta se i dati abbiano la risoluzione
richiesta — si e' chiuso su tutte e dieci le sequenze: il motore non e' mai
arrivato al punto in cui la claim generale sarebbe stata in gioco.

**Questa separazione non e' una ricostruzione fatta oggi.** La
preregistrazione del 2026-08-07, §"Esiti dichiarati come legittimi", la mappa
esplicitamente, prima delle run:

> **REJECTED**: il preflight chiude → i dati sono inadeguati alla risoluzione
> richiesta. **La riga resta `NOT_TESTED`** ma con un limite quantificato.

Era gia' scritto che questo esito avrebbe respinto la campagna **senza**
chiudere la riga. Il documento presente non decide nulla di nuovo: registra che
il perimetro non contiene altro materiale con cui riaprirla.

---

## 1. Cosa affermerebbe la riga se fosse vera

> Il CDE recupera una legge di governo da **dati misurati reali**, con la stessa
> disciplina con cui lo fa sui sistemi sintetici: supporto esatto, controllo
> negativo superato, replica su due runtime.

E' falsificabile. Non e' stata falsificata: e' stata lasciata non testata da un
esperimento che si e' fermato a monte.

---

## 2. Perche' oggi non e' testabile

Il repository contiene **un solo** dataset sperimentale reale. Su quello la
campagna e' gia' stata eseguita, con questi numeri:

| | |
|---|---|
| preflight `P3 < 0.05` | chiuso in **10/10** sequenze |
| miglior `P3` osservato | `0.0780` contro gate `0.05` |
| nulli | 0 falsi ritrovamenti su 100 |
| replica | 3.13 e 3.12, stesso esito |

Rieseguire la stessa campagna sugli stessi dati darebbe lo stesso risultato. Per
mettere alla prova la claim generale servono **altri dati**, che nel perimetro
non ci sono.

La preregistrazione vieta inoltre di riaggiustare finestre, ritagli o soglie
dopo aver visto i risultati: un secondo tentativo richiede una nuova
preregistrazione, con un nuovo identificativo e la dichiarazione esplicita del
primo esito. Nessuna scorciatoia sullo stesso dataset e' ammessa.

---

## 3. Cosa il fallimento ha lasciato, e con quale grado di certezza

Vale la pena registrarlo, ma con i livelli di confidenza separati — perche' non
sono uguali.

**Accertato**: il preflight chiude su tutte le sequenze, con la motivazione
preregistrata «dati inadeguati alla risoluzione richiesta». E' una misura.

**Interpretazione, non testata**: la spiegazione strutturale piu' plausibile e'
che la termografia pulsata misuri diffusione di calore attraverso una
superficie, con la dimensione di profondita' collassata nell'osservabile —
mentre la PDE che governa il fenomeno vive in tre dimensioni spaziali. E'
dedotta dalla geometria fisica del dataset, non da un esperimento. Dimostrarla
richiederebbe far sparire il problema recuperando l'informazione di profondita',
o usando un osservabile equivalente. Non e' stato fatto.

Quanto a un dataset candidato per riaprire la riga, cio' che si puo' dire senza
sovra-interpretare e': processo governato da una PDE **nelle dimensioni
effettivamente misurate**, campionamento adeguato in spazio e tempo, SNR
sufficiente.

---

## 4. La riformulazione che ho scartato, e perche'

Una via alternativa esisteva: riformulare la riga come «su dati reali fuori
inviluppo il CDE **si astiene correttamente**». Quella claim e' vera, e la
campagna termografica la dimostra — 10 astensioni su 10, nulli 0/100.

Diventerebbe `CONFIRMED`.

**Non l'ho fatto.** La riga chiede se il CDE sappia **scoprire** su dati reali;
l'astensione corretta e' una capacita' diversa e piu' debole, gia' coperta da
altre righe della matrix (`Null rejection`, `Governance della claim`).
Trasformare un fallimento in un successo cambiando la domanda e' precisamente la
mossa che questa infrastruttura esiste per intercettare — la stessa famiglia
dell'abbassare `V_ITG2` da 25/25 a 23/25 perche' la riga diventi verde.

---

## 5. Cosa questo NON dimostra

- **Non dimostra che il CDE non funzioni su dati reali.** Dimostra che non
  funziona su **questi** dati reali, e che il perimetro non ne contiene altri.
- **Non dimostra che il fattore 1.6** (`0.0780` contro `0.05`) **sia
  colmabile.** E' la distanza dal gate misurata su un dataset inadeguato: non
  dice nulla su quanto sarebbe facile colmarla, ne' quale distanza si
  osserverebbe su dati adatti.
- **Non stabilisce la causa del fallimento.** Vedi §3: la spiegazione della
  profondita' non osservata e' un'interpretazione, non un risultato.
- **Non chiude la ricerca di dati.** `NOT_TESTABLE` qui significa «non con il
  materiale disponibile oggi», non «mai».

---

## 6. Nota sugli artefatti

Nessun esperimento eseguito: la chiusura avviene al passo 1-2, quando si accerta
che i dati necessari non esistono nel perimetro. Gli artefatti sono **tre**
invece di cinque — claim card, voce di ledger, commit. Mancano il runner e
l'analyzer perche' non c'era nulla da eseguire, e manca una preregistrazione
nuova perche' quella rilevante esiste gia' ed e' anteriore alle run:
`PREREGISTRAZIONE_REAL_THERMOGRAPHY_2026_08_07.md`, che governava la campagna il
cui esito questa riga registra e che aveva **gia' dichiarato** che quell'esito
non avrebbe chiuso la riga.

---

## 7. Ledger

| data | voce |
|---|---|
| 2026-08-24 | riga chiusa `NOT_TESTABLE` per perimetro dichiarato. Separazione preregistrata il 2026-08-07 fra claim specifica — «il CDE recupera la legge da questo osservabile termografico», `REJECTED`, preflight chiuso 10/10, miglior `P3` 0.0780 contro gate 0.05, nulli 0/100 — e claim generale della riga, mai messa in gioco perche' il preflight si chiude a monte. La prereg stabiliva gia' che `REJECTED` avrebbe lasciato la riga `NOT_TESTED`. Unico dataset reale nel perimetro: termografia pulsata CFRP/GFRP, DOI 10.17632/v4knrwgj9y.2, 5.6 GB. Spiegazione strutturale (profondita' non osservata) registrata come interpretazione non testata. Scartata la riformulazione della riga sull'astensione corretta, che l'avrebbe resa `CONFIRMED` cambiando la domanda. Stato nella matrix invariato a `NOT_TESTED`. |
