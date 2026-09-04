# Claim card — CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0

- **burgers** [FD4+RK45]: r_GT=4.55e-05; support=['u_xx', 'uu_x'] gate(sigma=0)=True; sigma*=None; FDR=0.00
- **fisher_kpp** [FD4+RK45]: r_GT=4.75e-05; support=['u', 'u^2', 'u_xx'] gate(sigma=0)=True; sigma*=None; FDR=0.00

Dati generati con method-of-lines FD4 + scipy RK45: catena numerica indipendente dall'ETDRK4 spettrale di V8. Protocollo v1.1 congelato, importato da V8 senza ridefinizioni.

Claim boundary: come V8; rimossa l'obiezione 'stesso generatore' per Burgers e Fisher-KPP.