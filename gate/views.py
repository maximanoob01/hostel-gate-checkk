# gate/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth.decorators import permission_required, login_required

from .models import Student, MovementLog
from .forms import StudentForm, CSVUploadForm
import csv, io


# -------------------- Dashboard (role-aware) --------------------

@login_required
def dashboard(request):
    inside_count  = Student.objects.filter(is_inside=True).count()
    outside_count = Student.objects.filter(is_inside=False).count()
    return render(request, "gate/dashboard.html", {
        "inside_count": inside_count,
        "outside_count": outside_count,
    })


# -------------------- Public / Open pages --------------------

def home(request):
    inside_count = Student.objects.filter(is_inside=True).count()
    outside_count = Student.objects.filter(is_inside=False).count()
    return render(
        request,
        "gate/home.html",
        {"inside_count": inside_count, "outside_count": outside_count},
    )


@require_http_methods(["GET", "POST"])
def check(request):
    """
    Behaviors:
    - GET with ?enr=... -> show single student card (exact enrollment)
    - POST with enrollment_number or name:
        * exact match -> show single student card
        * else -> show results list of partial matches (enrollment or name)
    """
    context = {"student": None, "searched": False, "results": []}

    # Deep link: /check/?enr=XXXX
    enr_param = (request.GET.get("enr") or "").strip()
    if enr_param:
        context["searched"] = True
        try:
            student = Student.objects.get(enrollment_number__iexact=enr_param)
            context["student"] = student
        except Student.DoesNotExist:
            messages.error(request, f"No student found for enrollment {enr_param}.")
        return render(request, "gate/check.html", context)

    # POST search
    if request.method == "POST":
        q = (request.POST.get("enrollment_number") or "").strip()
        context["searched"] = True
        if not q:
            messages.error(request, "Please enter an enrollment number or name.")
            return render(request, "gate/check.html", context)

        # Try exact enrollment first
        try:
            student = Student.objects.get(enrollment_number__iexact=q)
            context["student"] = student
            return render(request, "gate/check.html", context)
        except Student.DoesNotExist:
            pass

        # Partial search on enrollment OR name
        results = (
            Student.objects.filter(
                Q(enrollment_number__icontains=q) | Q(full_name__icontains=q)
            )
            .order_by("enrollment_number")[:50]
        )
        if results:
            context["results"] = results
        else:
            messages.info(request, f'No matches found for “{q}”.')

    return render(request, "gate/check.html", context)


# -------------------- Lists (Wardens/Admin only) --------------------

@permission_required("gate.view_student", login_url="login")
def current_inside(request):
    students = Student.objects.filter(is_inside=True)
    return render(request, "gate/list.html", {"title": "Currently Inside", "students": students})


@permission_required("gate.view_student", login_url="login")
def current_outside(request):
    students = Student.objects.filter(is_inside=False)
    return render(request, "gate/list.html", {"title": "Currently Outside", "students": students})


# -------------------- Logs (Guards/Wardens/Admin) --------------------

@permission_required("gate.view_movementlog", login_url="login")
def logs(request):
    logs_qs = MovementLog.objects.select_related("student", "recorded_by").order_by("-timestamp")[:500]
    return render(request, "gate/logs.html", {"logs": logs_qs})


# -------------------- Toggle (Guards/Wardens/Admin) --------------------

@require_http_methods(["POST"])
@permission_required("gate.can_toggle_status", login_url="login")
def toggle_status(request):
    enr = (request.POST.get("enrollment_number") or "").strip()
    note = (request.POST.get("note") or "").strip()
    try:
        student = Student.objects.get(enrollment_number__iexact=enr)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("check")

    # Flip status
    student.is_inside = not student.is_inside
    student.save()

    direction = MovementLog.IN if student.is_inside else MovementLog.OUT
    MovementLog.objects.create(
        student=student,
        direction=direction,
        recorded_by=request.user if request.user.is_authenticated else None,
        note=note,
    )

    messages.success(
        request,
        f"{student.full_name} marked {direction} at {timezone.now():%d %b %Y, %I:%M %p}.",
    )
    return redirect("check")


# -------------------- Data entry (Wardens/Admin) --------------------

@permission_required("gate.add_student", login_url="login")
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Student {s.full_name} ({s.enrollment_number}) added.")
            return redirect("add_student")
    else:
        form = StudentForm()
    return render(request, "gate/add_student.html", {"form": form})


@permission_required("gate.change_student", login_url="login")
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {student.full_name}.")
            return redirect("check")
    else:
        form = StudentForm(instance=student)
    # Reuse the same template; it works for edit too
    return render(request, "gate/add_student.html", {"form": form})


@permission_required("gate.add_student", login_url="login")
@permission_required("gate.change_student", login_url="login")
def import_students_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            text = io.TextIOWrapper(request.FILES["file"].file, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            created = updated = errors = 0
            for row in reader:
                try:
                    enr = (row.get("enrollment_number") or "").strip()
                    name = (row.get("full_name") or "").strip()
                    room = (row.get("room_number") or "").strip()
                    phone = (row.get("phone") or "").strip()
                    if not enr or not name:
                        errors += 1
                        continue
                    obj, is_created = Student.objects.update_or_create(
                        enrollment_number__iexact=enr,
                        defaults={
                            "enrollment_number": enr,
                            "full_name": name,
                            "room_number": room,
                            "phone": phone,
                        },
                    )
                    if is_created:
                        created += 1
                    else:
                        updated += 1
                except Exception:
                    errors += 1
            messages.success(request, f"Import complete. Created: {created}, Updated: {updated}, Errors: {errors}")
            return redirect("import_students_csv")
    else:
        form = CSVUploadForm()
    return render(request, "gate/import_students_csv.html", {"form": form})


# -------------------- JSON APIs (keep for integrations) --------------------

@csrf_exempt
@require_http_methods(["GET"])
def api_search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    qs = Student.objects.filter(
        Q(enrollment_number__icontains=q) | Q(full_name__icontains=q)
    ).order_by("enrollment_number")[:50]
    data = [{
        "enrollment": s.enrollment_number,
        "name": s.full_name,
        "room": s.room_number,
        "phone": s.phone,
        "is_inside": s.is_inside
    } for s in qs]
    return JsonResponse({"results": data})


@csrf_exempt
@require_http_methods(["POST"])
def api_check(request):
    enr = (request.POST.get("enrollment_number") or "").strip()
    if not enr:
        return JsonResponse({"found": False, "error": "missing_enrollment_number"}, status=400)
    try:
        s = Student.objects.get(enrollment_number__iexact=enr)
        return JsonResponse({
            "found": True,
            "enrollment": s.enrollment_number,
            "name": s.full_name,
            "is_inside": s.is_inside,
        })
    except Student.DoesNotExist:
        return JsonResponse({"found": False}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@permission_required("gate.can_toggle_status", login_url="login")
def api_toggle(request):
    enr = (request.POST.get("enrollment_number") or "").strip()
    note = (request.POST.get("note") or "").strip()
    if not enr:
        return JsonResponse({"ok": False, "error": "missing_enrollment_number"}, status=400)
    try:
        s = Student.objects.get(enrollment_number__iexact=enr)
    except Student.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)

    s.is_inside = not s.is_inside
    s.save()

    direction = MovementLog.IN if s.is_inside else MovementLog.OUT
    MovementLog.objects.create(
        student=s,
        direction=direction,
        recorded_by=request.user if request.user.is_authenticated else None,
        note=note,
    )

    return JsonResponse(
        {
            "ok": True,
            "enrollment": s.enrollment_number,
            "name": s.full_name,
            "is_inside": s.is_inside,
            "direction": direction,
            "timestamp": timezone.now().isoformat(),
        }
    )
