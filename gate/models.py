
from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    enrollment_number = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=120)
    room_number = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_inside = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["enrollment_number"]

        permissions = [
            ("can_toggle_status", "Can toggle in/out status"),  # 👈 new
        ]


    def __str__(self):
        return f"{self.enrollment_number} - {self.full_name}"

class MovementLog(models.Model):
    IN = "IN"
    OUT = "OUT"
    DIRECTION_CHOICES = [(IN, "IN"), (OUT, "OUT")]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True)
    photo = models.ImageField(upload_to="students/", blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student.enrollment_number} {self.direction} at {self.timestamp:%Y-%m-%d %H:%M}"
