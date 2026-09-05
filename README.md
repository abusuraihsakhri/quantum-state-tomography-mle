# Quantum State Tomography MLE

> **Domain:** Quantum Information & Post-Quantum Cryptography  
> **Standards:** Quantum State Tomography Standard, NIST FIPS 203/204/205

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Quantum State Tomography MLE is a Python-based analytical platform for quantum state evaluation, protocol conformance checking, and density matrix analysis. It provides a multi-agent architecture with specialized workers for invariant QC, safety escalation, and protocol conformance evaluation.

---

## Architecture

The project consists of two main subsystems:

### Core Agents (`agents/`)
- **Models** (`agents/models.py`): Pydantic v2 schemas for task payloads, alerts, and consensus dossiers
- **Workers** (`agents/workers.py`): Specialized evaluation agents:
  - `InvariantQCWorker`: Primary metric boundary validation
  - `SafetyEscalationWorker`: Critical safety interlock detection
  - `ProtocolConformanceWorker`: Specification conformance checking
- **Supervisor** (`agents/supervisor.py`): Multi-agent orchestrator with consensus logic
- **Security** (`agents/base.py`): PHI guard, HMAC-SHA256 audit trail, security exceptions
- **API** (`agents/api.py`): FastAPI REST server endpoints

### Quantum Tomography (`quantum_tomography/`)
- **Engine** (`quantum_tomography/engine.py`): Core domain logic for parameter evaluation
- **Agents** (`quantum_tomography/agents.py`): Specialized sub-agents for quantum state analysis
- **CLI** (`quantum_tomography/cli.py`): Command-line interface

### Enrichment (`enrichment.py`)
- Maximum Likelihood Estimation with Regularized Optimization
- Compressed Sensing Quantum State Tomography
- Implementation and testing engines for domain-specific evaluations

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/quantum-state-tomography-mle.git
cd quantum-state-tomography-mle

# Install dependencies
pip install -e .

# For development (includes testing tools)
pip install pytest fastapi uvicorn pydantic

# Set the required audit secret key
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AUDIT_SECRET_KEY` | Yes | Cryptographic key for HMAC-SHA256 audit trail (min 16 chars) |
| `MODEL_PROVIDER` | No | LLM provider: `mock`, `ollama`, `claude`, `openai` (default: `mock`) |

---

## Usage

### CLI Commands

#### Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### System Chat
```bash
python cli.py chat "What is the system status?"
```

#### Verify Audit Trail
```bash
python cli.py verify-audit
```

#### Start API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query supervisory chat |
| `/api/audit/logs` | GET | Retrieve audit trail |

### Run Simulation
```bash
python simulator.py 1000
```

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=quantum_tomography

# Run specific test module
pytest tests/test_quantum_state_tomography_mle.py -v
```

---

## Security Features

- **PHI Outbound Guard**: AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail**: Cryptographically chained, tamper-evident logging
- **Input Validation**: Bounds checking on all metrics, finite-value enforcement
- **Audit Key Enforcement**: Requires `AUDIT_SECRET_KEY` environment variable (no hardcoded defaults)

---

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t quantum-state-tomography-mle .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") quantum-state-tomography-mle
```

---

## Project Structure

```
quantum-state-tomography-mle/
├── agents/                  # Core agent system
│   ├── __init__.py
│   ├── api.py              # FastAPI endpoints
│   ├── base.py             # Security, audit, PHI guard
│   ├── models.py           # Pydantic schemas
│   ├── supervisor.py       # Multi-agent orchestrator
│   ├── workers.py          # Specialized evaluation agents
│   ├── llm_factory.py      # LLM provider factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics
│   └── streamer.py         # WebSocket telemetry
├── quantum_tomography/      # Quantum tomography subsystem
│   ├── __init__.py
│   ├── agents.py           # Quantum state agents
│   ├── cli.py              # CLI interface
│   ├── engine.py           # Domain logic engine
│   ├── models.py           # Data models
│   └── server.py           # API server factory
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_enrichment.py
│   ├── test_quantum_state_tomography_mle.py
│   └── test_quantum_tomography.py
├── web/                     # Operations console
│   └── index.html
├── cli.py                   # Main CLI entry point
├── simulator.py             # Load testing simulator
├── enrichment.py            # MLE enrichment features
├── pyproject.toml           # Project configuration
├── Dockerfile               # Container definition
├── docker-compose.yml       # Docker Compose config
├── sample.csv               # Sample input data
├── sample_payload.json      # Sample API payload
└── benchmark_dataset.json   # Benchmark test cases
```
