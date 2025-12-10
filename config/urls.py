from django.contrib import admin
from django.urls import path, include
from gate import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("check/", views.check, name="check"),
    path("toggle/", views.toggle_status, name="toggle"),

    path("inside/", views.current_inside, name="inside"),
    path("outside/", views.current_outside, name="outside"),
    path("logs/", views.logs, name="logs"),

    path("students/add/", views.add_student, name="add_student"),
    path("students/<int:pk>/edit/", views.edit_student, name="edit_student"),
    path("students/import/", views.import_students_csv, name="import_students_csv"),

    path("accounts/", include("django.contrib.auth.urls")),
]

# ✅ DEV-ONLY: serve media (and optionally static) via runserver
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # optional; runserver already serves static if 'staticfiles' app is installed:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
