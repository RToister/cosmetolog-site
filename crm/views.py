from decimal import Decimal

from django.contrib import messages
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
from django.http import HttpResponseRedirect
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.http import require_POST

from academy.models import CourseEnrollment
from appointments.models import Booking
from crm.forms import CustomerForm
from crm.models import Customer
from shop.models import Order

MONEY_FIELD = DecimalField(
    max_digits=12,
    decimal_places=2,
)


@staff_member_required
def customer_list(request):
    customer_type = request.GET.get(
        "type",
        "all",
    )
    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    customers = Customer.objects.select_related(
        "user",
    ).annotate(
        booking_count=Count(
            "bookings",
            distinct=True,
        ),
        order_count=Count(
            "orders",
            distinct=True,
        ),
        course_count=Count(
            "course_applications",
            distinct=True,
        ),
        appointment_spending=Coalesce(
            Sum(
                "bookings__price_at_booking",
                filter=Q(
                    bookings__status=(
                        Booking.Status.COMPLETED
                    ),
                ),
                distinct=True,
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
        order_spending=Coalesce(
            Sum(
                "orders__total_price",
                filter=Q(
                    orders__status=Order.Status.PAID,
                ),
                distinct=True,
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
        course_spending=Coalesce(
            Sum(
                "course_applications__price_at_enrollment",
                filter=Q(
                    course_applications__status=(
                        CourseEnrollment.Status.COMPLETED
                    ),
                ),
                distinct=True,
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    if customer_type == "clients":
        customers = customers.filter(
            customer_type=Customer.CustomerType.CLIENT,
        )
    elif customer_type == "cosmetologists":
        customers = customers.filter(
            customer_type=(
                Customer.CustomerType.COSMETOLOGIST
            ),
        )
    else:
        customer_type = "all"

    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query)
            | Q(phone_number__icontains=search_query)
            | Q(user__email__icontains=search_query)
        )

    customers = customers.order_by(
        "-last_activity_at",
        "full_name",
    )

    paginator = Paginator(
        customers,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page"),
    )

    total_customers = Customer.objects.count()

    regular_clients = Customer.objects.filter(
        customer_type=Customer.CustomerType.CLIENT,
    ).count()

    cosmetologists = Customer.objects.filter(
        customer_type=(
            Customer.CustomerType.COSMETOLOGIST
        ),
    ).count()

    context = {
        "page_obj": page_obj,
        "customer_type": customer_type,
        "search_query": search_query,
        "total_customers": total_customers,
        "regular_clients": regular_clients,
        "cosmetologists": cosmetologists,
    }

    return render(
        request,
        "crm/customer_list.html",
        context,
    )


@staff_member_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            customer = form.save()

            messages.success(
                request,
                "Клієнта успішно додано до CRM.",
            )

            return redirect(
                "crm:customer-detail",
                pk=customer.pk,
            )
    else:
        form = CustomerForm()

    return render(
        request,
        "crm/customer_form.html",
        {
            "form": form,
            "page_title": "Новий клієнт",
            "submit_text": "Створити клієнта",
            "cancel_url": reverse(
                "crm:customer-list"
            ),
        },
    )


@staff_member_required
def customer_update(request, pk):
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":
        form = CustomerForm(
            request.POST,
            instance=customer,
        )

        if form.is_valid():
            customer = form.save()

            messages.success(
                request,
                "Дані клієнта успішно оновлено.",
            )

            return redirect(
                "crm:customer-detail",
                pk=customer.pk,
            )
    else:
        form = CustomerForm(
            instance=customer,
        )

    return render(
        request,
        "crm/customer_form.html",
        {
            "form": form,
            "customer": customer,
            "page_title": "Редагування клієнта",
            "submit_text": "Зберегти зміни",
            "cancel_url": reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": customer.pk,
                },
            ),
        },
    )


@staff_member_required
@require_POST
def customer_toggle_active(request, pk):
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    customer.is_active = not customer.is_active

    customer.save(
        update_fields=(
            "is_active",
            "updated_at",
        )
    )

    if customer.is_active:
        message = "Клієнта активовано."
    else:
        message = "Клієнта деактивовано."

    messages.success(
        request,
        message,
    )

    next_url = request.POST.get("next")

    if next_url:
        return HttpResponseRedirect(next_url)

    return redirect(
        "crm:customer-detail",
        pk=customer.pk,
    )


@staff_member_required
def customer_detail(request, pk):
    customer = get_object_or_404(
        Customer.objects.select_related("user"),
        pk=pk,
    )

    bookings = customer.bookings.select_related(
        "procedure",
        "created_by",
    ).order_by(
        "-date",
        "-start_time",
    )

    orders = customer.orders.prefetch_related(
        "items",
        "items__product",
    ).order_by(
        "-created_at",
    )

    course_applications = (
        customer.course_applications.select_related(
            "course",
            "created_by",
        ).order_by(
            "-enrolled_at",
        )
    )

    booking_statistics = bookings.aggregate(
        total=Count("id"),
        completed=Count(
            "id",
            filter=Q(
                status=Booking.Status.COMPLETED,
            ),
        ),
        spending=Coalesce(
            Sum(
                "price_at_booking",
                filter=Q(
                    status=Booking.Status.COMPLETED,
                ),
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    order_statistics = orders.aggregate(
        total=Count("id"),
        paid=Count(
            "id",
            filter=Q(
                status=Order.Status.PAID,
            ),
        ),
        spending=Coalesce(
            Sum(
                "total_price",
                filter=Q(
                    status=Order.Status.PAID,
                ),
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    course_statistics = course_applications.aggregate(
        total=Count("id"),
        completed=Count(
            "id",
            filter=Q(
                status=(
                    CourseEnrollment.Status.COMPLETED
                ),
            ),
        ),
        spending=Coalesce(
            Sum(
                "price_at_enrollment",
                filter=Q(
                    status=(
                        CourseEnrollment.Status.COMPLETED
                    ),
                ),
            ),
            Decimal("0.00"),
            output_field=MONEY_FIELD,
        ),
    )

    total_spending = (
            booking_statistics["spending"]
            + order_statistics["spending"]
            + course_statistics["spending"]
    )

    total_interactions = (
            booking_statistics["total"]
            + order_statistics["total"]
            + course_statistics["total"]
    )

    contact_digits = "".join(
        character
        for character in customer.phone_number
        if character.isdigit()
    )

    context = {
        "customer": customer,
        "bookings": bookings,
        "orders": orders,
        "course_applications": course_applications,
        "booking_statistics": booking_statistics,
        "order_statistics": order_statistics,
        "course_statistics": course_statistics,
        "total_spending": total_spending,
        "total_interactions": total_interactions,
        "contact_digits": contact_digits,
    }

    return render(
        request,
        "crm/customer_detail.html",
        context,
    )
