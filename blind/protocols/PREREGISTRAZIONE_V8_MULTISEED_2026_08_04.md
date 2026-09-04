# Preregistrazione — CDE_V8_MULTISEED_CHARACTERIZATION

**2026-08-04. Congelata prima di lanciare qualunque seme.**

---

## 1. Da dove nasce: la nota se lo dice da sola

Fra i limiti dichiarati in `arxiv_note/main.tex`:

> **Seeds.** Claims are verified on two independent seeds (7 and 11), which
> removes single-realization dependence but does not support a statistical
> characterization of recovery probability, coefficient variance or breakdown
> distributions. A journal version should use 10–30 seeds (or bootstrap
> confidence intervals) per system.

Questa campagna colma quel limite, e uno solo. **Non** tocca gli altri quattro —
dati sintetici, contenimento della libreria, preflight oracolare, osservazione
liscio/caotico — che restano aperti e dichiarati.

## 2. La cosa che rende la campagna onesta, e va detta per prima

**I semi 7 e 11 non entrano nella stima.** Sono i due che hanno prodotto la
claim: usarli per misurare quanto spesso la claim vale significherebbe stimare
una frequenza sui casi che l'hanno generata.

Vengono riportati a parte, come riferimento storico, e la loro esclusione è la
ragione per cui questa campagna può smentire l'originale invece di confermarla
per costruzione.

## 3. I semi, fissati ora

    semi = 101, 102, ..., 120        venti, consecutivi, dichiarati qui

Consecutivi e non estratti: un elenco «casuale» generato adesso sarebbe
indistinguibile da un elenco scelto fra diversi. Venti è il limite basso
dell'intervallo 10–30 raccomandato dalla nota, ed è vincolato dal costo: nove
minuti a seme, quattro sistemi, cinque livelli di rumore.

**Nessun seme verrà aggiunto o rimosso dopo aver visto un risultato.** Se un seme
fallisce per una ragione tecnica — eccezione, ambiente — viene riportato come
fallito, non sostituito.

## 4. Che cosa NON cambia

`CDE_PDE_DISCOVERY_V8.py` **non viene modificato**. Nessuna costante, nessuna
soglia, nessun parametro: la campagna lo esegue come è sigillato, cambiando solo
`--seed`.

Gli artefatti del seme 7 (`results.json` `e5662ad857671b4d…`,
`evidence_envelope.json` `0a606e342120f71d…`, `claim_card.md`
`d59723eb72a12c43…`) vengono salvati prima, ripristinati dopo, e i loro hash
riverificati. Lo script scrive su percorso fisso e li sovrascriverebbe: è un
difetto noto dell'orchestrazione, non del protocollo, e si gestisce spostando gli
output invece di toccare V8.

## 5. Endpoint e soglie

### S1 — recupero esatto del supporto a rumore nullo *(primario)*

Per ciascuno dei quattro sistemi, su venti semi:

| esito | condizione |
|---|---|
| `CONFERMATA` | ≥ **19/20** su **tutti e quattro** i sistemi |
| `PROBABILISTICA` | fra **15/20** e **18/20** su almeno un sistema |
| `NON_SOSTENUTA` | < **15/20** su almeno un sistema |

**Ancoraggio.** La claim originale è di recupero *esatto*, non frequente. Una
proprietà dichiarata esatta che si verifica 18 volte su 20 non è falsa: è
un'altra proprietà, e va scritta con l'altra parola. La soglia di 19/20 lascia
spazio a un singolo caso limite senza consentire una coda.

### S2 — recupero al 10% di rumore

    >= 15/20 per sistema  perche' la formulazione «fino al 10% di rumore» regga

Sotto quel livello la formulazione va indebolita nella nota, indicando il livello
di rumore effettivamente sostenuto.

### S3 — falsi positivi sui nulli

    FDR aggregata su tutti i semi e tutti i sistemi <= 0,05

La claim originale dice **0**. Un solo falso positivo su venti semi non la
falsifica ma la trasforma in una stima con intervallo, e va riportato come tale.

### S4 — descrittivi, senza soglia

Distribuzione dell'errore relativo dei coefficienti per sistema e per livello di
rumore; distribuzione di `sigma_star_first_fail`; tempo per seme. Si riportano,
non si giudicano: servono alla versione da rivista, non a decidere un esito.

## 6. Attesa a priori, registrata ora

`CONFERMATA` su `allen_cahn` e `fisher_kpp`, incertezza reale su `burgers` e
`kdv`. Ragione: i primi due hanno supporto a tre termini con struttura
polinomiale netta; `kdv` dipende da una derivata terza, la più esposta al rumore,
ed è il sistema che nel protocollo non è mai stato usato per la messa a punto —
quindi anche quello con meno margine.

Se l'attesa risulta sbagliata, resta agli atti.

## 7. Conseguenze sull'artefatto esistente

- `CONFERMATA` → la nota aggiunge la caratterizzazione e **non cambia** le claim.
- `PROBABILISTICA` → la claim card di V8 va **emendata**: «recupero esatto»
  diventa «recupero esatto in *k*/20 realizzazioni», con il numero.
- `NON_SOSTENUTA` → la claim card viene **retrocessa** e il ledger aggiornato.

In tutti e tre i casi l'artefatto originale del seme 7 resta dov'è, invariato:
non si riscrive un risultato passato, si aggiunge quello nuovo accanto.

## 8. Divieti

- Nessuna modifica a `CDE_PDE_DISCOVERY_V8.py`.
- Nessun seme aggiunto, rimosso o sostituito dopo aver visto un risultato.
- Nessuna soglia ritoccata dopo il conteggio.
- I semi 7 e 11 **non entrano** in S1, S2, S3.
- Una sola esecuzione per seme; l'orchestratore rifiuta di sovrascrivere.
- `.venv313`; Python 3.14 vietato.

## 9. Provenienza richiesta

`runtime_guard` per ogni seme, `source_sha256` di V8 **e** dell'orchestratore,
`prereg_sha256` di questo file, elenco completo dei venti semi con il loro esito,
hash degli artefatti del seme 7 prima e dopo, `execution_mode = SCIENTIFIC`.
