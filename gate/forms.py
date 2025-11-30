# gate/forms.py
from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["enrollment_number", "full_name", "room_number", "phone", "is_inside"]
        widgets = {
            "enrollment_number": forms.TextInput(attrs={"placeholder":"Enrollment Number"}),
            "full_name": forms.TextInput(attrs={"placeholder":"Full name"}),
            "room_number": forms.TextInput(attrs={"placeholder":"Room (optional)"}),
            "phone": forms.TextInput(attrs={"placeholder":"Phone (optional)"}),
        }

class CSVUploadForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV with columns: enrollment_number,full_name,room_number,phone")

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["enrollment_number", "full_name", "room_number", "phone", "is_inside"]

class CSVUploadForm(forms.Form):
    file = forms.FileField(help_text="CSV with: enrollment_number,full_name,room_number,phone")