from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academy.models import Course, CourseEnrollment


class AcademyViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.public_course = Course.objects.create(
            title="Основи домашнього догляду",
            description=(
                "Навчання правильному домашньому "
                "догляду за шкірою."
            ),
            audience=Course.Audience.EVERYONE,
            training_type=Course.TrainingType.BOTH,
            format=Course.Format.ONLINE,
            duration_hours=3,
            price=Decimal("1500.00"),
            is_published=True,
        )

        cls.professional_course = Course.objects.create(
            title="Професійна мезотерапія",
            description=(
                "Професійне навчання для косметологів."
            ),
            audience=Course.Audience.COSMETOLOGISTS,
            training_type=Course.TrainingType.INDIVIDUAL,
            format=Course.Format.OFFLINE,
            duration_hours=8,
            price=Decimal("6000.00"),
            is_published=True,
        )

        cls.unpublished_course = Course.objects.create(
            title="Неопублікований курс",
            description="Цей курс не повинен бути видимим.",
            audience=Course.Audience.EVERYONE,
            training_type=Course.TrainingType.GROUP,
            format=Course.Format.ONLINE,
            duration_hours=2,
            price=Decimal("1000.00"),
            is_published=False,
        )

    def test_course_list_is_available(self):
        response = self.client.get(
            reverse("academy:course-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "academy/course_list.html",
        )

    def test_course_list_displays_both_audiences(self):
        response = self.client.get(
            reverse("academy:course-list")
        )

        self.assertContains(
            response,
            self.public_course.title,
        )
        self.assertContains(
            response,
            self.professional_course.title,
        )

    def test_unpublished_course_is_hidden(self):
        response = self.client.get(
            reverse("academy:course-list")
        )

        self.assertNotContains(
            response,
            self.unpublished_course.title,
        )

        detail_response = self.client.get(
            reverse(
                "academy:course-detail",
                args=[self.unpublished_course.pk],
            )
        )

        self.assertEqual(
            detail_response.status_code,
            404,
        )

    def test_published_course_detail_is_available(self):
        response = self.client.get(
            reverse(
                "academy:course-detail",
                args=[self.public_course.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "academy/course_detail.html",
        )
        self.assertContains(
            response,
            self.public_course.title,
        )

    def test_guest_can_submit_course_application(self):
        response = self.client.post(
            reverse(
                "academy:course-detail",
                args=[self.public_course.pk],
            ),
            {
                "applicant_name": "Марія",
                "applicant_phone": "+380991112233",
                "applicant_comment": (
                    "Цікавить індивідуальне навчання."
                ),
            },
        )

        application = CourseEnrollment.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "academy:application-success",
                args=[application.pk],
            ),
        )

        self.assertIsNone(application.student)
        self.assertEqual(
            application.applicant_name,
            "Марія",
        )
        self.assertEqual(
            application.applicant_phone,
            "+380991112233",
        )
        self.assertEqual(
            application.course,
            self.public_course,
        )
        self.assertEqual(
            application.status,
            CourseEnrollment.Status.PENDING,
        )
        self.assertEqual(
            application.source,
            CourseEnrollment.Source.ONLINE,
        )
        self.assertEqual(
            application.price_at_enrollment,
            Decimal("1500.00"),
        )

    def test_authenticated_user_cannot_create_duplicate_application(
            self,
    ):
        cosmetologist = (
            get_user_model().objects.create_user(
                username="cosmetologist",
                password="test-password-123",
                first_name="Анна",
                phone_number="+380991112244",
                user_type="cosmetologist",
            )
        )

        self.client.force_login(cosmetologist)

        application_data = {
            "applicant_name": "Анна",
            "applicant_phone": "+380991112244",
            "applicant_comment": "",
        }

        self.client.post(
            reverse(
                "academy:course-detail",
                args=[self.professional_course.pk],
            ),
            application_data,
        )

        self.client.post(
            reverse(
                "academy:course-detail",
                args=[self.professional_course.pk],
            ),
            application_data,
        )

        self.assertEqual(
            CourseEnrollment.objects.filter(
                student=cosmetologist,
                course=self.professional_course,
            ).count(),
            1,
        )

    def test_invalid_phone_does_not_create_application(self):
        response = self.client.post(
            reverse(
                "academy:course-detail",
                args=[self.public_course.pk],
            ),
            {
                "applicant_name": "Марія",
                "applicant_phone": "invalid-phone",
                "applicant_comment": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            CourseEnrollment.objects.exists()
        )

        phone_errors = response.context["form"].errors[
            "applicant_phone"
        ]

        self.assertIn(
            "Номер телефону містить недопустимі символи.",
            phone_errors,
        )

    def test_success_page_is_available_after_application(self):
        self.client.post(
            reverse(
                "academy:course-detail",
                args=[self.public_course.pk],
            ),
            {
                "applicant_name": "Олена",
                "applicant_phone": "+380991112255",
                "applicant_comment": "",
            },
        )

        application = CourseEnrollment.objects.get()

        response = self.client.get(
            reverse(
                "academy:application-success",
                args=[application.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "academy/application_success.html",
        )
        self.assertContains(
            response,
            self.public_course.title,
        )

    def test_unrelated_success_page_is_hidden(self):
        application = CourseEnrollment.objects.create(
            applicant_name="Інший заявник",
            applicant_phone="+380991112266",
            course=self.public_course,
            source=CourseEnrollment.Source.ONLINE,
        )

        response = self.client.get(
            reverse(
                "academy:application-success",
                args=[application.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
