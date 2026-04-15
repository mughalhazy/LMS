from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/academy-ops/service.py"
_spec = importlib.util.spec_from_file_location("academy_ops_branch_module", MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load academy-ops module")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

AcademyOpsService = _module.AcademyOpsService
Batch = _module.Batch
Branch = _module.Branch
BranchStatus = _module.BranchStatus


def test_branch_lifecycle_and_operational_summary() -> None:
    service = AcademyOpsService()
    branch = service.create_branch(
        Branch(
            tenant_id="tenant_branch",
            branch_id="branch_1",
            name="Downtown",
            code="DT-01",
            location="NYC",
            manager_id="mgr_1",
            capacity=2,
            metadata={"franchise_type": "owned"},
        )
    )
    assert branch.code == "DT-01"

    updated = service.update_branch(
        tenant_id="tenant_branch",
        branch_id="branch_1",
        manager_id="mgr_2",
        metadata={"franchise_type": "partner"},
    )
    assert updated.manager_id == "mgr_2"

    service.create_batch(
        Batch(
            tenant_id="tenant_branch",
            branch_id="branch_1",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Python",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            learner_ids=("l1", "l2"),
        )
    )

    summary = service.list_branch_operational_summary(tenant_id="tenant_branch", branch_id="branch_1")
    assert summary["active_batch_count"] == 1
    assert summary["learner_count"] == 2
    assert summary["economics_ready"]["owner_economics"] is True


def test_assign_batch_to_inactive_branch_rejected() -> None:
    service = AcademyOpsService()
    service.create_branch(
        Branch(
            tenant_id="tenant_branch2",
            branch_id="branch_2",
            name="Uptown",
            code="UP-01",
            location="LA",
            capacity=1,
            status=BranchStatus.INACTIVE,
        )
    )

    service._batches[("tenant_branch2", "batch_2")] = Batch(
        tenant_id="tenant_branch2",
        branch_id="branch_2",
        batch_id="batch_2",
        academy_id="academy_2",
        title="Math",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 1),
        learner_ids=(),
    )

    try:
        service.assign_batch_to_branch(tenant_id="tenant_branch2", branch_id="branch_2", batch_id="batch_2")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "inactive" in str(exc)
