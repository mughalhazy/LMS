from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


RBAC_ROLE_CREATED = "rbac.role.created.v1"
RBAC_ROLE_UPDATED = "rbac.role.updated.v1"
RBAC_ASSIGNMENT_CREATED = "rbac.assignment.created.v1"
RBAC_ASSIGNMENT_REVOKED = "rbac.assignment.revoked.v1"
RBAC_POLICY_RULE_CHANGED = "rbac.policy_rule.changed.v1"


@dataclass
class InMemoryEventPublisher:
    published: list[dict] = field(default_factory=list)

    def publish(self, event_type: str, tenant_id: str, payload: dict) -> None:
        self.published.append(
            {
                "event_type": event_type,
                "tenant_id": tenant_id,
                "payload": payload,
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        )


@dataclass
class InMemoryObservabilityHook:
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
        key = metric if not tags else f"{metric}|{','.join(f'{k}:{v}' for k, v in sorted(tags.items()))}"
        self.counters[key] = self.counters.get(key, 0) + 1
