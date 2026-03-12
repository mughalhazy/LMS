from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_roles_seeded():
    response = client.get('/roles')
    assert response.status_code == 200
    names = {r['role_name'] for r in response.json()}
    assert 'Tenant Admin' in names
    assert 'Learner' in names


def test_assignment_and_authorize_allow():
    create = client.post(
        '/assignments',
        json={
            'subject_type': 'user',
            'subject_id': 'u-1',
            'role_id': 'tenant-admin',
            'scope_type': 'tenant',
            'scope_id': 't-1',
            'assigned_by': 'admin-user',
            'assignment_model': 'direct',
        },
    )
    assert create.status_code == 201

    decision = client.post(
        '/authorize',
        json={
            'principal_id': 'u-1',
            'principal_type': 'user',
            'permission': 'tenant.settings.manage',
            'scope_type': 'tenant',
            'scope_id': 't-1',
        },
    )
    assert decision.status_code == 200
    assert decision.json()['decision'] == 'ALLOW'


def test_protected_endpoint_middleware_denies_without_assignment():
    response = client.get(
        '/audit-log',
        headers={
            'X-Principal-Id': 'u-2',
            'X-Principal-Type': 'user',
            'X-Scope-Type': 'tenant',
            'X-Scope-Id': 't-1',
        },
    )
    assert response.status_code == 403
