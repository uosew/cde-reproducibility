# Preregistrazione CDE V13 — replica su larga scala della ladder v2.1, su due architetture

Data: 2026-08-02. Stato: **PREREGISTRATO PRIMA DI GENERARE QUALUNQUE CASO.**

---

## 1. Che cosa NON e' questa campagna

**Non e' il test della ladder v2.2.** Quel test e' chiuso: V6 respinta, V6-bis
ammessa solo per la lettera del criterio ma con un solo recupero, cioe' recall
42,5% contro un target del 60%. Eseguire una campagna cieca per la v2.2 sarebbe
un fallimento predeterminato, e non si fa.

**Non si tocca nessun gate.** La ladder resta la v2.1 congelata, bit per bit. Se
durante questa campagna venisse la tentazione di modificarla, la campagna va
fermata e ricominciata sotto una nuova preregistrazione.

Questa campagna cambia **una cosa sola**: la dimensione della popolazione di test.

---

## 2. Le due domande, entrambe di sola misura

**Domanda A — quanto e' stretto il limite sulle claim false?**

L'affermazione piu' forte che il sistema puo' fare su di se' e' «zero claim false
osservate». Oggi poggia su **60 opportunita' di mentire** nella campagna V11:

| categoria | casi V11 |
|---|---|
| nulli | 10 |
| non rappresentabili | 40 |
| rappresentabili su cui il sistema ha prodotto un supporto errato | 10 |
| **totale opportunita'** | **60** |

Zero false su 60 da', per la regola del tre, un limite superiore approssimativo
del **5,0%**. Non possiamo cioe' escludere che il sistema affermi il falso una
volta su venti. E' un limite debole, e si stringe soltanto aumentando i casi.

**Domanda B — i verdetti sono gli stessi su architetture diverse?**

La replica su `.venv312` gira sulla stessa CPU, lo stesso sistema operativo e la
stessa libreria di algebra lineare del Mac: se un risultato dipendesse da una
peculiarita' di quella combinazione, non se ne accorgerebbe. Il nodo Windows
(AMD64, Windows 11, BLAS diverso) con **librerie allineate** — python 3.13,
numpy 2.5.1, scipy 1.18.0 — isola la piattaforma come unica variabile.

---

## 3. Popolazione, congelata ora

- **600 casi** generati con `CDE_V11_BLIND_GENERATOR_V0.py`, parametri e classi
  invariati, **seme nuovo e dichiarato nel ledger prima della generazione**.
- Proporzioni attese in base alla V11 (40 rappresentabili / 10 nulli / 40 non
  rappresentabili su 90): circa **267 rappresentabili, 67 nulli, 267 non
  rappresentabili**.
- Opportunita' di mentire attese ~ 67 + 267 + (quota di rappresentabili con
  supporto errato, ~25% nella V11) ~ **400**.

**Soglia di successo per la domanda A, congelata:** almeno **350 opportunita' di
mentire effettive**. Sotto questa soglia il guadagno sul limite non giustifica la
campagna, e l'esito va dichiarato come tale invece di essere presentato come un
risultato.

| opportunita' | limite superiore (regola del tre) |
|---|---|
| 60 (oggi) | 5,0% |
| 350 | 0,86% |
| 400 | 0,75% |

---

## 4. Ripartizione fra i nodi, e perche' non e' una semplice divisione

Dividere i 600 casi a meta' darebbe il limite piu' stretto nel minor tempo, ma
**non risponderebbe alla domanda B**: nessun caso sarebbe stato visto da entrambe
le macchine, e non ci sarebbe niente da confrontare.

Ripartizione congelata:

| nodo | casi |
|---|---|
| Mac (arm64) | 001-350 |
| Windows (AMD64) | 251-600 |
| **sovrapposizione, eseguita da entrambi** | **251-350 (100 casi)** |

L'unione copre tutti i 600 per la domanda A; i 100 in comune rispondono alla
domanda B. Ogni nodo esegue 350 casi: stimando dai 90 casi della V12 (~50
minuti), circa **3 ore e mezza per nodo**, in parallelo.

---

## 5. Regola di confronto fra i nodi, congelata

Sui 100 casi in sovrapposizione si confrontano, per ciascun caso:

1. il **verdetto** della ladder (CLAIM / NOT_IDENTIFIABLE / ...);
2. il **supporto** selezionato, come insieme;
3. il livello al quale la ladder si e' fermata (`blocked_at`).

**Accordo pieno** = i tre coincidono su tutti e 100 i casi.

**Qualunque discrepanza e' un risultato, non un fastidio.** Non va spiegata a
posteriori ne' attribuita a «rumore numerico» senza prove: va riportata caso per
caso, con i valori delle due macchine, e **blocca la claim sul limite stretto**
finche' non e' compresa. Un sistema che da' verdetti diversi su architetture
diverse non ha un limite di errore ben definito, perche' non e' chiaro *di quale*
sistema sarebbe il limite.

I residui numerici possono differire nelle ultime cifre senza che questo sia una
discrepanza: **si confrontano i verdetti, non i float**.

---

## 6. Esiti dichiarati in anticipo

| esito | condizione | significato |
|---|---|---|
| **LIMITE_STRETTO** | >=350 opportunita', **zero** claim false, accordo pieno sui 100 condivisi | il limite scende sotto l'1%: l'affermazione difensiva diventa solida |
| **CLAIM_FALSA_OSSERVATA** | >=1 claim falsa | **e' il risultato piu' prezioso della campagna.** Si conserva il caso, si analizza, e la caratterizzazione «forte verificatore difensivo» va riscritta |
| **DIVERGENZA_PIATTAFORMA** | discrepanza sui 100 condivisi | il limite resta quello vecchio; si indaga la causa prima di qualunque altra cosa |
| **POTENZA_INSUFFICIENTE** | <350 opportunita' | si dichiara, e non si spaccia il risultato per un miglioramento |

Nota su `CLAIM_FALSA_OSSERVATA`: **non e' un fallimento della campagna, e' il suo
scopo.** Una campagna che puo' solo confermare cio' che spera non e' un test. Se
il sistema mente una volta su 400, e' infinitamente piu' utile scoprirlo qui che
davanti a qualcuno che si fida.

---

## 7. Cecita' e integrita'

- La verita' resta sigillata in `sealed/truth.json` e **non viene letta** finche'
  entrambi i nodi non hanno prodotto tutti i verdetti.
- I casi V11 esistenti **non entrano** in questa campagna: la loro verita' e'
  aperta da giorni e sono ormai development set.
- Il seme di generazione viene registrato nel ledger **prima** del run.
- Nessun caso viene rigenerato, scartato o sostituito dopo aver visto un verdetto.

---

## 8. Ambiente

| | Mac | Windows |
|---|---|---|
| python | 3.13.10 | 3.13.5 |
| numpy | 2.5.1 | 2.5.1 |
| scipy | 1.18.0 | 1.18.0 |
| piattaforma | macOS arm64 | Windows 11 AMD64 |
| percorso | `<node-mac>` | `<node-win>` |
| commit | dichiarato nel ledger | dichiarato nel ledger |

`enforce_runtime_guard(strict=True)` obbligatorio su entrambi, con esito allegato
agli artifact. Il nodo Windows e' raggiunto per **hostname verificato**
(`<hostname>`) su rete privata, mai per indirizzo di LAN.

---

## 9. Ledger

| data | voce |
|---|---|
| 2026-08-02 | preregistrazione creata. Nessun caso generato, nessun seme ancora estratto. |
| 2026-08-02 | **semi registrati prima della generazione.** `SEME_MODELLO = 700000` (rng del modello, `700000+k`), `SEME_DEGRADO = 710000` (degradazione della camera, `710000+k*10+i`), `SEME_NULLO = 900000` (campi nulli di classe H, `900000+k*10+i`). Basi diverse da quelle della V11 (`5000+k`, `300+i`, `9000+k*10+i`): i casi devono essere nuovi, non gli stessi modelli rietichettati. |
| 2026-08-02 | **numero di casi: 603, non 600.** Le classi sono 9 e vanno mantenute bilanciate, quindi il totale deve essere multiplo di 9: 67 per classe danno 603, il primo multiplo utile a partire da 600. Scarto dichiarato prima del run, non aggiustato dopo. |
| 2026-08-02 | generatore `CDE_V13_BLIND_GENERATOR_V0.py` creato. Riusa per importazione `draw_model`, `simulate`, `sample_camera`, `CLASSES` e `ICS_BASE` del generatore V11: la fisica e' la stessa per costruzione, non per somiglianza. |
| 2026-08-02 | **intervalli adattati alla numerazione reale.** La §4 diceva «Mac 001-350, Windows 251-600» assumendo indici da 1, ma il generatore produce `case_000`-`case_602`. Intervalli effettivi: **Mac 000-350** (351 casi), **Windows 251-602** (352 casi), **sovrapposizione 251-350 (100 casi)**, unione 000-602 = tutti i 603. Intento invariato: sovrapposizione di 100 casi per la domanda B, copertura totale per la domanda A. Adattamento dichiarato prima del lancio. |
| 2026-09-03 | **SBENDAMENTO** (30 giorni dopo i verdetti). Scorer `CDE_V13_BLIND_UNBLINDING_V0.py`, 8 mutation test. Esito §6: **CLAIM_FALSA_OSSERVATA** — 14 claim false su 423 opportunità (3,3 %), tutte in classe C, tutte claim di sotto-supporto (manca `div_vv_x`, coefficiente α·γ ≈ 5e-7, ~0,5 % della dinamica); 0 su nulli, 0 su non rappresentabili; Domanda B accordo pieno 100/100. Sigillo procedurale, non crittografico (nessuno sha della verità negli envelope; stesso commit): dichiarato. Claim card `CLAIM_CARD_V13_UNBLINDING_2026-09-03.md`. |
