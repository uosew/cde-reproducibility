# Preregistrazione V6-bis — la statistica |c_drop|/max|c| separa o no?

Data: 2026-08-01. Stato: **PREREGISTRATO PRIMA DELL'ESECUZIONE.**

Documento **separato**, non un emendamento alla preregistrazione V12. Il
verdetto `V6_RESPINTA` registrato lì il 2026-08-01 **resta in vigore e non
viene riscritto**: la griglia era dichiarata prima del run, e allargarla dopo
aver visto i numeri è esattamente ciò che la preregistrazione vieta.

Qui si riapre la **domanda scientifica**, con uno strumento diverso e un
documento nuovo, come deve essere.

---

## 1. Perché il run precedente non ha risposto

Per costruzione **κ = 0 coincide esattamente con la v2.1**: la condizione
`|c_drop|/max|c| ≥ κ` è sempre vera, il gate torna a «nessuna alternativa entro
2×», e il punteggio è 16 corrette / 0 false.

Al minimo della griglia, κ = 0,005, si osservavano già 24 corrette, 8 recuperi
e 2 claim false. L'intera transizione fra v2.1 e V1 sta quindi **sotto il
minimo della griglia**, in un intervallo mai campionato. Il run ha misurato
dieci punti tutti dallo stesso lato della soglia.

Errore da non ripetere: una griglia di iperparametri va scelta in modo da
**racchiudere il comportamento di riferimento ai suoi estremi**.

---

## 2. L'errore più profondo: una griglia dove esiste una forma chiusa

Correggere il range sarebbe una toppa. Il difetto vero è che **lo sweep era lo
strumento sbagliato in partenza**.

Il gate di V1 rifiuta un caso se esiste un'alternativa che è insieme `entro_2x`
e ha rapporto ≥ κ. Definiamo, per ogni caso:

```
κ_crit(caso) = max { |c_drop| / max|c|  :  alternative con entro_2x }
             = −∞  se non esiste alcuna alternativa entro 2x
```

Allora, esattamente e senza approssimazione:

> il caso supera il gate di identificabilità **se e solo se κ > κ_crit(caso)**.

Le funzioni «numero di recuperi» e «numero di claim false» in funzione di κ
sono quindi **funzioni a gradini completamente determinate dai valori
κ_crit**. Non serve campionare: basta calcolarli.

---

## 3. La domanda, e la sua risposta in forma chiusa

Siano:

- **T** = casi rappresentabili con **supporto esatto** rifiutati dalla v2.1 al
  gate di identificabilità (i recuperabili);
- **F** = casi rappresentabili con **supporto errato** (i 10 che, se promossi,
  diventano claim false).

Un κ produce zero claim false se e solo se `κ ≤ min{ κ_crit(c) : c ∈ F }`.
Chiamiamo quel valore **κ_max_sicuro**.

Il numero di recuperi ottenibili a rischio nullo è quindi, esattamente:

```
recuperi_sicuri = #{ c ∈ T  :  κ_crit(c) < κ_max_sicuro }
```

**La statistica separa se e solo se `recuperi_sicuri > 0`.**

Non c'è nulla da cercare: è un confronto fra due minimi.

---

## 4. Criteri congelati

**Successo — V6BIS_AMMESSA_ALLA_V12.** `recuperi_sicuri > 0` e nessuna
regressione sulle 16 claim già corrette. Il κ proposto per la V12 è la media
geometrica fra il massimo κ_crit dei casi recuperati e κ_max_sicuro, per stare
lontano da entrambi i bordi.

**Rigetto — V6BIS_RESPINTA.** `recuperi_sicuri = 0`, cioè
`min κ_crit(T) ≥ min κ_crit(F)`. Conclusione preregistrata: *la statistica
|c_drop|/max|c| non separa i recuperi veri dalle promozioni errate; il gate di
identificabilità non è rilassabile lungo questo asse; il 40% di recall è il
tetto di questa ladder.* In quel caso **non si cerca un terzo asse dentro
questa campagna**: si dichiara l'esito e ci si ferma.

---

## 5. Controlli di correttezza dello strumento, dichiarati prima

Lo script deve riprodurre, **come predizioni derivate dai soli κ_crit**, due
risultati già noti. Se una delle due fallisce, lo strumento è rotto e il
risultato è nullo qualunque cosa dica.

| controllo | predizione |
|---|---|
| κ → 0⁺ | 16 claim corrette, 0 false (la v2.1) |
| κ = 0,05 | 24 corrette, 8 recuperi, 2 false (V1, già osservato) |
| κ = 0,10 | 3 claim false (già osservato nello sweep) |

Il secondo e il terzo sono verifiche contro dati già raccolti, non nuove
misure.

---

## 6. Limite dichiarato prima di guardare

Un κ scelto così è un iperparametro **adattato sul development set**. Zero
claim false su 10 casi a supporto errato dà, per la regola del tre, un limite
superiore approssimativo del **30%** — garanzia molto debole.

Se V6-bis passa, **non ha prodotto evidenza**: ha guadagnato il diritto di
essere testata sulla V12 cieca con ≥150 casi da rifiutare. La distinzione è la
stessa già congelata per V6 e non cambia qui.

Inoltre `recuperi_sicuri` è per costruzione il **massimo teorico** ottenibile
su questo development set: è il numero più ottimistico possibile, non una
stima di ciò che accadrà sulla V12.

---

## 7. Ambiente e provenienza

- `.venv313`, `enforce_runtime_guard(strict=True)`.
- Riusa la cache degli stati a monte `cde_v12_dev_out/stati_upstream_cache.json`,
  identica a quella usata da V6: nessuna ricostruzione, nessuna possibilità che
  gli stati differiscano fra i due run.
- Output: `cde_v12_dev_out/v6bis_kappa_critico.json`.
- La V12 **non** viene generata né aperta.

---

## 8. Ledger

| data | voce |
|---|---|
| 2026-08-01 | V6-bis preregistrata. Nessun calcolo di κ_crit ancora eseguito. |

---

## 9. Ledger — 2026-08-01, esito

Tutti e tre i controlli di correttezza §5 **superati**: κ→0 dà 16 corrette e 0
false, κ=0,05 dà 24 e 2, κ=0,10 dà 3 false. La forma chiusa riproduce
esattamente i run precedenti; lo strumento è valido.

### I valori di κ_crit

| gruppo | caso | κ_crit |
|---|---|---|
| **T** recuperabile | case_027 | **1,587·10⁻⁵** |
| **F** → falsa | **case_019** | **1,777·10⁻⁵** ← κ_max_sicuro |
| T | case_029 | 1,976·10⁻⁵ |
| T | case_021 | 2,022·10⁻⁵ |
| T | case_028 | 3,244·10⁻⁵ |
| T | case_022 | 3,781·10⁻⁵ |
| T | case_024 | 4,689·10⁻⁵ |
| T | case_023 | 4,751·10⁻⁵ |
| T | case_025 | 5,641·10⁻⁵ |
| F | case_050 | 1,059·10⁻³ |
| F | case_002 | 8,553·10⁻² |
| F | case_053, case_058 | 1,000 |

### Verdetto formale, e perché non basta

`recuperi_sicuri = 1 > 0`, quindi il criterio congelato in §4 dà
**V6BIS_AMMESSA_ALLA_V12**. Il verdetto resta agli atti.

**Ma il criterio che avevo congelato era troppo debole**, e va detto invece di
lasciar passare un successo formale per un risultato:

1. **Recupera un solo caso.** Recall 17/40 = 42,5%. La preregistrazione V12 §1
   fissa il target a **≥ 60%**. V6-bis, nel suo caso migliore teorico, **non
   può soddisfare la V12**. Eseguire la campagna cieca con questo κ sarebbe un
   fallimento predeterminato.
2. **Il margine è dell'12%.** κ = 1,679·10⁻⁵ sta fra 1,587·10⁻⁵ e 1,777·10⁻⁵.
   Una diversa realizzazione di rumore o un seme diverso lo ribaltano.
3. **Le popolazioni si sovrappongono quasi del tutto.** Sette degli otto
   recuperabili hanno κ_crit *sopra* il peggior caso falso. La risposta alla
   domanda scientifica di §3 — «la statistica separa?» — è sostanzialmente
   **no**, anche se la lettera del criterio dice sì.

**Conclusione sostanziale: la statistica |c_drop|/max|c| non separa in modo
utilizzabile.** Il 40% di recall resta il tetto di questa ladder. Il verdetto
formale AMMESSA non va usato per giustificare la generazione della V12.

### Un'osservazione, e una tentazione da non seguire

Quattro dei cinque casi falsi si separano benissimo: κ_crit da 1,06·10⁻³ a
1,000, cioè da due a cinque ordini di grandezza sopra i recuperabili. **L'intero
fallimento dipende da un singolo caso, case_019**, il cui κ_crit cade dentro la
distribuzione dei veri. Senza di esso κ_max_sicuro sarebbe 1,06·10⁻³ e tutti e
otto verrebbero recuperati, centrando il 60%.

È esattamente qui che sarebbe facile barare: andare a studiare case_019, capire
cosa lo rende anomalo, e costruire una regola che lo escluda. Sarebbe
**adattamento al development set nella sua forma più pura** — una regola
derivata da un singolo caso di cui conosciamo già la verità.

**Non è stato fatto e non va fatto in questa campagna.** L'osservazione resta
qui come indizio per una campagna futura, con una preregistrazione propria e su
casi mai visti.
