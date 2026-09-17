from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from academy.models import CourseEnrollment
from appointments.models import Booking, VisitComment
from shop.models import Order

from .operation_forms import (
    BookingStatusForm,
    CourseApplicationStatusForm,
    OrderStatusForm,
)


@staff_member_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "procedure",
            "procedure__category",
            "client",
            "customer",
            "created_by",
        ),
        pk=pk,
    )

    try:
        visit_comment = booking.visit_comment
    except VisitComment.DoesNotExist:
        visit_comment = None

    status_form = BookingStatusForm(
        initial={
            "status": booking.status,
        }
    )

    return render(
        request,
        "crm/operation_detail.html",
        {
            "operation_type": "booking",
            "active_crm_section": "bookings",
            "booking": booking,
            "visit_comment": visit_comment,
            "status_form": status_form,
        },
    )


@staff_member_required
@require_POST
def booking_status_update(request, pk):
    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    form = BookingStatusForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            "Не вдалося змінити статус запису.",
        )

        return redirect(
            "crm:booking-detail",
            pk=booking.pk,
        )

    Booking.objects.filter(
        pk=booking.pk,
    ).update(
        status=form.cleaned_data["status"],
        updated_at=timezone.now(),
    )

    messages.success(
        request,
        "Статус запису успішно змінено.",
    )

    return redirect(
        "crm:booking-detail",
        pk=booking.pk,
    )


@staff_member_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related(
            "client",
            "customer",
            "created_by",
        ).prefetch_related(
            "items",
            "items__product",
        ),
        pk=pk,
    )

    status_form = OrderStatusForm(
        initial={
            "status": order.status,
            "payment_method": (
                order.payment_method
            ),
        }
    )

    return render(
        request,
        "crm/operation_detail.html",
        {
            "operation_type": "order",
            "active_crm_section": "orders",
            "order": order,
            "status_form": status_form,
        },
    )


@staff_member_required
@require_POST
@transaction.atomic
def order_status_update(request, pk):
    order = get_object_or_404(
        Order.objects.select_for_update(),
        pk=pk,
    )

    form = OrderStatusForm(
        request.POST
    )

    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(
                    request,
                    error,
                )

        return redirect(
            "crm:order-detail",
            pk=order.pk,
        )

    new_status = form.cleaned_data["status"]
    payment_method = form.cleaned_data[
        "payment_method"
    ]

    try:
        if new_status == Order.Status.PAID:
            if order.status == Order.Status.CANCELLED:
                messages.error(
                    request,
                    (
                        "Скасоване замовлення спочатку "
                        "потрібно повернути у статус "
                        "«Очікує обробки»."
                    ),
                )

                return redirect(
                    "crm:order-detail",
                    pk=order.pk,
                )

            order.payment_method = payment_method

            order.save(
                update_fields=(
                    "payment_method",
                    "updated_at",
                )
            )

            order.mark_as_paid()

        elif new_status == Order.Status.CANCELLED:
            order.cancel()

        else:
            if order.status == Order.Status.PAID:
                messages.error(
                    request,
                    (
                        "Оплачене замовлення не можна "
                        "відразу повернути в очікування. "
                        "Спочатку скасуйте його, щоб "
                        "повернути товар на склад."
                    ),
                )

                return redirect(
                    "crm:order-detail",
                    pk=order.pk,
                )

            order.status = Order.Status.PENDING
            order.payment_method = payment_method
            order.paid_at = None

            order.save(
                update_fields=(
                    "status",
                    "payment_method",
                    "paid_at",
                    "updated_at",
                )
            )

    except ValidationError as error:
        if hasattr(error, "messages"):
            error_text = " ".join(
                error.messages
            )
        else:
            error_text = str(error)

        messages.error(
            request,
            error_text,
        )

        return redirect(
            "crm:order-detail",
            pk=order.pk,
        )

    messages.success(
        request,
        "Статус замовлення успішно змінено.",
    )

    return redirect(
        "crm:order-detail",
        pk=order.pk,
    )


@staff_member_required
def course_application_detail(
        request,
        pk,
):
    application = get_object_or_404(
        CourseEnrollment.objects.select_related(
            "course",
            "student",
            "customer",
            "created_by",
        ),
        pk=pk,
    )

    status_form = (
        CourseApplicationStatusForm(
            initial={
                "status": application.status,
            }
        )
    )

    return render(
        request,
        "crm/operation_detail.html",
        {
            "operation_type": "course",
            "active_crm_section": "courses",
            "application": application,
            "status_form": status_form,
        },
    )


@staff_member_required
@require_POST
def course_application_status_update(
        request,
        pk,
):
    application = get_object_or_404(
        CourseEnrollment,
        pk=pk,
    )

    form = CourseApplicationStatusForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            "Не вдалося змінити статус заявки.",
        )

        return redirect(
            "crm:course-application-detail",
            pk=application.pk,
        )

    CourseEnrollment.objects.filter(
        pk=application.pk,
    ).update(
        status=form.cleaned_data["status"],
        updated_at=timezone.now(),
    )

    messages.success(
        request,
        "Статус заявки успішно змінено.",
    )

    return redirect(
        "crm:course-application-detail",
        pk=application.pk,
    )
