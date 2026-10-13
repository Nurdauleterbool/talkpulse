from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import segno
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import JoinForm, SessionForm
from .models import REACTIONS, Listener, Reaction, Session


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
