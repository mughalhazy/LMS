from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_hierarchy_and_uniqueness_rules() -> None:
    org = client.post(
        "/organizations",
        json={"tenant_id": "t1", "name": "Acme", "code": "ACME"},
    ).json()

    dep1 = client.post(
        "/departments",
        json={"organization_id": org["organization_id"], "name": "Engineering", "code": "ENG"},
    )
    assert dep1.status_code == 201

    duplicate_dep = client.post(
        "/departments",
        json={"organization_id": org["organization_id"], "name": "Engineering", "code": "ENG2"},
    )
    assert duplicate_dep.status_code == 409

    dep = dep1.json()
    team1 = client.post(
        "/teams",
        json={"department_id": dep["department_id"], "name": "Platform", "code": "PLAT"},
    )
    assert team1.status_code == 201

    duplicate_team = client.post(
        "/teams",
        json={"department_id": dep["department_id"], "name": "Platform", "code": "PLAT2"},
    )
    assert duplicate_team.status_code == 409

    tree = client.get(f"/organizations/{org['organization_id']}/hierarchy")
    assert tree.status_code == 200
    data = tree.json()
    assert len(data["departments"]) == 1
    assert len(data["teams"]) == 1


def test_lifecycle_and_reparent_audit() -> None:
    org = client.post(
        "/organizations",
        json={"tenant_id": "t2", "name": "Beta", "code": "BETA"},
    ).json()

    dep = client.post(
        "/departments",
        json={"organization_id": org["organization_id"], "name": "Sales", "code": "SALES"},
    ).json()

    team = client.post(
        "/teams",
        json={"department_id": dep["department_id"], "name": "Enterprise", "code": "ENT"},
    ).json()

    no_cascade = client.post(f"/organizations/{org['organization_id']}/deactivate", json={"cascade": False})
    assert no_cascade.status_code == 400

    cascade = client.post(f"/organizations/{org['organization_id']}/deactivate", json={"cascade": True})
    assert cascade.status_code == 200
    assert cascade.json()["status"] == "inactive"

    other_dep = client.post(
        "/departments",
        json={"organization_id": org["organization_id"], "name": "Ops", "code": "OPS"},
    )
    assert other_dep.status_code == 400

    patch = client.patch(
        f"/teams/{team['team_id']}",
        headers={"x-actor-user-id": "u-123"},
        json={"department_id": dep["department_id"], "code": "ENT-NEW"},
    )
    assert patch.status_code == 200

    audit = client.get("/audit/reparent-events")
    assert audit.status_code == 200
    assert isinstance(audit.json(), list)
