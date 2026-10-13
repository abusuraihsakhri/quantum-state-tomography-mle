"""Single-qubit maximum-likelihood tomography from Pauli X/Y/Z counts.

For each measured Pauli axis i, counts (n_plus, n_minus) have
P(+|r_i)=(1+r_i)/2. Maximize their joint binomial likelihood subject to
||r||_2 <= 1, ensuring a positive-semidefinite, trace-one density matrix.
"""
import argparse
import json
import math
from typing import Mapping, Sequence

_AXES = ("x", "y", "z")
_EPS = 1e-15


def _axis_given_penalty(n_plus: int, n_minus: int, penalty: float) -> float:
    """Solve the monotone stationarity equation for a single Bloch component."""
    lo, hi = -1.0 + _EPS, 1.0 - _EPS
    for _ in range(64):
        mid = (lo + hi) / 2.0
        derivative = (
            (n_minus / (1.0 - mid) if n_minus else 0.0)
            - (n_plus / (1.0 + mid) if n_plus else 0.0)
            + 2.0 * penalty * mid
        )
        if derivative < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def estimate_pauli_mle(counts: Mapping[str, Sequence[int]]) -> dict:
    """Return the physical single-qubit MLE for X/Y/Z outcome counts.

    "counts" maps axis names (x, y, z) to [plus, minus] nonnegative
    integers. Missing axes are allowed; at least one shot is required.
    Unmeasured Bloch components are set to zero (minimum-norm selection).
    This is an MLE, not a Bayesian uncertainty estimate.
    """
    if not isinstance(counts, Mapping) or set(counts) - set(_AXES):
        raise ValueError("counts must map only x, y, z to [plus, minus]")
    validated = {}
    for axis in _AXES:
        pair = counts.get(axis, (0, 0))
        if (
            not isinstance(pair, (list, tuple)) or len(pair) != 2
            or any(type(v) is not int or v < 0 for v in pair)
        ):
            raise ValueError(f"{axis} counts must be two nonnegative integers")
        validated[axis] = tuple(pair)
    if not sum(sum(pair) for pair in validated.values()):
        raise ValueError("at least one measurement shot is required")

    empirical = [
        (plus - minus) / (plus + minus) if plus + minus else 0.0
        for plus, minus in validated.values()
    ]
    length_squared = sum(r * r for r in empirical)
    if length_squared <= 1.0:
        bloch = empirical
    else:
        # Convex negative log-likelihood, unit-Bloch-ball constraint.
        # KKT multiplier is found by bisection; no numerical packages needed.
        def coordinates(penalty):
            return [
                _axis_given_penalty(plus, minus, penalty)
                if plus + minus else 0.0
                for plus, minus in validated.values()
            ]

        low, high = 0.0, 1.0
        while sum(r * r for r in coordinates(high)) > 1.0:
            high *= 2.0
        for _ in range(65):
            middle = (low + high) / 2.0
            if sum(r * r for r in coordinates(middle)) > 1.0:
                low = middle
            else:
                high = middle
        bloch = coordinates(high)
        # Floating-point safeguard for a strictly physical state.
        norm = math.sqrt(sum(r * r for r in bloch))
        if norm > 1.0:
            bloch = [r / norm for r in bloch]

    x, y, z = bloch
    log_likelihood = 0.0
    for axis, r in zip(_AXES, bloch):
        plus, minus = validated[axis]
        if plus:
            log_likelihood += plus * math.log((1.0 + r) / 2.0)
        if minus:
            log_likelihood += minus * math.log((1.0 - r) / 2.0)
    return {
        "bloch_vector": dict(zip(_AXES, bloch)),
        "density_matrix": [
            [[(1.0 + z) / 2.0, 0.0], [x / 2.0, -y / 2.0]],
            [[x / 2.0, y / 2.0], [(1.0 - z) / 2.0, 0.0]],
        ],
        "purity": (1.0 + sum(r * r for r in bloch)) / 2.0,
        "log_likelihood": log_likelihood,
        "shots": sum(sum(pair) for pair in validated.values()),
        "counts": {axis: list(pair) for axis, pair in validated.items()},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Single-qubit Pauli-count maximum-likelihood tomography")
    for axis in _AXES:
        parser.add_argument(f"--{axis}", nargs=2, type=int, metavar=("PLUS", "MINUS"), default=(0, 0))
    args = parser.parse_args(argv)
    try:
        result = estimate_pauli_mle({axis: getattr(args, axis) for axis in _AXES})
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
