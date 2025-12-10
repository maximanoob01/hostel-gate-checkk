from django.contrib import admin
from .models import Student, MovementLog

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("enrollment_number", "full_name", "room_number", "is_inside")
    search_fields = ("enrollment_number", "full_name", "room_number", "phone")
    list_filter = ("is_inside",)

@admin.register(MovementLog)
class MovementLogAdmin(admin.ModelAdmin):
    list_display = ("student", "direction", "timestamp", "recorded_by")
    search_fields = ("student__enrollment_number", "student__full_name")
    list_filter = ("direction", "timestamp")
    
admin.site.site_header = "GateCheck Admin"
admin.site.site_title = "GateCheck Admin Portal"
admin.site.index_title = "Welcome to the Hostel Management Panel"
