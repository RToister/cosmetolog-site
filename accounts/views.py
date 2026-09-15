from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import UserProfileForm, UserRegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Ваш обліковий запис успішно створено.",
            )
            return redirect("accounts:dashboard")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


@login_required
def dashboard(request):
    current_datetime = timezone.localtime()
    today = current_datetime.date()
    current_time = current_datetime.time()

    bookings = (
        request.user.bookings
        .select_related("procedure", "procedure__category")
        .order_by("-date", "-start_time")
    )

    upcoming_bookings = bookings.filter(
        Q(date__gt=today)
        | Q(
            date=today,
            end_time__gt=current_time,
        ),
        status__in=(
            "pending",
            "confirmed",
        ),
    ).order_by("date", "start_time")

    booking_history = bookings.filter(
        Q(date__lt=today)
        | Q(
            date=today,
            end_time__lte=current_time,
        )
        | Q(
            status__in=(
                "completed",
                "cancelled",
            )
        )
    )

    orders = (
        request.user.orders
        .prefetch_related("items", "items__product")
        .order_by("-created_at")
    )

    course_enrollments = (
        request.user.course_enrollments
        .select_related("course")
        .order_by("-enrolled_at")
    )

    context = {
        "upcoming_bookings": upcoming_bookings,
        "booking_history": booking_history,
        "orders": orders,
        "course_enrollments": course_enrollments,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context,
    )


@login_required
def profile_update(request):
    if request.method == "POST":
        form = UserProfileForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Дані профілю успішно оновлено.",
            )
            return redirect("accounts:dashboard")
    else:
        form = UserProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile_form.html",
        {"form": form},
    )
