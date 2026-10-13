"""Analytic and physical constraints for single-qubit MLE."""
import math
import pytest
from quantum_tomography.mle import estimate_pauli_mle, main


def test_mixed_state_reconstruction():
    result = estimate_pauli_mle({"x": (90, 10), "y": (50, 50), "z": (50, 50)})
    assert result["bloch_vector"] == pytest.approx({"x": 0.8, "y": 0, "z": 0})
    assert result["purity"] == pytest.approx(0.82)
    assert result["shots"] == 300
    assert result["density_matrix"][0][1] == pytest.approx([0.4, 0])


def test_pure_z_up_and_unmeasured_components():
    result = estimate_pauli_mle({"z": (100, 0)})
    assert result["bloch_vector"] == pytest.approx({"x": 0, "y": 0, "z": 1})
    assert result["density_matrix"][1][1] == pytest.approx([0, 0])
    assert result["purity"] == pytest.approx(1)


def test_unequal_shots_constrained_mle():
    result = estimate_pauli_mle({"x": (90, 10), "y": (18, 2), "z": (18, 2)})
    r = result["bloch_vector"]
    assert math.sqrt(sum(v*v for v in r.values())) == pytest.approx(1, abs=1e-10)
    assert r["x"] > r["y"] > 0
    assert r["y"] == pytest.approx(r["z"])
    assert result["purity"] <= 1 + 1e-12
    assert sum(v*v for v in r.values()) <= 1 + 1e-12


@pytest.mark.parametrize("counts", [
    {}, {"x": (0, 0)}, {"w": (1, 0)}, {"x": (-1, 2)},
    {"x": (1.0, 2)}, {"x": (True, 2)}, {"x": (2,)},
    {"x": (1, float("nan"))},
])
def test_bad_counts_rejected(counts):
    with pytest.raises(ValueError):
        estimate_pauli_mle(counts)


def test_cli_prints_json(capsys):
    assert main(["--x", "9", "1", "--z", "5", "5"]) == 0
    assert '"bloch_vector"' in capsys.readouterr().out
