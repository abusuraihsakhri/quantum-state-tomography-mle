"""
Pytest configuration for quantum-state-tomography-mle test suite.
Sets required environment variables before any test collection.
"""
import os

# Set a deterministic test audit key before any agent module is imported
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-unit-tests-2026")
