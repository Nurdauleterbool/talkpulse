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


from datetime import timedelta

from django.test import Client
from django.utils import timezone

from talks.models import REACTIONS, Reaction


@pytest.fixture
def owner_client(talk):
    c = Client()
    c.force_login(talk.owner)
    return c


@pytest.mark.django_db
def test_new_session_is_waiting(talk):
    assert talk.state == "waiting"


@pytest.mark.django_db
def test_start_talk_goes_live(owner_client, talk):
    owner_client.post(reverse("start_talk", args=[talk.pk]))
    talk.refresh_from_db()
    assert talk.state == "live"
    assert talk.started_at is not None


@pytest.mark.django_db
def test_start_twice_keeps_first_time(owner_client, talk):
    owner_client.post(reverse("start_talk", args=[talk.pk]))
    talk.refresh_from_db()
    first = talk.started_at
    owner_client.post(reverse("start_talk", args=[talk.pk]))
    talk.refresh_from_db()
    assert talk.started_at == first


@pytest.mark.django_db
def test_end_talk_opens_form(owner_client, talk):
    owner_client.post(reverse("start_talk", args=[talk.pk]))
    owner_client.post(reverse("end_talk", args=[talk.pk]))
    talk.refresh_from_db()
    assert talk.state == "form_open"
    assert talk.ended_at is not None


@pytest.mark.django_db
def test_end_before_start_does_nothing(owner_client, talk):
    owner_client.post(reverse("end_talk", args=[talk.pk]))
    talk.refresh_from_db()
    assert talk.state == "waiting"
    assert talk.ended_at is None


@pytest.mark.django_db
def test_form_stays_open_ten_minutes_then_closes(talk):
    talk.started_at = timezone.now() - timedelta(minutes=30)
    talk.ended_at = timezone.now() - timedelta(minutes=9)
    assert talk.state == "form_open"
    talk.ended_at = timezone.now() - timedelta(minutes=11)
    assert talk.state == "closed"


@pytest.mark.django_db
def test_other_presenter_cannot_start(client, django_user_model, talk):
    other = django_user_model.objects.create_user("boris", password=PASSWORD)
    client.force_login(other)
    r = client.post(reverse("start_talk", args=[talk.pk]))
    assert r.status_code == 404
    talk.refresh_from_db()
    assert talk.state == "waiting"


@pytest.mark.django_db
def test_start_requires_login(client, talk):
    r = client.post(reverse("start_talk", args=[talk.pk]))
    assert r.status_code == 302
    assert "/accounts/login/" in r["Location"]


@pytest.mark.django_db
def test_start_with_get_is_not_allowed(owner_client, talk):
    assert owner_client.get(reverse("start_talk", args=[talk.pk])).status_code == 405


def go_live(talk, seconds_ago=0):
    talk.started_at = timezone.now() - timedelta(seconds=seconds_ago)
    talk.save()


def joined_client(talk, name="Boris"):
    c = Client()
    c.post(reverse("join", args=[talk.join_code]), {"name": name})
    return c


@pytest.mark.django_db
def test_reaction_is_stored_with_offset(talk):
    go_live(talk, seconds_ago=125)
    c = joined_client(talk)
    r = c.post(reverse("react", args=[talk.join_code]), {"kind": "unclear"})
    assert r.status_code == 200
    reaction = Reaction.objects.get()
    assert reaction.kind == "unclear"
    assert 125 <= reaction.offset_seconds <= 127


@pytest.mark.django_db
def test_reaction_before_start_is_rejected(talk):
    c = joined_client(talk)
    r = c.post(reverse("react", args=[talk.join_code]), {"kind": "unclear"})
    assert r.status_code == 409
    assert Reaction.objects.count() == 0


@pytest.mark.django_db
def test_reaction_after_end_is_rejected(talk):
    go_live(talk, seconds_ago=60)
    talk.ended_at = timezone.now()
    talk.save()
    c = joined_client(talk)
    r = c.post(reverse("react", args=[talk.join_code]), {"kind": "unclear"})
    assert r.status_code == 409
    assert Reaction.objects.count() == 0


@pytest.mark.django_db
def test_unknown_reaction_is_rejected(talk):
    go_live(talk)
    c = joined_client(talk)
    r = c.post(reverse("react", args=[talk.join_code]), {"kind": "boo"})
    assert r.status_code == 400
    assert Reaction.objects.count() == 0


@pytest.mark.django_db
def test_reaction_without_joining_is_rejected(client, talk):
    go_live(talk)
    r = client.post(reverse("react", args=[talk.join_code]), {"kind": "unclear"})
    assert r.status_code == 403
    assert Reaction.objects.count() == 0


@pytest.mark.django_db
def test_listener_sees_five_reaction_buttons(talk):
    go_live(talk)
    c = joined_client(talk)
    html = c.get(reverse("listen", args=[talk.join_code])).content.decode()
    assert len(REACTIONS) == 5
    for _, label in REACTIONS:
        assert label in html


def tap_unclear(talk, how_many):
    for i in range(how_many):
        listener = Listener.objects.create(session=talk, name=f"L{i}")
        Reaction.objects.create(session=talk, listener=listener, kind="unclear", offset_seconds=5)


@pytest.mark.django_db
def test_signal_turns_red_when_many_tap_unclear(owner_client, talk):
    go_live(talk)
    tap_unclear(talk, 2)
    url = reverse("signal", args=[talk.pk])
    assert owner_client.get(url).json()["level"] == "green"
    tap_unclear(talk, 1)
    assert owner_client.get(url).json()["level"] == "red"


@pytest.mark.django_db
def test_signal_ignores_old_taps(owner_client, talk):
    go_live(talk, seconds_ago=300)
    tap_unclear(talk, 3)
    Reaction.objects.update(created_at=timezone.now() - timedelta(seconds=120))
    assert owner_client.get(reverse("signal", args=[talk.pk])).json()["level"] == "green"


@pytest.mark.django_db
def test_signal_shows_no_numbers(owner_client, talk):
    go_live(talk)
    tap_unclear(talk, 3)
    data = owner_client.get(reverse("signal", args=[talk.pk])).json()
    assert set(data.keys()) == {"level", "state"}


@pytest.mark.django_db
def test_signal_only_for_owner(client, django_user_model, talk):
    other = django_user_model.objects.create_user("boris", password=PASSWORD)
    client.force_login(other)
    assert client.get(reverse("signal", args=[talk.pk])).status_code == 404


@pytest.mark.django_db
def test_live_session_page_has_signal_bar(owner_client, talk):
    go_live(talk)
    html = owner_client.get(reverse("session_detail", args=[talk.pk])).content.decode()
    assert 'id="signal"' in html
    assert "End talk" in html
