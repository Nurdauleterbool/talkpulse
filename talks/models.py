import secrets

from django.conf import settings
from django.db import models


def make_code():
    return secrets.token_urlsafe(6)


class Session(models.Model):

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="talk_sessions"
    )
    title = models.CharField(max_length=200)
    join_code = models.CharField(max_length=20, unique=True, default=make_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Listener(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="listeners")
    name = models.CharField(max_length=100, blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        if self.is_anonymous or not self.name:
            return "Anonymous"
        return self.name


from datetime import timedelta

from django.utils import timezone

FORM_WINDOW = timedelta(minutes=10)

REACTIONS = [
    ("unclear", "Unclear"),
    ("too_fast", "Too fast"),
    ("too_slow", "Too slow"),
    ("great_point", "Great point"),
    ("question", "I have a question"),
]


def _state(self):
    if self.started_at is None:
        return "waiting"
    if self.ended_at is None:
        return "live"
    if timezone.now() < self.ended_at + FORM_WINDOW:
        return "form_open"
    return "closed"


Session.state = property(_state)
Session.add_to_class("started_at", models.DateTimeField(null=True, blank=True))
Session.add_to_class("ended_at", models.DateTimeField(null=True, blank=True))


class Reaction(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="reactions")
    listener = models.ForeignKey(Listener, on_delete=models.CASCADE, related_name="reactions")
    kind = models.CharField(max_length=20, choices=REACTIONS)
    offset_seconds = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
