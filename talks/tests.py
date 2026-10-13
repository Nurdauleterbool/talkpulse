from django.urls import reverse


def test_home_returns_200(client):
    assert client.get(reverse("home")).status_code == 200
