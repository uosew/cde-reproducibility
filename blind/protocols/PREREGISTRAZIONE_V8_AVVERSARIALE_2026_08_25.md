# Preregistrazione — CDE_V8_AVVERSARIALE_SEMI_NUOVI_V0

**25 agosto 2026. Congelata prima di eseguire un solo seme nuovo.**

---

## 1. Perche' questa campagna esiste

La caratterizzazione multi-seme di V8 ha dato **20/20 su tutti e quattro i
sistemi**, sia a rumore zero sia al 10%, con FDR 0 su 800 run di nullo. Verdetto
`CONFERMATA`.

Un punteggio perfetto non e' una buona notizia: significa che **la prova non era
abbastanza dura per trovare il punto di rottura**. `sigma_star_first_fail` esce
`None` ovunque — il metodo non ha mai fallito dentro il perimetro provato, e
quindi il perimetro non e' stato misurato, e' stato solo superato.

La nota arXiv e' a un passo dalla sottomissione. Un difetto trovato adesso costa
qualche ora; lo stesso difetto trovato da un revisore costa la sottomissione.
**Questa campagna esiste per tentare di rompere una claim che credo vera**, ed e'
scritta prima di guardare qualunque risultato.

## 2. I semi, e perche' sono davvero nuovi

Semi gia' usati sulla linea V8: **7 e 11** (hanno prodotto la claim originale,
esclusi dalla stima) e **101-120** (la caratterizzazione).

Semi di questa campagna: **201-220**. Venti semi mai toccati da nessuna
esecuzione V8. Non vengono scelti, non vengono filtrati, non se ne scarta
nessuno dopo l'esecuzione.

## 3. Il motore non viene toccato

`CDE_PDE_DISCOVERY_V8.py`, impronta **`4a2181b8dbeda428`**, unica versione mai
esistita nella storia del repository. Nessuna modifica, nessun parametro
diverso: e' esattamente il codice che ha prodotto `CONFERMATA`.

Gli artefatti esistenti in `cde_pde_discovery_v8_out/` vengono salvati prima e
ripristinati dopo, con verifica per impronta: **questa campagna non puo'
sovrascrivere la campagna sigillata.**

## 4. `A1` — la replica, con le soglie congelate

Le soglie **non vengono ridiscusse**. Sono quelle di
`PREREGISTRAZIONE_V8_MULTISEED_2026_08_04.md`, riportate qui alla lettera.

| gate | criterio | soglia congelata |
|---|---|---|
| `S1` | `support_exact` a sigma 0, per sistema | **>= 19/20** confermata · >= 15/20 probabilistica |
| `S2` | `support_exact` a sigma 0,10, per sistema | **>= 15/20** per sistema |
| `S3` | falsi positivi sui nulli (20x4x10 = 800 run) | **FDR <= 0,05** |

### Regola di decisione, dichiarata adesso

- **`REPLICA`** — tutti e tre i gate passano su tutti e quattro i sistemi. La
  claim regge su semi mai visti.
- **`INDEBOLITA`** — `S1` scende fra 15/20 e 18/20 su almeno un sistema. La
  formulazione «recupero esatto» va sostituita con una frequenza dichiarata, e
  la nota va corretta **prima** della sottomissione.
- **`ROTTA`** — `S1 < 15/20` oppure `S2 < 15/20` oppure `FDR > 0,05` su almeno
  un sistema. La claim `CONFERMATA` non regge fuori dai semi su cui e' stata
  misurata e **va ritirata**, non attenuata.

Un solo sistema che fallisce basta: la claim e' su tutti e quattro.

## 5. `A2` — dove si rompe davvero, che nessuno ha mai misurato

La claim e' delimitata a rumore **<= 10%**. `A2` guarda **oltre** quel confine,
quindi per costruzione **non puo' rompere `A1`**: e' territorio nuovo, non una
seconda occasione di giudicare il vecchio.

Livelli: **0,15 · 0,20 · 0,30**, sui primi **cinque** semi nuovi (201-205).

Questo richiede un sorgente diverso — la costante `SIGMAS` del motore e' fissa.
Si usa una **copia dichiarata** del motore la cui unica differenza e' quella
riga; entrambe le impronte finiscono nell'artefatto, e la copia **non** viene
usata per `A1`. `A2` e' descrittivo e **senza soglia**: riporta, per ogni
sistema, il primo livello a cui `support_exact` cade.

## 6. Attesa a priori, registrata adesso

- **`A1` REPLICA.** 20/20 su venti semi con FDR 0 e' un precedente forte.
- **`A2`**: degrado fra il 15% e il 30%, e mi aspetto che **KdV ceda per primo**
  — e' l'unico con derivata terza, la piu' sensibile al rumore.

**Il mio precedente su queste attese e' pessimo e va pesato.** Nelle ultime
cinque campagne l'attesa registrata non ha retto, e sulla campagna degli orfani
ha sbagliato tutti e tre i punti, `S4` compreso. Se `A1` passasse sarebbe la
prima volta in sei che indovino, il che e' un motivo in piu' per aver scritto
la regola di decisione prima.

## 7. Divieti

- Nessuna modifica alle soglie di `S1`, `S2`, `S3` dopo l'esecuzione.
- Nessun seme scartato dopo averne visto l'esito.
- Nessuna riesecuzione di un seme «andato male».
- `A2` non puo' essere usato per rileggere `A1`.
- Gli artefatti della campagna sigillata non vengono toccati: verifica per
  impronta prima e dopo, con arresto bloccante se cambiano.
- `.venv313`; Python 3.14 vietato; `enforce_runtime_guard(strict=True)`.
- Una sola esecuzione. Un fallimento tecnico si riporta come tale.

## 8. Provenienza richiesta

`runtime_guard`, `execution_mode = SCIENTIFIC`, impronta del motore
(`4a2181b8dbeda428`), impronta della copia usata per `A2`, impronta di questa
preregistrazione, elenco dei venti semi in chiaro, conteggi `support_exact` per
sistema e per livello senza aggregazione, e i conteggi dei nulli non riassunti.
