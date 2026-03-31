import json

from app.pricing import list_plans, resolve_plan


def test_plan_resolution_from_runtime_payload(monkeypatch) -> None:
    monkeypatch.setenv(
        "SUBSCRIPTION_PRICING_PLANS_JSON",
        json.dumps(
            {
                "enterprise": {
                    "price": "499.00",
                    "billing_cycle": "yearly",
                    "included_features": ["dedicated_isolation", "priority_support"],
                }
            }
        ),
    )

    plans = list_plans()
    assert "enterprise" in plans
    assert resolve_plan("enterprise") == plans["enterprise"]
    assert plans["enterprise"].billing_cycle.value == "yearly"
