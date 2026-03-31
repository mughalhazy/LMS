from __future__ import annotations

from dataclasses import dataclass
from typing import Any

"""Validation contracts anchored to architecture docs.

Source of truth:
- docs/architecture/payment_provider_adapter_interface_contract.md
- docs/architecture/communication_adapter_interface_contract.md
- docs/architecture/ARCH_02_microservice_boundary_map.md
"""


@dataclass(frozen=True)
class ServiceInteractionContract:
    """Runtime contract for a dependency between two service boundaries."""

    interaction_id: str
    consumer: str
    provider: str
    required_methods: tuple[str, ...]


@dataclass(frozen=True)
class ContractValidationResult:
    interaction_id: str
    consumer: str
    provider: str
    valid: bool
    missing_methods: tuple[str, ...]


SERVICE_INTERACTION_CONTRACTS: tuple[ServiceInteractionContract, ...] = (
    ServiceInteractionContract(
        interaction_id="commerce_to_payments",
        consumer="commerce",
        provider="payments_orchestration",
        required_methods=("process_checkout_payment",),
    ),
    ServiceInteractionContract(
        interaction_id="academy_to_system_of_record",
        consumer="academy_ops",
        provider="system_of_record",
        required_methods=(
            "list_student_profiles",
            "post_invoice_to_ledger",
            "post_payment_to_ledger",
            "run_qc_autofix",
        ),
    ),
    ServiceInteractionContract(
        interaction_id="workflow_to_notifications",
        consumer="workflow_engine",
        provider="notification_orchestrator",
        required_methods=("send_notification",),
    ),
)


def validate_contract(contract: ServiceInteractionContract, provider_instance: Any) -> ContractValidationResult:
    missing = tuple(method for method in contract.required_methods if not callable(getattr(provider_instance, method, None)))
    return ContractValidationResult(
        interaction_id=contract.interaction_id,
        consumer=contract.consumer,
        provider=contract.provider,
        valid=len(missing) == 0,
        missing_methods=missing,
    )


def validate_service_dependency_contracts(
    *,
    payment_orchestrator: Any,
    sor_service: Any,
    notification_orchestrator: Any,
) -> dict[str, ContractValidationResult]:
    provider_by_interaction = {
        "commerce_to_payments": payment_orchestrator,
        "academy_to_system_of_record": sor_service,
        "workflow_to_notifications": notification_orchestrator,
    }

    return {
        contract.interaction_id: validate_contract(contract, provider_by_interaction[contract.interaction_id])
        for contract in SERVICE_INTERACTION_CONTRACTS
    }


def summarize_contract_validation(results: dict[str, ContractValidationResult]) -> dict[str, bool]:
    return {interaction_id: result.valid for interaction_id, result in results.items()}
