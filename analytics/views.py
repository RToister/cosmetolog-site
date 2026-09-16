from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.contrib.auth import get_user_model
from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)
from django.shortcuts import render
from django.utils import timezone

from academy.models import CourseEnrollment
from appointments.models import Booking
from shop.models import Order, OrderItem

from .forms import AnalyticsPeriodForm


@staff_member_required(
    login_url="accounts:login",
)
def analytics_dashboard(request):
    today = timezone.localdate()
    default_start_date = today - timedelta(days=29)

    form_data = request.GET or {
        "start_date": default_start_date.isoformat(),
        "end_date": today.isoformat(),
    }

    form = AnalyticsPeriodForm(form_data)

    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
    else:
        start_date = default_start_date
        end_date = today

    bookings = Booking.objects.filter(
        date__range=(start_date, end_date),
    )

    completed_bookings = bookings.filter(
        status=Booking.Status.COMPLETED,
    )

    procedure_revenue = (
            completed_bookings.aggregate(
                total=Sum("price_at_booking"),
            )["total"]
            or Decimal("0.00")
    )

    paid_orders = Order.objects.filter(
        status=Order.Status.PAID,
        paid_at__date__range=(
            start_date,
            end_date,
        ),
    )

    product_revenue = (
            paid_orders.aggregate(
                total=Sum("total_price"),
            )["total"]
            or Decimal("0.00")
    )

    total_revenue = (
            procedure_revenue + product_revenue
    )

    top_procedures = (
        completed_bookings.values(
            "procedure__name",
        )
        .annotate(
            bookings_count=Count("id"),
            revenue=Sum("price_at_booking"),
        )
        .order_by("-bookings_count", "-revenue")[:5]
    )

    item_revenue_expression = ExpressionWrapper(
        F("quantity") * F("price_at_purchase"),
        output_field=DecimalField(
            max_digits=12,
            decimal_places=2,
        ),
    )

    top_products = (
        OrderItem.objects.filter(
            order__status=Order.Status.PAID,
            order__paid_at__date__range=(
                start_date,
                end_date,
            ),
        )
        .values(
            "product__name",
            "product__sku",
        )
        .annotate(
            sold_quantity=Sum("quantity"),
            revenue=Sum(item_revenue_expression),
        )
        .order_by("-sold_quantity", "-revenue")[:5]
    )

    registered_clients_count = (
        get_user_model().objects.filter(
            user_type="client",
        ).count()
    )

    cosmetologists_count = (
        get_user_model().objects.filter(
            user_type="cosmetologist",
        ).count()
    )

    unique_booking_clients = (
        bookings.exclude(client_phone="")
        .values("client_phone")
        .distinct()
        .count()
    )

    pending_orders_count = Order.objects.filter(
        status=Order.Status.PENDING,
    ).count()

    pending_course_applications_count = (
        CourseEnrollment.objects.filter(
            status=CourseEnrollment.Status.PENDING,
        ).count()
    )

    upcoming_bookings_count = (
        Booking.objects.filter(
            date__gte=today,
        )
        .exclude(
            status=Booking.Status.CANCELLED,
        )
        .count()
    )

    recent_orders = (
        Order.objects.select_related("client")
        .prefetch_related("items__product")
        .order_by("-created_at")[:5]
    )

    upcoming_bookings = (
        Booking.objects.select_related(
            "client",
            "procedure",
        )
        .filter(date__gte=today)
        .exclude(
            status=Booking.Status.CANCELLED,
        )
        .order_by(
            "date",
            "start_time",
        )[:5]
    )

    recent_course_applications = (
        CourseEnrollment.objects.select_related(
            "student",
            "course",
        )
        .order_by("-enrolled_at")[:5]
    )

    context = {
        "form": form,
        "start_date": start_date,
        "end_date": end_date,
        "bookings_count": bookings.count(),
        "completed_bookings_count": (
            completed_bookings.count()
        ),
        "cancelled_bookings_count": (
            bookings.filter(
                status=Booking.Status.CANCELLED,
            ).count()
        ),
        "orders_count": Order.objects.filter(
            created_at__date__range=(
                start_date,
                end_date,
            ),
        ).count(),
        "paid_orders_count": paid_orders.count(),
        "procedure_revenue": procedure_revenue,
        "product_revenue": product_revenue,
        "total_revenue": total_revenue,
        "registered_clients_count": (
            registered_clients_count
        ),
        "cosmetologists_count": cosmetologists_count,
        "unique_booking_clients": (
            unique_booking_clients
        ),
        "pending_orders_count": (
            pending_orders_count
        ),
        "pending_course_applications_count": (
            pending_course_applications_count
        ),
        "upcoming_bookings_count": (
            upcoming_bookings_count
        ),
        "top_procedures": top_procedures,
        "top_products": top_products,
        "recent_orders": recent_orders,
        "upcoming_bookings": upcoming_bookings,
        "recent_course_applications": (
            recent_course_applications
        ),
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )
