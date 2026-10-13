import pytest
from django.urls import reverse

from talks.models import Session

PASSWORD = "S3cret-pass-42"


def test_home_returns_200(client):
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_signup_creates_user_and_logs_in(client, django_user_model):
    r = client.post(
        reverse("signup"),
        {"username": "anna", "password1": PASSWORD, "password2": PASSWORD},
    )
    assert r.status_code == 302
    assert django_user_model.objects.filter(username="anna").exists()
    assert client.get(reverse("session_create")).status_code == 200


@pytest.mark.django_db
def test_login_works(client, django_user_model):
    django_user_model.objects.create_user("anna", password=PASSWORD)
    r = client.post(reverse("login"), {"username": "anna", "password": PASSWORD})
    assert r.status_code == 302
    assert client.get(reverse("session_create")).status_code == 200


@pytest.mark.django_db
def test_login_with_wrong_password_shows_form_again(client, django_user_model):
    django_user_model.objects.create_user("anna", password=PASSWORD)
    r = client.post(reverse("login"), {"username": "anna", "password": "wrong"})
    assert r.status_code == 200


@pytest.mark.django_db
def test_create_requires_login(client):
    r = client.get(reverse("session_create"))
    assert r.status_code == 302
    assert "/accounts/login/" in r["Location"]


@pytest.mark.django_db
def test_presenter_creates_session(client, django_user_model):
    user = django_user_model.objects.create_user("anna", password=PASSWORD)
    client.force_login(user)
    r = client.post(reverse("session_create"), {"title": "My defense"})
    session = Session.objects.get(title="My defense")
    assert session.owner == user
    assert r.status_code == 302
    assert r["Location"] == reverse("session_detail", args=[session.pk])


@pytest.mark.django_db
def test_empty_title_is_rejected(client, django_user_model):
    user = django_user_model.objects.create_user("anna", password=PASSWORD)
    client.force_login(user)
    r = client.post(reverse("session_create"), {"title": ""})
    assert r.status_code == 200
    assert Session.objects.count() == 0


@pytest.mark.django_db
def test_session_page_shows_join_link_and_qr(client, django_user_model):
    user = django_user_model.objects.create_user("anna", password=PASSWORD)
    client.force_login(user)
    session = Session.objects.create(owner=user, title="My defense")
    r = client.get(reverse("session_detail", args=[session.pk]))
    html = r.content.decode()
    assert r.status_code == 200
    assert f"/join/{session.join_code}/" in html
    assert "<svg" in html


@pytest.mark.django_db
def test_other_presenter_cannot_open_session(client, django_user_model):
    owner = django_user_model.objects.create_user("anna", password=PASSWORD)
    other = django_user_model.objects.create_user("boris", password=PASSWORD)
    session = Session.objects.create(owner=owner, title="Private")
    client.force_login(other)
    r = client.get(reverse("session_detail", args=[session.pk]))
    assert r.status_code == 404


from talks.models import Listener


@pytest.fixture
def talk(django_user_model):
    user = django_user_model.objects.create_user("anna", password=PASSWORD)
    return Session.objects.create(owner=user, title="My defense")


@pytest.mark.django_db
def test_join_page_opens_without_login(client, talk):
    r = client.get(reverse("join", args=[talk.join_code]))
    assert r.status_code == 200
    html = r.content.decode()
    assert "My defense" in html
    assert 'name="viewport"' in html


@pytest.mark.django_db
def test_unknown_join_code_is_404(client):
    assert client.get(reverse("join", args=["nope"])).status_code == 404


@pytest.mark.django_db
def test_join_with_name_keeps_the_name(client, talk):
    client.post(reverse("join", args=[talk.join_code]), {"name": "Boris"})
    listener = Listener.objects.get()
    assert listener.name == "Boris"
    assert listener.is_anonymous is False
    assert listener.display_name == "Boris"


@pytest.mark.django_db
def test_join_anonymous_is_marked_anonymous(client, talk):
    client.post(reverse("join", args=[talk.join_code]), {"name": "Boris", "anonymous": "on"})
    listener = Listener.objects.get()
    assert listener.is_anonymous is True
    assert listener.display_name == "Anonymous"


@pytest.mark.django_db
def test_join_without_name_or_anonymous_shows_error(client, talk):
    r = client.post(reverse("join", args=[talk.join_code]), {"name": "  "})
    assert r.status_code == 200
    assert "Enter a name or tick anonymous." in r.content.decode()
    assert Listener.objects.count() == 0


@pytest.mark.django_db
def test_after_join_listener_goes_to_session_screen(client, talk):
    r = client.post(reverse("join", args=[talk.join_code]), {"name": "Boris"})
    assert r.status_code == 302
    assert r["Location"] == reverse("listen", args=[talk.join_code])
    page = client.get(r["Location"])
    assert page.status_code == 200
    assert "Boris" in page.content.decode()


@pytest.mark.django_db
def test_session_screen_without_joining_redirects_to_join(client, talk):
    r = client.get(reverse("listen", args=[talk.join_code]))
    assert r.status_code == 302
    assert r["Location"] == reverse("join", args=[talk.join_code])


@pytest.mark.django_db
def test_listener_without_name_displays_as_anonymous(talk):
    assert Listener(session=talk, name="").display_name == "Anonymous"
