import json

import pytest


@pytest.fixture(autouse=True)
def configure_subscription_pricing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SUBSCRIPTION_PRICING_PLANS_JSON",
        json.dumps(
            {
                "free": {
                    "price": "0",
                    "billing_cycle": "monthly",
                    "included_features": ["catalog_basic"],
                },
                "pro": {
                    "price": "39.99",
                    "billing_cycle": "monthly",
                    "included_features": ["analytics_basic"],
                },
                "enterprise": {
                    "price": "299.99",
                    "billing_cycle": "monthly",
                    "included_features": ["analytics_advanced", "dedicated_isolation"],
                },
            }
        ),
    )
