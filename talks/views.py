from django.db.models import Avg
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import segno
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FeedbackForm, JoinForm, SessionForm
from .models import REACTIONS, Feedback, Listener, Reaction, Session


def home(request):
    sessions = Session.objects.none()
    if request.user.is_authenticated:
        sessions = request.user.talk_sessions.order_by("-created_at")
    return render(request, "home.html", {"sessions": sessions})


def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("session_create")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def session_create(request):
    form = SessionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.owner = request.user
        session.save()
        return redirect("session_detail", pk=session.pk)
    return render(request, "talks/session_form.html", {"form": form})


@login_required
def session_detail(request, pk):
    session = get_object_or_404(Session, pk=pk, owner=request.user)
    join_url = request.build_absolute_uri(f"/join/{session.join_code}/")
    qr_svg = segno.make(join_url).svg_inline(scale=6)
    return render(
        request,
        "talks/session_detail.html",
        {"session": session, "join_url": join_url, "qr_svg": qr_svg},
    )


def join(request, code):
    session = get_object_or_404(Session, join_code=code)
    form = JoinForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        anonymous = form.cleaned_data["anonymous"]
        listener = Listener.objects.create(
            session=session,
            name="" if anonymous else form.cleaned_data["name"].strip(),
            is_anonymous=anonymous,
        )
        request.session[f"listener_{session.pk}"] = listener.pk
        return redirect("listen", code=session.join_code)
    return render(request, "talks/join.html", {"session": session, "form": form})


def listen(request, code):
    session = get_object_or_404(Session, join_code=code)
    listener_id = request.session.get(f"listener_{session.pk}")
    listener = None
    if listener_id:
        listener = Listener.objects.filter(pk=listener_id, session=session).first()
    if listener is None:
        return redirect("join", code=code)
    return render(request, "talks/listen.html", {"session": session, "listener": listener, "reactions": REACTIONS})


SIGNAL_WINDOW = timedelta(seconds=60)
SIGNAL_THRESHOLD = 3


def signal_level(session):
    if session.state != "live":
        return "idle"
    since = timezone.now() - SIGNAL_WINDOW
    n = (
        session.reactions.filter(kind="unclear", created_at__gte=since)
        .values("listener")
        .distinct()
        .count()
    )
    return "red" if n >= SIGNAL_THRESHOLD else "green"


@login_required
@require_POST
def start_talk(request, pk):
    session = get_object_or_404(Session, pk=pk, owner=request.user)
    if session.state == "waiting":
        session.started_at = timezone.now()
        session.save()
    return redirect("session_detail", pk=pk)


@login_required
@require_POST
def end_talk(request, pk):
    session = get_object_or_404(Session, pk=pk, owner=request.user)
    if session.state == "live":
        session.ended_at = timezone.now()
        session.save()
    return redirect("session_detail", pk=pk)


@login_required
def signal(request, pk):
    session = get_object_or_404(Session, pk=pk, owner=request.user)
    return JsonResponse({"level": signal_level(session), "state": session.state})


@require_POST
def react(request, code):
    session = get_object_or_404(Session, join_code=code)
    listener_id = request.session.get(f"listener_{session.pk}")
    listener = None
    if listener_id:
        listener = Listener.objects.filter(pk=listener_id, session=session).first()
    if listener is None:
        return JsonResponse({"error": "join first"}, status=403)
    kind = request.POST.get("kind")
    if kind not in dict(REACTIONS):
        return JsonResponse({"error": "unknown reaction"}, status=400)
    if session.state != "live":
        return JsonResponse({"error": "talk is not live"}, status=409)
    offset = int((timezone.now() - session.started_at).total_seconds())
    Reaction.objects.create(session=session, listener=listener, kind=kind, offset_seconds=offset)
    return JsonResponse({"ok": True, "offset_seconds": offset})


def _listener(request, session):
    listener_id = request.session.get(f"listener_{session.pk}")
    if not listener_id:
        return None
    return Listener.objects.filter(pk=listener_id, session=session).first()


def feedback(request, code):
    session = get_object_or_404(Session, join_code=code)
    listener = _listener(request, session)
    if listener is None:
        return redirect("join", code=code)
    if session.state != "form_open":
        return render(
            request,
            "talks/message.html",
            {"session": session, "message": "The feedback form is not open now."},
            status=403,
        )
    if Feedback.objects.filter(listener=listener).exists():
        return render(
            request,
            "talks/message.html",
            {"session": session, "message": "Thank you! You have already sent your feedback."},
        )
    form = FeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.session = session
        obj.listener = listener
        obj.save()
        return redirect("feedback", code=code)
    return render(request, "talks/feedback.html", {"session": session, "form": form})


@login_required
def results(request, pk):
    session = get_object_or_404(Session, pk=pk, owner=request.user)
    if session.ended_at is None:
        return redirect("session_detail", pk=pk)
    kinds = [k for k, _ in REACTIONS]
    data = list(session.reactions.values_list("offset_seconds", "kind"))
    length = int((session.ended_at - session.started_at).total_seconds() // 60) + 1
    last = max([o // 60 for o, _ in data], default=0)
    grid = [[0] * len(kinds) for _ in range(max(length, last + 1))]
    for offset, kind in data:
        grid[offset // 60][kinds.index(kind)] += 1
    rows = [{"minute": i, "cells": cells} for i, cells in enumerate(grid)]
    avg = session.feedbacks.aggregate(
        content=Avg("content"), delivery=Avg("delivery"), slides=Avg("slides"), answers=Avg("answers")
    )
    ratings = [
        ("Content", avg["content"]),
        ("Delivery", avg["delivery"]),
        ("Slides", avg["slides"]),
        ("Answers to questions", avg["answers"]),
    ]
    comments = [
        {"author": f.listener.display_name, "worked_well": f.worked_well, "to_improve": f.to_improve}
        for f in session.feedbacks.select_related("listener")
    ]
    return render(
        request,
        "talks/results.html",
        {
            "session": session,
            "rows": rows,
            "labels": [label for _, label in REACTIONS],
            "ratings": ratings,
            "comments": comments,
        },
    )
