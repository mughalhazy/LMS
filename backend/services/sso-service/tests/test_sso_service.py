from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_supported_providers():
    response = client.get('/providers')
    assert response.status_code == 200
    payload = response.json()['providers_supported']
    assert {'saml', 'oauth2', 'oidc'} <= set(payload.keys())


def test_initiate_saml_flow():
    response = client.post(
        '/sso/initiate',
        json={
            'tenant_id': 'tenant-a',
            'provider': 'saml',
            'config': {
                'idp_entity_id': 'idp.example',
                'idp_sso_url': 'https://idp.example/sso',
                'idp_x509_certificate': 'cert',
                'sp_entity_id': 'lms-sp',
                'acs_url': 'https://lms.example/sso/acs',
            },
        },
    )
    assert response.status_code == 200
    assert response.json()['flow'] == 'sp_initiated_or_idp_initiated_saml'


def test_oidc_callback_requires_id_token():
    response = client.post(
        '/sso/callback',
        json={
            'tenant_id': 'tenant-a',
            'provider': 'oidc',
            'payload': {'code': 'abc', 'sub': 'u-1'},
        },
    )
    assert response.status_code == 400
