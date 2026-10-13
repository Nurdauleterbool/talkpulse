from django.contrib import admin
from django.urls import include, path

from talks import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sessions/new/", views.session_create, name="session_create"),
    path("sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path("join/<str:code>/", views.join, name="join"),
    path("join/<str:code>/live/", views.listen, name="listen"),
    path("join/<str:code>/react/", views.react, name="react"),
    path("sessions/<int:pk>/start/", views.start_talk, name="start_talk"),
    path("sessions/<int:pk>/end/", views.end_talk, name="end_talk"),
    path("sessions/<int:pk>/signal/", views.signal, name="signal"),
]
