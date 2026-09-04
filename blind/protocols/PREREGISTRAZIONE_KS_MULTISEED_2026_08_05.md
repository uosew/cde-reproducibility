# Preregistrazione — CDE_KS_MULTISEED_CHARACTERIZATION

**2026-08-05. Congelata prima di lanciare qualunque seme KS.**

---

## 1. Una correzione, prima di tutto il resto

Ieri, chiudendo la caratterizzazione dei quattro sistemi V8, ho scritto nella
nota che il limite «Seeds» restava aperto per Kuramoto–Sivashinsky perché

> *KS, whose cost per seed made 20 realizations impractical here*

**È falso, ed è un'affermazione che non avevo misurato.** Il costo reale:

    V8 (quattro sistemi)   9-13 minuti a seme
    KS (un sistema)         2,6 minuti a seme

KS è **cinque volte più economico**, non più caro. Venti semi costano circa
cinquantadue minuti. La frase è stata scritta per giustificare una lacuna invece
che per descrivere un vincolo, ed è il tipo di errore che questa campagna esiste
per rendere impossibile.

La correzione della nota fa parte di questa campagna e avviene comunque, quale
che sia l'esito dei venti semi.

---

## 2. Che cosa si chiude, e che cosa no

Il caso caotico è l'unico dei cinque sistemi della nota a poggiare ancora su due
semi. Questa campagna lo caratterizza. **Non** tocca gli altri quattro limiti
dichiarati — dati sintetici, contenimento della libreria, preflight oracolare,
osservazione liscio/caotico — che restano aperti.

Il perimetro della claim resta quello della claim card V9: PDE 1D periodica,
solver spettrale, `L = 32π`, rumore gaussiano di misura, libreria estesa col
termine `u_xxxx` validato dal track D4 **prima** della discovery.

---

## 3. I semi

    semi = 101, 102, ..., 120        gli STESSI usati per V8

Riusare gli stessi venti non è una scorciatoia: rende le due caratterizzazioni
confrontabili seme per seme e **toglie una scelta**. Un elenco nuovo generato
adesso sarebbe una decisione presa da me, e quindi una decisione da giustificare.

I semi **7 e 11 non entrano nella stima**, per la stessa ragione di V8: sono
quelli che hanno prodotto la claim originale. Riportati a parte.

**Nessun seme aggiunto, rimosso o sostituito dopo aver visto un risultato.** Un
seme che fallisce per ragione tecnica si riporta come fallito.

## 4. Che cosa NON cambia

`CDE_KS_DISCOVERY_V9.py` **non viene modificato**: la campagna lo esegue come è,
cambiando solo `--seed`.

Gli artefatti sigillati del seme 7 (`results.json` `9b4a119d6ed677d2…`,
`evidence_envelope.json` `afbf54c2ec7aca73…`, `claim_card.md`
`5e1ba1961236d00e…`) vengono verificati prima, messi in salvo, ripristinati dopo
e riverificati. V9 scrive su percorso fisso e li sovrascriverebbe.

---

## 5. Endpoint e soglie

`S1`, `S2` e `S3` sono **ereditati invariati** dalla preregistrazione V8. Non
sono stati riscelti: cambiarli qui renderebbe le due campagne non confrontabili,
ed è precisamente il momento in cui una soglia verrebbe ritoccata sapendo dove
sta la difficoltà.

### S1 — recupero esatto del supporto a rumore nullo *(primario)*

| esito | condizione |
|---|---|
| `CONFERMATA` | ≥ **19/20** |
| `PROBABILISTICA` | fra **15/20** e **18/20** |
| `NON_SOSTENUTA` | < **15/20** |

### S2 — recupero al 10% di rumore

    >= 15/20

### S3 — falsi positivi sui nulli

    FDR <= 0,05        (la claim originale dice 0, su 10 run per seme)

### S5 — tenuta del gate al 10% di rumore *(criterio nuovo)*

    gate_pass >= 15/20 a sigma = 0,10

**Questo criterio è nuovo e va giustificato apertamente.** Non esisteva nella
preregistrazione V8, e lo introduco perché la campagna V8 ha scoperto che il gate
è la parte fragile: su Allen–Cahn a rumore 10% il supporto è esatto in 20 semi su
20 ma il gate ne rifiuta 9.

Aggiungere un criterio sapendo *dove* sta la debolezza non è selezione a
posteriori finché il criterio è fissato **prima di vedere i dati del sistema che
giudica** — e su KS non ho ancora alcuna informazione sul comportamento del gate.
La soglia è la stessa di `S2`, per non inventarne una seconda.

Se avessi lasciato il gate fra i descrittivi, questa campagna non avrebbe potuto
fallire proprio sulla cosa che l'altra ha rivelato.

### S4 — descrittivi, senza soglia

Errore relativo dei coefficienti per livello di rumore; `sigma_star_first_fail`;
esito del track D4 per seme; tempo per seme. Si riportano, non si giudicano.

---

## 6. Attesa a priori, registrata ora

- **`S1` `CONFERMATA`**: il supporto KS è a tre termini con `u_xxxx` validato a
  parte, e i due semi storici lo recuperano con errore `6·10⁻⁶`.
- **`S5` genuinamente incerto**, ed è la ragione della campagna. Un campo caotico
  ha residui più strutturati di uno liscio: se il gate è conservativo ad alto
  rumore su Allen–Cahn, su KS potrebbe esserlo di più.

**L'attesa a priori di ieri era sbagliata.** Avevo previsto incertezza su
`burgers` e `kdv` e sicurezza su `allen_cahn`; sono usciti tutti `20/20` sul
recupero, e la fragilità è emersa proprio su `allen_cahn`, e nel gate. Lo scrivo
qui perché una previsione sbagliata due volte di fila su quale sia il punto
debole è essa stessa un'informazione.

---

## 7. Conseguenze

- `S1 CONFERMATA` **e** `S5 PASS` → la nota dichiara il limite «Seeds» **chiuso
  per tutti e cinque i sistemi**.
- `S1 CONFERMATA` **e** `S5 FAIL` → il limite si chiude sul recupero e si apre un
  limite nuovo, esplicito, sulla tenuta del gate in regime caotico.
- `S1 PROBABILISTICA` → la claim card V9 va emendata: «recupero esatto» diventa
  «recupero esatto in *k*/20 realizzazioni».
- `S1 NON_SOSTENUTA` → claim card retrocessa e ledger aggiornato.

In ogni caso gli artefatti dei semi 7 e 11 restano dove sono, invariati.

---

## 8. Divieti

- Nessuna modifica a `CDE_KS_DISCOVERY_V9.py`.
- Nessun seme aggiunto, rimosso o sostituito dopo aver visto un risultato.
- Nessuna soglia ritoccata dopo il conteggio; `S1`–`S3` restano quelle di V8.
- I semi 7 e 11 non entrano in `S1`, `S2`, `S3`, `S5`.
- Una sola esecuzione per seme.
- `.venv313`; Python 3.14 vietato.

## 9. Provenienza richiesta

`runtime_guard` per seme, `source_sha256` di V9, dell'orchestratore e
dell'aggregatore, `prereg_sha256` di questo file, elenco completo dei venti semi
con esito, hash degli artefatti del seme 7 prima e dopo,
`execution_mode = SCIENTIFIC`.
