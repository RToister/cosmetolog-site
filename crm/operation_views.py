from datetime import date
from decimal import Decimal

from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.core.paginator import Paginator
from django.db.models import (
    Count,
    DecimalField,
    Q,
    Sum,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render

from academy.models import (
    Course,
    CourseEnrollment,
)
from appointments.models import Booking
from shop.models import Order

MONEY_FIELD = DecimalField(
    max_digits=12,
    decimal_places=2,
)

ITEMS_PER_PAGE = 25


def parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def get_pagination_query(request):
    query = request.GET.copy()
    query.pop("page", None)

    return query.urlencode()


def paginate(request, queryset):
    paginator = Paginator(
        queryset,
        ITEMS_PER_PAGE,
    )

    return paginator.get_page(request.GET.get("page"))


def get_common_filters(request):
    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    )

    date_from_value = request.GET.get(
        "date_from",
        "",
    )

    date_to_value = request.GET.get(
        "date_to",
        "",
    )

    sort = request.GET.get(
        "sort",
        "newest",
    )

    if sort not in (
        "newest",
        "oldest",
    ):
        sort = "newest"

    return {
        "search_query": search_query,
        "status": status,
        "date_from": parse_date(date_from_value),
        "date_to": parse_date(date_to_value),
        "date_from_value": date_from_value,
        "date_to_value": date_to_value,
        "sort": sort,
    }


@staff_member_required
def booking_list(request):
    filters = get_common_filters(request)

    valid_statuses = {value for value, label in Booking.Status.choices}

    if filters["status"] not in valid_statuses:
        filters["status"] = ""

    bookings = Booking.objects.select_related(
        "procedure",
        "client",
        "customer",
        "created_by",
    )

    if filters["search_query"]:
        search_query = filters["search_query"]

        bookings = bookings.filter(
            Q(client_name__icontains=(search_query))
            | Q(client_phone__icontains=(search_query))
            | Q(procedure__name__icontains=(search_query))
        )

    if filters["status"]:
        bookings = bookings.filter(
            status=filters["status"],
        )

    if filters["date_from"]:
        bookings = bookings.filter(
            date__gte=filters["date_from"],
        )

    if filters["date_to"]:
        bookings = bookings.filter(
            date__lte=filters["date_to"],
        )

    if filters["sort"] == "oldest":
        bookings = bookings.order_by(
            "date",
            "start_time",
            "pk",
        )
    else:
        bookings = bookings.order_by(
            "-date",
            "-start_time",
            "-pk",
        )

    statistics = bookings.aggregate(
        total=Count("id"),
        completed=Count(
            "id",
            filter=Q(
                status=Booking.Status.COMPLETED,
            ),
        ),
        pending=Count(
            "id",
            filter=Q(
                status=Booking.Status.PENDING,
            ),
        ),
        total_value=Coalesce(
            Sum("price_at_booking"),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    context = {
        "operation_type": "bookings",
        "active_crm_section": "bookings",
        "page_title": "Записи на послуги",
        "page_description": (
            "Усі записи на процедури незалежно " "від конкретного клієнта."
        ),
        "page_obj": paginate(
            request,
            bookings,
        ),
        "statistics": statistics,
        "status_choices": Booking.Status.choices,
        "pagination_query": (get_pagination_query(request)),
        **filters,
    }

    return render(
        request,
        "crm/operation_list.html",
        context,
    )


@staff_member_required
def order_list(request):
    filters = get_common_filters(request)

    valid_statuses = {value for value, label in Order.Status.choices}

    if filters["status"] not in valid_statuses:
        filters["status"] = ""

    orders = (
        Order.objects.select_related(
            "client",
            "customer",
            "created_by",
        )
        .prefetch_related(
            "items",
            "items__product",
        )
        .annotate(
            item_count=Count(
                "items",
                distinct=True,
            )
        )
    )

    if filters["search_query"]:
        search_query = filters["search_query"]

        orders = orders.filter(
            Q(client_name__icontains=(search_query))
            | Q(client_phone__icontains=(search_query))
            | Q(items__product__name__icontains=(search_query))
        ).distinct()

    if filters["status"]:
        orders = orders.filter(
            status=filters["status"],
        )

    if filters["date_from"]:
        orders = orders.filter(
            created_at__date__gte=(filters["date_from"]),
        )

    if filters["date_to"]:
        orders = orders.filter(
            created_at__date__lte=(filters["date_to"]),
        )

    if filters["sort"] == "oldest":
        orders = orders.order_by(
            "created_at",
            "pk",
        )
    else:
        orders = orders.order_by(
            "-created_at",
            "-pk",
        )

    statistics = orders.aggregate(
        total=Count(
            "id",
            distinct=True,
        ),
        paid=Count(
            "id",
            filter=Q(
                status=Order.Status.PAID,
            ),
            distinct=True,
        ),
        pending=Count(
            "id",
            filter=Q(
                status=Order.Status.PENDING,
            ),
            distinct=True,
        ),
        total_value=Coalesce(
            Sum(
                "total_price",
                distinct=True,
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    context = {
        "operation_type": "orders",
        "active_crm_section": "orders",
        "page_title": "Замовлення товарів",
        "page_description": (
            "Усі замовлення магазину, товари, " "суми та статуси оплати."
        ),
        "page_obj": paginate(
            request,
            orders,
        ),
        "statistics": statistics,
        "status_choices": Order.Status.choices,
        "pagination_query": (get_pagination_query(request)),
        **filters,
    }

    return render(
        request,
        "crm/operation_list.html",
        context,
    )


@staff_member_required
def course_application_list(request):
    filters = get_common_filters(request)

    audience = request.GET.get(
        "audience",
        "",
    )

    valid_statuses = {
        value for value, label in CourseEnrollment.Status.choices
    }

    valid_audiences = {value for value, label in Course.Audience.choices}

    if filters["status"] not in valid_statuses:
        filters["status"] = ""

    if audience not in valid_audiences:
        audience = ""

    applications = CourseEnrollment.objects.select_related(
        "course",
        "student",
        "customer",
        "created_by",
    )

    if filters["search_query"]:
        search_query = filters["search_query"]

        applications = applications.filter(
            Q(applicant_name__icontains=(search_query))
            | Q(applicant_phone__icontains=(search_query))
            | Q(course__title__icontains=(search_query))
        )

    if filters["status"]:
        applications = applications.filter(
            status=filters["status"],
        )

    if audience:
        applications = applications.filter(
            course__audience=audience,
        )

    if filters["date_from"]:
        applications = applications.filter(
            enrolled_at__date__gte=(filters["date_from"]),
        )

    if filters["date_to"]:
        applications = applications.filter(
            enrolled_at__date__lte=(filters["date_to"]),
        )

    if filters["sort"] == "oldest":
        applications = applications.order_by(
            "enrolled_at",
            "pk",
        )
    else:
        applications = applications.order_by(
            "-enrolled_at",
            "-pk",
        )

    statistics = applications.aggregate(
        total=Count("id"),
        completed=Count(
            "id",
            filter=Q(
                status=(CourseEnrollment.Status.COMPLETED),
            ),
        ),
        pending=Count(
            "id",
            filter=Q(
                status=(CourseEnrollment.Status.PENDING),
            ),
        ),
        total_value=Coalesce(
            Sum("price_at_enrollment"),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    context = {
        "operation_type": "courses",
        "active_crm_section": "courses",
        "page_title": "Заявки на навчання",
        "page_description": (
            "Усі заявки до Школи догляду " "та на підвищення кваліфікації."
        ),
        "page_obj": paginate(
            request,
            applications,
        ),
        "statistics": statistics,
        "status_choices": (CourseEnrollment.Status.choices),
        "audience_choices": Course.Audience.choices,
        "selected_audience": audience,
        "pagination_query": (get_pagination_query(request)),
        **filters,
    }

    return render(
        request,
        "crm/operation_list.html",
        context,
    )
