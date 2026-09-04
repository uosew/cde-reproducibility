"""Every scorer's gates must bite: broken gates must change the verdict."""
import pytest
from _common import load
@pytest.mark.parametrize("module,expected_min", [("CDE_V13_BLIND_UNBLINDING_V0.py", 8), ("CDE_BLIND4_SCORER_V0.py", 5), ("CDE_RISOLUZIONE_ANALYZER_V0.py", 5)])
def test_all_mutations_bite(module, expected_min):
    res = load(module).mutation_test()
    assert len(res) >= expected_min and all(res.values()), {k: v for k, v in res.items() if not v}
