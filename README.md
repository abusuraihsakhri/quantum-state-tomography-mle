# Quantum State Tomography MLE

Single-qubit quantum state reconstruction from Pauli X/Y/Z measurement counts by **constrained maximum likelihood estimation (MLE)**. The repository also retains its pre-existing general-purpose audit-agent CLI/API for compatibility.

## Tomography application

The static application lives in [web/](web/). Start a local static HTTP server:

~~~bash
python -m http.server 8001 --directory web
~~~

Open http://localhost:8001/. Enter non-negative integer +1/−1 Pauli outcome counts, then select **Reconstruct state**. The browser displays the Bloch vector, a complex 2×2 density matrix, purity, and log likelihood. Export results to JSON or CSV. Calculations happen entirely in the browser; no server, upload, or CDN is required.

The estimator maximizes independent binomial likelihoods under the physicality constraint ||r||₂ ≤ 1. The density matrix is ρ = (I + r·σ)/2, with unit trace and non-negative eigenvalues. Unmeasured Bloch components default to zero (a minimum-norm MLE selection). The calculation assumes independent ideal projective measurements, without readout-error correction. **Only single-qubit states are supported.** Uncertainty intervals, multi-qubit reconstruction, Bayesian regularization, and compressed sensing are not implemented.

### Python API and CLI

~~~bash
python -m pip install -e .
python -m quantum_tomography.mle --x 90 10 --y 50 50 --z 50 50
~~~

~~~python
from quantum_tomography.mle import estimate_pauli_mle

result = estimate_pauli_mle({"x": [90, 10], "y": [50, 50], "z": [50, 50]})
print(result["bloch_vector"])  # {'x': 0.8, 'y': 0.0, 'z': 0.0}
print(result["density_matrix"])  # each entry is [real, imaginary]
~~~

The CLI prints JSON. The Python and browser estimators are implemented in [quantum_tomography/mle.py](quantum_tomography/mle.py) and [web/tomography.mjs](web/tomography.mjs).

## Legacy auditing CLI and API

The pre-existing agents/ subsystem uses generic metric thresholds and worker alerts. **It does not perform density-matrix tomography.** It is retained for compatibility with existing workflows.

~~~bash
python -m pip install -e ".[dev]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The REST API supports /health, /metrics, /api/audit, /api/chat, and /api/audit/logs. Audit-log retrieval is disabled unless AUDIT_READ_TOKEN is configured; when enabled it requires an Authorization: Bearer token header. Supply a separate, random AUDIT_SECRET_KEY (minimum 16 characters) for HMAC signatures. The audit chain is **in-memory**, not durably stored across restarts or anchored externally. The PHI pattern guard is heuristic, not a complete de-identification mechanism.

For Docker:

~~~bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
~~~

Docker Compose binds the API to 127.0.0.1:8000 by default. Do not commit secrets or submit real patient identifiers. Any historical production use of the prior hard-coded Compose key requires key rotation.

## Development and tests

~~~bash
python -m pip install -e ".[dev]"
pytest -q
python -m pip wheel --no-deps . -w /tmp/wheels
node --test web/tomography.test.mjs
~~~

CI runs Python 3.10, 3.11, and 3.12 and JavaScript unit tests. The browser UI uses ES modules and requires a modern browser. GitHub Pages deployment is configured in .github/workflows/pages.yml; Pages availability depends on repository settings.

## Structure

- **quantum_tomography/mle.py** — genuine single-qubit constrained MLE
- **web/** — standalone browser interface and JavaScript estimator
- **agents/** and **quantum_tomography/agents.py** — pre-existing threshold-based audit workflows
- **enrichment.py** — legacy threshold evaluators, not actual regularized MLE or compressed sensing
- **tests/** — regression and security tests
- **.github/workflows/** — CI and deployment

**Privacy:** Browser calculations run locally in memory with no upload, telemetry, or persistent storage. Backend deployments have separate security and logging requirements.

**License:** [MIT](LICENSE).
