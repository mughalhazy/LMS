from __future__ import annotations
import pytest
from app.service import EnterpriseControlService


def _svc() -> EnterpriseControlService:
    return EnterpriseControlService()


def test_default_compliance_baseline():
    svc = _svc()
    status, body = svc.get_compliance("t1")
    assert status == 200
    assert body["compliance_level"] == "baseline"


def test_update_compliance_level():
    svc = _svc()
    status, body = svc.update_compliance("t1", {"compliance_level": "strict"})
    assert status == 200
    assert body["compliance_level"] == "strict"


def test_invalid_compliance_level():
    svc = _svc()
    status, _ = svc.update_compliance("t1", {"compliance_level": "ultra"})
    assert status == 400


def test_register_integration():
    svc = _svc()
    status, body = svc.register_integration({"tenant_id": "t1", "integration_type": "hris",
                                               "name": "Workday", "config": {"url": "https://workday.example"}})
    assert status == 201
    assert body["integration_type"] == "hris"


def test_invalid_integration_type():
    svc = _svc()
    status, _ = svc.register_integration({"tenant_id": "t1", "integration_type": "unknown"})
    assert status == 400


def test_list_integrations():
    svc = _svc()
    svc.register_integration({"tenant_id": "t1", "integration_type": "sso", "name": "SAML"})
    svc.register_integration({"tenant_id": "t1", "integration_type": "hris", "name": "SAP"})
    _, body = svc.list_integrations("t1")
    assert body["count"] == 2


def test_set_rbac_policy():
    svc = _svc()
    status, body = svc.set_rbac_policy({"tenant_id": "t1", "role": "admin",
                                         "permissions": ["read", "write", "delete"]})
    assert status == 201
    assert "delete" in body["permissions"]


def test_get_rbac_policies():
    svc = _svc()
    svc.set_rbac_policy({"tenant_id": "t1", "role": "admin", "permissions": ["read"]})
    svc.set_rbac_policy({"tenant_id": "t1", "role": "instructor", "permissions": ["read"]})
    _, body = svc.get_rbac_policies("t1")
    assert len(body["policies"]) == 2
