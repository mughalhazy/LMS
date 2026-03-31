from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from shared.validation import validate_service_dependency_contracts


class GoodPayments:
    def process_checkout_payment(self) -> None:  # pragma: no cover - signature not part of runtime contract check
        return None


class GoodSor:
    def list_student_profiles(self) -> None:
        return None

    def post_invoice_to_ledger(self) -> None:
        return None

    def post_payment_to_ledger(self) -> None:
        return None

    def run_qc_autofix(self) -> None:
        return None


class GoodNotifications:
    def send_notification(self) -> None:
        return None


class BrokenNotifications:
    pass


def test_validation_contracts_pass_for_expected_service_interfaces() -> None:
    results = validate_service_dependency_contracts(
        payment_orchestrator=GoodPayments(),
        sor_service=GoodSor(),
        notification_orchestrator=GoodNotifications(),
    )

    assert results["commerce_to_payments"].valid is True
    assert results["academy_to_system_of_record"].valid is True
    assert results["workflow_to_notifications"].valid is True


def test_validation_contracts_report_missing_methods_for_broken_dependencies() -> None:
    results = validate_service_dependency_contracts(
        payment_orchestrator=GoodPayments(),
        sor_service=GoodSor(),
        notification_orchestrator=BrokenNotifications(),
    )

    assert results["workflow_to_notifications"].valid is False
    assert results["workflow_to_notifications"].missing_methods == ("send_notification",)
