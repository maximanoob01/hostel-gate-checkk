from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Student, MovementLog
import datetime
from django.urls import reverse

class BasicTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class StudentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            enrollment_number="2023-001",
            full_name="John Doe",
            room_number="101",
            phone="1234567890",
            is_inside=True,
        )

    def test_student_creation(self):
        self.assertIsInstance(self.student, Student)
        self.assertEqual(self.student.enrollment_number, "2023-001")
        self.assertEqual(self.student.full_name, "John Doe")
        self.assertTrue(self.student.is_inside)

    def test_student_str(self):
        self.assertEqual(str(self.student), "2023-001 - John Doe")

class MovementLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.student = Student.objects.create(
            enrollment_number="2023-001",
            full_name="John Doe",
        )
        self.log = MovementLog.objects.create(
            student=self.student,
            direction=MovementLog.OUT,
            recorded_by=self.user,
        )

    def test_movement_log_creation(self):
        self.assertIsInstance(self.log, MovementLog)
        self.assertEqual(self.log.student, self.student)
        self.assertEqual(self.log.direction, MovementLog.OUT)
        self.assertEqual(self.log.recorded_by, self.user)

    def test_movement_log_str(self):
        # The timestamp is auto-generated, so we need to be careful with the string representation.
        # We will check the parts of the string that we can predict.
        expected_start = f"{self.student.enrollment_number} {self.log.direction} at "
        self.assertTrue(str(self.log).startswith(expected_start))

class HomePageTest(TestCase):
    def test_home_page_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

class CheckViewTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            enrollment_number="2023-001",
            full_name="John Doe",
            room_number="101",
            phone="1234567890",
            is_inside=True,
        )

    def test_check_view_get_existing_student(self):
        response = self.client.get(reverse('check'), {'enr': '2023-001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "2023-001")

    def test_check_view_get_non_existing_student(self):
        response = self.client.get(reverse('check'), {'enr': '2023-002'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "John Doe")
        self.assertContains(response, "No student found for enrollment 2023-002.")

    def test_check_view_post_exact_match(self):
        response = self.client.post(reverse('check'), {'enrollment_number': '2023-001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_check_view_post_partial_enrollment_match(self):
        response = self.client.post(reverse('check'), {'enrollment_number': '2023'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_check_view_post_partial_name_match(self):
        response = self.client.post(reverse('check'), {'enrollment_number': 'john'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_check_view_post_no_match(self):
        response = self.client.post(reverse('check'), {'enrollment_number': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No matches found for “nonexistent”.')

    def test_check_view_post_empty_query(self):
        response = self.client.post(reverse('check'), {'enrollment_number': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter an enrollment number or name.')

class ToggleStatusViewTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(enrollment_number="2023-001", full_name="John Doe", is_inside=True)
        self.user_with_perm = User.objects.create_user(username='testuser', password='password')
        permission = Permission.objects.get(codename='can_toggle_status')
        self.user_with_perm.user_permissions.add(permission)
        self.user_without_perm = User.objects.create_user(username='noperm', password='password')

    def test_toggle_status_unauthenticated(self):
        response = self.client.post(reverse('toggle'), {'enrollment_number': '2023-001'})
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('toggle')}")

    def test_toggle_status_authenticated_no_permission(self):
        self.client.login(username='noperm', password='password')
        response = self.client.post(reverse('toggle'), {'enrollment_number': '2023-001'})
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('toggle')}")


    def test_toggle_status_authenticated_with_permission(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('toggle'), {'enrollment_number': '2023-001'})

        # The view redirects to 'check' on success
        self.assertRedirects(response, reverse('check'))
        
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_inside)
        
        # Check that a MovementLog was created
        log = MovementLog.objects.latest('timestamp')
        self.assertEqual(log.student, self.student)
        self.assertEqual(log.direction, MovementLog.OUT)
        self.assertEqual(log.recorded_by, self.user_with_perm)

