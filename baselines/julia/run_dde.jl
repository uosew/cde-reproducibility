# Seconda implementazione indipendente sulle stesse matrici di disegno.
# Prereg: PREREGISTRAZIONE_BASELINE_INDIPENDENTE_JULIA_2026-09-07.md
#
# Via di chiamata scoperta da `probe_api.jl` (non indovinata): l'algoritmo di
# DataDrivenSparse si applica direttamente a (X, Y) con X = A' e Y = b', e
# restituisce (coefficienti, iperparametri, indici). Sulla prova a soluzione nota
# recupera il supporto esatto.
# Nessun verdetto qui: la scelta della soglia e il punteggio stanno nello scorer Python.
using Pkg
Pkg.activate(@__DIR__)
using DataDrivenSparse, NPZ, JSON3, LinearAlgebra

const EXPORT = joinpath(@__DIR__, "..", "cde_feature_export_out")
const SOGLIE = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]   # la stessa griglia concessa a PySINDy

function risolvi(A::Matrix{Float64}, b::Vector{Float64})
    X = permutedims(A)                      # feature x campioni
    Y = permutedims(reshape(b, :, 1))       # 1 x campioni
    fuori = Dict{String,Any}()
    for lam in SOGLIE
        try
            res = STLSQ(lam)(X, Y)
            c = vec(Matrix{Float64}(res[1]))
            supporto = findall(x -> abs(x) > 1e-14, c) .- 1     # base 0, per Python
            resid = norm(A * c - b) / max(norm(b), 1e-300)
            fuori[string(lam)] = Dict("coef" => c, "supporto" => supporto,
                                      "resid_rel" => resid, "errore" => false)
        catch e
            fuori[string(lam)] = Dict("errore" => true,
                                      "messaggio" => first(sprint(showerror, e), 200))
        end
    end
    return fuori
end

function main()
    man = JSON3.read(read(joinpath(EXPORT, "manifest.json"), String))
    risultati = Dict{String,Any}()
    n = 0
    for (cid, _) in man["celle"]
        d = npzread(joinpath(EXPORT, string(cid) * ".npz"))
        A = Matrix{Float64}(d["A"]); b = Vector{Float64}(vec(d["b"]))
        risultati[string(cid)] = risolvi(A, b)
        n += 1
        if n % 10 == 0
            println("  $n celle"); flush(stdout)
        end
    end
    open(joinpath(@__DIR__, "risultati_dde.json"), "w") do io
        JSON3.pretty(io, Dict("run" => "DataDrivenSparse_STLSQ", "soglie" => SOGLIE,
                              "julia" => string(VERSION),
                              "via" => "STLSQ(lambda)(X, Y), scoperta da probe_api.jl",
                              "celle" => risultati))
    end
    println("scritte $n celle in risultati_dde.json")
end

main()
