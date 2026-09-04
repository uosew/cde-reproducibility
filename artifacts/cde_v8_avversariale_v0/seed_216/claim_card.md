# Claim card — CDE_PDE_DISCOVERY_V8

- **allen_cahn**: r_GT=2.01e-04; sigma=0 -> support=['u', 'u^3', 'u_xx'] gate=True; sigma*=0.1; FDR nulli=0.00
- **fisher_kpp**: r_GT=8.91e-05; sigma=0 -> support=['u', 'u^2', 'u_xx'] gate=True; sigma*=None; FDR nulli=0.00
- **burgers**: r_GT=4.55e-05; sigma=0 -> support=['u_xx', 'uu_x'] gate=True; sigma*=None; FDR nulli=0.00
- **kdv**: r_GT=5.31e-05; sigma=0 -> support=['u_xxx', 'uu_x'] gate=True; sigma*=None; FDR nulli=0.00

Protocollo preregistrato (stability selection B=100, freq>=0.8, BIC su griglia soglie fissa); libreria condivisa a 7 termini; KdV mai usata per la messa a punto dell'operatore (transfer).

Claim boundary: PDE 1D periodiche lisce, solver spettrale, rumore gaussiano di misura; nessuna claim su dati sperimentali.