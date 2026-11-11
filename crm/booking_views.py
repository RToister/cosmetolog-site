from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse

from appointments.forms import (
    StaffBookingForm,
    VisitCommentForm,
)
from appointments.models import (
    Booking,
    VisitComment,
)


@staff_member_required
@transaction.atomic
def booking_create(request):
    form = StaffBookingForm(
        request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)

        booking.source = Booking.Source.ADMIN

        booking.created_by = request.user
        booking.save()

        messages.success(
            request,
            "Запис успішно створено.",
        )

        return redirect(
            "crm:booking-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "crm/booking_form.html",
        {
            "form": form,
            "booking": None,
            "page_title": "Новий запис",
            "submit_text": "Створити запис",
            "cancel_url": reverse("crm:booking-list"),
        },
    )


@staff_member_required
@transaction.atomic
def booking_update(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "procedure",
            "customer",
            "client",
        ),
        pk=pk,
    )

    form = StaffBookingForm(
        request.POST or None,
        instance=booking,
    )

    if request.method == "POST" and form.is_valid():
        booking = form.save()

        messages.success(
            request,
            "Запис успішно оновлено.",
        )

        return redirect(
            "crm:booking-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "crm/booking_form.html",
        {
            "form": form,
            "booking": booking,
            "page_title": (f"Редагування запису №{booking.pk}"),
            "submit_text": "Зберегти зміни",
            "cancel_url": reverse(
                "crm:booking-detail",
                kwargs={
                    "pk": booking.pk,
                },
            ),
        },
    )


@staff_member_required
@transaction.atomic
def booking_comment_update(
    request,
    pk,
):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "procedure",
            "customer",
        ),
        pk=pk,
    )

    visit_comment = VisitComment.objects.filter(
        booking=booking,
    ).first()

    form = VisitCommentForm(
        request.POST or None,
        instance=visit_comment,
    )

    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)

        comment.booking = booking
        comment.author = request.user
        comment.save()

        messages.success(
            request,
            ("Коментар лікаря та " "рекомендації збережено."),
        )

        return redirect(
            "crm:booking-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "crm/booking_comment_form.html",
        {
            "form": form,
            "booking": booking,
            "visit_comment": visit_comment,
        },
    )
