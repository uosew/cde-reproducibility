from _common import load
def test_canary_runs_and_is_quiet_on_this_environment():
    G = load("numpy_guard.py"); r = G.elision_mutation_canary()
    assert r["any"] is False, f"numpy temporary elision mutates operands here: {r}"
def test_envelope_policy_fails_closed():
    RG = load("runtime_guard_bootstrap.py")
    assert RG.evaluate_run_validity({}) == RG.EVIDENCE_INCOMPLETE
    assert RG.evaluate_run_validity({"runtime_guard": {"status": "FAIL"}}) == RG.RUN_INVALID_ENVIRONMENT
    assert RG.evaluate_run_validity({"runtime_guard": {"status": "PASS", "input_mutation_detected": True}}) == RG.RUN_INVALID_ENVIRONMENT
    assert RG.is_promotable({"runtime_guard": {"status": "PASS"}})
