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
]
