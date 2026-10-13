"""
Tests for input validation, security enforcement, and error handling.
"""
import math
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a test audit key before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-unit-tests-2026")

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload


class TestInputValidation:
    """Tests for SystemTaskPayload input validation."""

    def test_valid_payload(self):
        p = SystemTaskPayload(
            task_id="TASK-001",
            target_identifier="KEY-01",
            primary_metric=25.0,
            secondary_metric=10.0,
        )
        assert p.task_id == "TASK-001"
        assert p.primary_metric == 25.0

    def test_empty_task_id_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="", target_identifier="KEY-01", primary_metric=10.0)

    def test_whitespace_only_task_id_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="   ", target_identifier="KEY-01", primary_metric=10.0)

    def test_nan_metric_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("nan"))

    def test_infinity_metric_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("inf"))

    def test_negative_infinity_metric_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", secondary_metric=float("-inf"))

    def test_identifier_stripped(self):
        p = SystemTaskPayload(task_id="  TASK-01  ", target_identifier="  KEY-01  ", primary_metric=10.0)
        assert p.task_id == "TASK-01"
        assert p.target_identifier == "KEY-01"

    def test_long_task_id_rejected(self):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="X" * 300, target_identifier="K1", primary_metric=10.0)


class TestPHIGuard:
    """Tests for PHI outbound guard."""

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")

    def test_mrn_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-994827 blood culture")

    def test_ssn_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_email_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Contact user@example.com for results")

    def test_redaction(self):
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 test")
        assert "MRN-12345678" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted


class TestAuditTrailSecurity:
    """Tests for audit trail security enforcement."""

    def test_missing_secret_key_raises(self):
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(EnvironmentError):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_short_secret_key_rejected(self):
        with pytest.raises(ValueError):
            AuditTrail(secret_key="short")

    def test_valid_key_works(self):
        trail = AuditTrail(secret_key="this-is-a-valid-secret-key")
        assert trail.secret_key == b"this-is-a-valid-secret-key"

    def test_audit_chain_integrity(self):
        trail = AuditTrail(secret_key="test-key-for-integrity-check")
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_2", {"data": "value2"})
        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 2


class TestCLIBatchErrorHandling:
    """Tests for CLI batch processing error handling."""

    def test_missing_input_file(self):
        from cli import main
        result = main(["batch", "-i", "nonexistent_file.csv"])
        assert result == 1

    def test_empty_csv(self):
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric\n")
            temp_path = f.name
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as out_f:
                out_path = out_f.name
            result = main(["batch", "-i", temp_path, "-o", out_path])
            assert result == 0
        finally:
            os.unlink(temp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_csv_with_invalid_rows(self):
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric\n")
            f.write("TASK-001,KEY-01,25.0,10.0\n")
            f.write("TASK-002,KEY-02,invalid,5.0\n")  # Invalid metric
            temp_path = f.name
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as out_f:
                out_path = out_f.name
            result = main(["batch", "-i", temp_path, "-o", out_path])
            assert result == 0
        finally:
            os.unlink(temp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)



class TestAuditTamperDetection:
    def test_modified_signed_fields_rejected(self):
        trail = AuditTrail(secret_key="test-audit-verification-key")
        trail.log("actor1", "tier1", "EVENT_1", {"key": "value"})
        trail.log("actor2", "tier1", "EVENT_2", {"key": "value"})
        assert trail.verify_integrity() is True
        trail.logs[0]["actor"] = "impostor"
        assert trail.verify_integrity() is False

    def test_relinked_hash_chain_rejected(self):
        trail = AuditTrail(secret_key="test-audit-verification-key")
        trail.log("actor", "tier", "EVENT_1", {"key": "v1"})
        trail.log("actor", "tier", "EVENT_2", {"key": "v2"})
        trail.logs[0]["current_hash"] = "0" * 64
        trail.logs[1]["prev_hash"] = "0" * 64
        assert trail.verify_integrity() is False

    def test_exposed_trail_is_copy(self):
        trail = AuditTrail(secret_key="test-audit-verification-key")
        trail.log("actor", "tier", "EVENT", {"key": "value"})
        public_log = trail.get_trail()
        public_log[0]["actor"] = "attacker"
        assert trail.verify_integrity() is True


class TestAuditLogAccess:
    def test_disabled_by_default(self, monkeypatch):
        from fastapi.testclient import TestClient
        from agents.api import app
        monkeypatch.delenv("AUDIT_READ_TOKEN", raising=False)
        client = TestClient(app)
        assert client.get("/api/audit/logs").status_code == 403

    def test_requires_bearer_token(self, monkeypatch):
        from fastapi.testclient import TestClient
        from agents.api import app
        monkeypatch.setenv("AUDIT_READ_TOKEN", "test-audit-read-token")
        client = TestClient(app)
        assert client.get("/api/audit/logs").status_code == 401
        assert client.get("/api/audit/logs", headers={
            "Authorization": "Bearer test-audit-read-token"
        }).status_code == 200
