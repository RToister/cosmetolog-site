from django.db.models.signals import post_save
from django.dispatch import receiver

from academy.models import Course, CourseEnrollment
from appointments.models import Booking
from shop.models import Order

from .models import Customer


def get_customer_type(user=None, professional=False):
    if professional:
        return Customer.CustomerType.COSMETOLOGIST

    if (
            user
            and user.is_authenticated
            and getattr(user, "user_type", None) == "cosmetologist"
    ):
        return Customer.CustomerType.COSMETOLOGIST

    return Customer.CustomerType.CLIENT


@receiver(post_save, sender=Booking)
def create_customer_from_booking(
        sender,
        instance,
        **kwargs,
):
    if not instance.client_phone:
        return

    user = instance.client if instance.client_id else None

    customer, _ = Customer.objects.get_or_create_by_phone(
        full_name=instance.client_name,
        phone_number=instance.client_phone,
        user=user,
        customer_type=get_customer_type(user=user),
    )

    if instance.customer_id != customer.pk:
        sender.objects.filter(
            pk=instance.pk,
        ).update(
            customer=customer,
        )


@receiver(post_save, sender=Order)
def create_customer_from_order(
        sender,
        instance,
        **kwargs,
):
    if not instance.client_phone:
        return

    user = instance.client if instance.client_id else None

    professional = instance.client_is_cosmetologist

    if (
            instance.customer_id
            and instance.customer.customer_type
            == Customer.CustomerType.COSMETOLOGIST
    ):
        professional = True

    customer, _ = Customer.objects.get_or_create_by_phone(
        full_name=instance.client_name,
        phone_number=instance.client_phone,
        user=user,
        customer_type=get_customer_type(
            user=user,
            professional=professional,
        ),
    )

    if instance.customer_id != customer.pk:
        sender.objects.filter(
            pk=instance.pk,
        ).update(
            customer=customer,
        )


@receiver(post_save, sender=CourseEnrollment)
def create_customer_from_course_application(
        sender,
        instance,
        **kwargs,
):
    if not instance.applicant_phone:
        return

    user = instance.student if instance.student_id else None

    professional_course = (
            instance.course.audience
            == Course.Audience.COSMETOLOGISTS
    )

    customer, _ = Customer.objects.get_or_create_by_phone(
        full_name=instance.applicant_name,
        phone_number=instance.applicant_phone,
        user=user,
        customer_type=get_customer_type(
            user=user,
            professional=professional_course,
        ),
    )

    if instance.customer_id != customer.pk:
        sender.objects.filter(
            pk=instance.pk,
        ).update(
            customer=customer,
        )
