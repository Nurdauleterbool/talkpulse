import secrets

from django.conf import settings
from django.db import models


def make_code():
    return secrets.token_urlsafe(6)


class Session(models.Model):
    WAITING = "waiting"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="talk_sessions"
    )
    title = models.CharField(max_length=200)
    join_code = models.CharField(max_length=20, unique=True, default=make_code)
    state = models.CharField(max_length=20, default=WAITING)
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
