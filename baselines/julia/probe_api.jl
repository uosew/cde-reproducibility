# Sonda: scopre come si chiama STLSQ di DataDrivenSparse su una coppia (A, b) nota,
# senza indovinare. Stampa quale via funziona e il supporto recuperato.
using Pkg; Pkg.activate(@__DIR__)
using DataDrivenDiffEq, DataDrivenSparse, LinearAlgebra, Random

Random.seed!(0)
A = randn(400, 7); c = zeros(7); c[2] = 0.7; c[5] = -0.3
b = A * c
println("vero: supporto [2, 5], coef [0.7, -0.3]")

println("\n--- via 1: DirectDataDrivenProblem + Basis + solve ---")
try
    prob = DirectDataDrivenProblem(permutedims(A), permutedims(reshape(b, :, 1)))
    @variables u[1:7]
    basis = Basis(collect(u), collect(u))
    res = solve(prob, basis, STLSQ(0.1))
    println("  OK  parametri: ", DataDrivenDiffEq.get_parameter_values(res))
    println("  risultato: ", res)
catch e
    println("  FALLITA: ", sprint(showerror, e)[1:min(end, 300)])
end

println("\n--- via 2: l'algoritmo chiamato direttamente su (X, Y) ---")
for (nome, f) in [("opt(X, Y)", (o, X, Y) -> o(X, Y)),
                  ("solve(o, X, Y)", (o, X, Y) -> solve(o, X, Y)),
                  ("init+fit", (o, X, Y) -> begin
                       cache = DataDrivenSparse.init_cache(o, X, Y); DataDrivenSparse.fit!(cache); cache
                   end)]
    try
        out = f(STLSQ(0.1), permutedims(A), permutedims(reshape(b, :, 1)))
        println("  $nome  OK -> ", typeof(out), "  ", out)
    catch e
        println("  $nome  fallita: ", sprint(showerror, e)[1:min(end, 160)])
    end
end

println("\n--- metodi esportati da DataDrivenSparse ---")
println(filter(n -> occursin("STLSQ", string(n)) || occursin("sparse", lowercase(string(n))), names(DataDrivenSparse)))
println("\n--- metodi di STLSQ ---")
println(methods(STLSQ))
