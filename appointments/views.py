from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import (
    require_GET,
    require_POST,
)

from schedule.models import BlockedDate, WorkingHour
from services.models import Procedure

from .forms import (
    BookingForm,
    StaffBookingForm,
    VisitCommentForm,
)
from .models import Booking, VisitComment


def booking_create(request):
    form = BookingForm(
        request.POST or None,
        user=request.user,
    )

    if (
            request.method == "POST"
            and form.is_valid()
    ):
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

        return redirect(
            "appointments:booking-success"
        )

    return render(
        request,
        "appointments/booking_form.html",
        {
            "form": form,
        },
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
                "error": (
                    "Оберіть процедуру та дату."
                ),
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
                "error": (
                    "Неможливо записатися "
                    "на минулу дату."
                ),
            }
        )

    try:
        procedure = Procedure.objects.get(
            pk=procedure_id,
            is_active=True,
        )
    except (
            Procedure.DoesNotExist,
            ValueError,
    ):
        return JsonResponse(
            {
                "available_times": [],
                "error": (
                    "Процедуру не знайдено."
                ),
            }
        )

    if BlockedDate.objects.filter(
            date=booking_date,
    ).exists():
        return JsonResponse(
            {
                "available_times": [],
                "error": (
                    "Обраний день недоступний "
                    "для запису."
                ),
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
                "error": (
                    "У цей день лікар не працює."
                ),
            }
        )

    existing_bookings = Booking.objects.filter(
        date=booking_date,
    ).exclude(
        status=Booking.Status.CANCELLED,
    )

    excluded_booking_id = request.GET.get(
        "exclude_booking"
    )

    if excluded_booking_id:
        existing_bookings = (
            existing_bookings.exclude(
                pk=excluded_booking_id,
            )
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

    while (
            slot_datetime + procedure_duration
            <= working_day_end
    ):
        slot_start = slot_datetime.time()
        slot_end = (
                slot_datetime + procedure_duration
        ).time()

        slot_is_in_past = (
                booking_date
                == current_datetime.date()
                and slot_start
                <= current_datetime.time()
        )

        has_overlap = existing_bookings.filter(
            start_time__lt=slot_end,
            end_time__gt=slot_start,
        ).exists()

        if (
                not slot_is_in_past
                and not has_overlap
        ):
            available_slots.append(
                {
                    "value": slot_start.strftime(
                        "%H:%M"
                    ),
                    "label": slot_start.strftime(
                        "%H:%M"
                    ),
                }
            )

        slot_datetime += slot_interval

    return JsonResponse(
        {
            "available_times": available_slots,
            "error": "",
        }
    )


@staff_member_required
def booking_manage_list(request):
    selected_date = request.GET.get(
        "date",
        "",
    )
    selected_status = request.GET.get(
        "status",
        "",
    )
    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    bookings = Booking.objects.select_related(
        "procedure",
        "procedure__category",
        "customer",
        "client",
    )

    if selected_date:
        try:
            parsed_date = datetime.strptime(
                selected_date,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            selected_date = ""
        else:
            bookings = bookings.filter(
                date=parsed_date,
            )

    valid_statuses = {
        value
        for value, label in Booking.Status.choices
    }

    if selected_status in valid_statuses:
        bookings = bookings.filter(
            status=selected_status,
        )
    else:
        selected_status = ""

    if search_query:
        bookings = bookings.filter(
            Q(
                client_name__icontains=(
                    search_query
                )
            )
            | Q(
                client_phone__icontains=(
                    search_query
                )
            )
            | Q(
                procedure__name__icontains=(
                    search_query
                )
            )
        )

    bookings = bookings.order_by(
        "-date",
        "-start_time",
    )

    paginator = Paginator(
        bookings,
        25,
    )
    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    today = timezone.localdate()

    context = {
        "page_obj": page_obj,
        "selected_date": selected_date,
        "selected_status": selected_status,
        "search_query": search_query,
        "status_choices": Booking.Status.choices,
        "today": today,
        "today_count": Booking.objects.filter(
            date=today,
        ).exclude(
            status=Booking.Status.CANCELLED,
        ).count(),
        "pending_count": Booking.objects.filter(
            status=Booking.Status.PENDING,
        ).count(),
        "confirmed_count": Booking.objects.filter(
            status=Booking.Status.CONFIRMED,
        ).count(),
    }

    return render(
        request,
        "appointments/manage_list.html",
        context,
    )


@staff_member_required
@transaction.atomic
def booking_manage_create(request):
    form = StaffBookingForm(
        request.POST or None,
    )

    if (
            request.method == "POST"
            and form.is_valid()
    ):
        booking = form.save(commit=False)
        booking.source = Booking.Source.ADMIN
        booking.created_by = request.user
        booking.save()

        messages.success(
            request,
            "Запис успішно створено.",
        )

        return redirect(
            "appointments:manage-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "appointments/manage_form.html",
        {
            "form": form,
            "page_title": "Новий запис",
            "submit_text": "Створити запис",
            "booking": None,
        },
    )


@staff_member_required
def booking_manage_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "procedure",
            "procedure__category",
            "customer",
            "client",
            "created_by",
        ),
        pk=pk,
    )

    try:
        visit_comment = booking.visit_comment
    except VisitComment.DoesNotExist:
        visit_comment = None

    return render(
        request,
        "appointments/manage_detail.html",
        {
            "booking": booking,
            "visit_comment": visit_comment,
        },
    )


@staff_member_required
@transaction.atomic
def booking_manage_update(request, pk):
    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    form = StaffBookingForm(
        request.POST or None,
        instance=booking,
    )

    if (
            request.method == "POST"
            and form.is_valid()
    ):
        booking = form.save()

        messages.success(
            request,
            "Запис успішно оновлено.",
        )

        return redirect(
            "appointments:manage-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "appointments/manage_form.html",
        {
            "form": form,
            "page_title": "Редагування запису",
            "submit_text": "Зберегти зміни",
            "booking": booking,
        },
    )


@staff_member_required
@require_POST
def booking_status_update(request, pk):
    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    new_status = request.POST.get("status")

    valid_statuses = {
        value
        for value, label in Booking.Status.choices
    }

    if new_status not in valid_statuses:
        messages.error(
            request,
            "Обрано некоректний статус.",
        )

        return redirect(
            "appointments:manage-detail",
            pk=booking.pk,
        )

    Booking.objects.filter(
        pk=booking.pk,
    ).update(
        status=new_status,
        updated_at=timezone.now(),
    )

    messages.success(
        request,
        "Статус запису змінено.",
    )

    return redirect(
        "appointments:manage-detail",
        pk=booking.pk,
    )


@staff_member_required
@transaction.atomic
def booking_comment_update(request, pk):
    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    visit_comment = VisitComment.objects.filter(
        booking=booking,
    ).first()

    form = VisitCommentForm(
        request.POST or None,
        instance=visit_comment,
    )

    if (
            request.method == "POST"
            and form.is_valid()
    ):
        comment = form.save(commit=False)
        comment.booking = booking
        comment.author = request.user
        comment.save()

        messages.success(
            request,
            "Коментар і рекомендації збережено.",
        )

        return redirect(
            "appointments:manage-detail",
            pk=booking.pk,
        )

    return render(
        request,
        "appointments/comment_form.html",
        {
            "form": form,
            "booking": booking,
        },
    )
