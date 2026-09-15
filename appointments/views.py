from datetime import datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from schedule.models import BlockedDate, WorkingHour
from services.models import Procedure

from .forms import BookingForm
from .models import Booking


def booking_create(request):
    form = BookingForm(
        request.POST or None,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.source = Booking.Source.ONLINE

        if request.user.is_authenticated:
            booking.client = request.user
            booking.created_by = request.user

        booking.save()

        messages.success(
            request,
            "Ваш запис успішно створено.",
        )

        return redirect("appointments:booking-success")

    return render(
        request,
        "appointments/booking_form.html",
        {"form": form},
    )


def booking_success(request):
    return render(
        request,
        "appointments/booking_success.html",
    )


@require_GET
def available_times(request):
    selected_date = request.GET.get("date")
    procedure_id = request.GET.get("procedure")

    if not selected_date or not procedure_id:
        return JsonResponse(
            {
                "available_times": [],
                "error": "Оберіть процедуру та дату.",
            }
        )

    try:
        booking_date = datetime.strptime(
            selected_date,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return JsonResponse(
            {
                "available_times": [],
                "error": "Некоректна дата.",
            }
        )

    if booking_date < timezone.localdate():
        return JsonResponse(
            {
                "available_times": [],
                "error": "Неможливо записатися на минулу дату.",
            }
        )

    try:
        procedure = Procedure.objects.get(
            pk=procedure_id,
            is_active=True,
        )
    except (Procedure.DoesNotExist, ValueError):
        return JsonResponse(
            {
                "available_times": [],
                "error": "Процедуру не знайдено.",
            }
        )

    if BlockedDate.objects.filter(date=booking_date).exists():
        return JsonResponse(
            {
                "available_times": [],
                "error": "Обраний день недоступний для запису.",
            }
        )

    try:
        working_hours = WorkingHour.objects.get(
            day_of_week=booking_date.weekday(),
            is_active=True,
        )
    except WorkingHour.DoesNotExist:
        return JsonResponse(
            {
                "available_times": [],
                "error": "У цей день лікар не працює.",
            }
        )

    existing_bookings = Booking.objects.filter(
        date=booking_date,
    ).exclude(
        status=Booking.Status.CANCELLED,
    )

    current_datetime = timezone.localtime()

    slot_datetime = datetime.combine(
        booking_date,
        working_hours.start_time,
    )
    working_day_end = datetime.combine(
        booking_date,
        working_hours.end_time,
    )

    procedure_duration = timedelta(
        minutes=procedure.duration_minutes,
    )
    slot_interval = timedelta(minutes=30)

    available_slots = []

    while slot_datetime + procedure_duration <= working_day_end:
        slot_start = slot_datetime.time()
        slot_end = (
                slot_datetime + procedure_duration
        ).time()

        slot_is_in_past = (
                booking_date == current_datetime.date()
                and slot_start <= current_datetime.time()
        )

        has_overlap = existing_bookings.filter(
            start_time__lt=slot_end,
            end_time__gt=slot_start,
        ).exists()

        if not slot_is_in_past and not has_overlap:
            available_slots.append(
                {
                    "value": slot_start.strftime("%H:%M"),
                    "label": slot_start.strftime("%H:%M"),
                }
            )

        slot_datetime += slot_interval

    return JsonResponse(
        {
            "available_times": available_slots,
            "error": "",
        }
    )
