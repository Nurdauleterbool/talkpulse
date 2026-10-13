import segno
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SessionForm
from .models import Session


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
