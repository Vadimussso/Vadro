import pytest


def test_read_ads(client):
    response = client.get("/ads")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.parametrize("header_tf, status",
                         [(True, 200),
                          (False, 401)])
def test_ad_add(client, header_tf, status, make_user_token, ad_data):
    headers = {}
    if header_tf:
        headers = {"Authorization": f"Bearer {make_user_token}"}

    response = client.post("/ads", json=ad_data, headers=headers)

    assert response.status_code == status


@pytest.mark.parametrize("ad_exist, user_admin, status",
                         [(False, True, 404),
                          (True, False, 403),
                          (True, True, 200)]
                         )
def test_moderate(client, ad_exist, user_admin, status, make_user_token, ad_data, make_admin_token):
    ad_id = 9999
    headers_user = {"Authorization": f"Bearer {make_user_token}"}

    if ad_exist:
        created_ad = client.post('/ads', json=ad_data, headers=headers_user)
        ad_id = created_ad.json()['id']

    headers_admin = headers_user
    if user_admin:
        headers_admin = {"Authorization": f"Bearer {make_admin_token}"}

    response = client.post(f"/ads/{ad_id}/moderate", headers=headers_admin)

    assert response.status_code == status


@pytest.mark.parametrize("ad_exist, status",
                         [(True, 200),
                          (False, 404)])
def test_read_ad(client, ad_data, make_user_token, make_admin_token, ad_exist, status):

    ad_id = 9999
    if ad_exist:
        headers_user = {"Authorization": f"Bearer {make_user_token}"}

        created_ad = client.post('/ads', json=ad_data, headers=headers_user)
        ad_id = created_ad.json()['id']

        headers_admin = {"Authorization": f"Bearer {make_admin_token}"}
        response_moderation = client.post(f"/ads/{ad_id}/moderate", headers=headers_admin)
        assert response_moderation.status_code == 200

    response = client.get(f"/ads/{ad_id}")

    assert response.status_code == status

