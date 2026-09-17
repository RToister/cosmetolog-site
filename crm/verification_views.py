from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.http import HttpResponseRedirect
from django.shortcuts import (
    get_object_or_404,
)
from django.urls import reverse
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)
from django.views.decorators.http import require_POST

from accounts.models import User
from crm.models import Customer


def get_safe_next_url(request, customer):
    next_url = request.POST.get(
        "next",
        "",
    )

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={
            request.get_host(),
        },
        require_https=request.is_secure(),
    ):
        return next_url

    return reverse(
        "crm:customer-detail",
        kwargs={
            "pk": customer.pk,
        },
    )


@staff_member_required
@require_POST
def verify_cosmetologist(request, pk):
    customer = get_object_or_404(
        Customer.objects.select_related("user"),
        pk=pk,
    )

    redirect_url = get_safe_next_url(
        request,
        customer,
    )

    if customer.user_id is None:
        messages.error(
            request,
            (
                "Підтвердити косметолога неможливо: "
                "клієнт не має пов’язаного "
                "облікового запису."
            ),
        )

        return HttpResponseRedirect(redirect_url)

    if customer.customer_type != Customer.CustomerType.COSMETOLOGIST:
        messages.error(
            request,
            ("Підтвердити можна лише клієнта " "з типом «Косметолог»."),
        )

        return HttpResponseRedirect(redirect_url)

    user = customer.user

    if user.is_cosmetologist_verified:
        messages.info(
            request,
            ("Цього косметолога вже " "підтверджено."),
        )

        return HttpResponseRedirect(redirect_url)

    if not user.is_cosmetologist:
        user.user_type = User.UserType.COSMETOLOGIST

        user.save(update_fields=("user_type",))

    user.verify_cosmetologist(
        verified_by=request.user,
    )

    if customer.customer_type != Customer.CustomerType.COSMETOLOGIST:
        customer.customer_type = Customer.CustomerType.COSMETOLOGIST

        customer.save(
            update_fields=(
                "customer_type",
                "updated_at",
            )
        )

    messages.success(
        request,
        (
            "Косметолога підтверджено. "
            "Тепер йому доступні професійні "
            "ціни та препарати."
        ),
    )

    return HttpResponseRedirect(redirect_url)


@staff_member_required
@require_POST
def revoke_cosmetologist_verification(
    request,
    pk,
):
    customer = get_object_or_404(
        Customer.objects.select_related("user"),
        pk=pk,
    )

    redirect_url = get_safe_next_url(
        request,
        customer,
    )

    if customer.user_id is None:
        messages.error(
            request,
            (
                "Скасувати підтвердження неможливо: "
                "клієнт не має пов’язаного "
                "облікового запису."
            ),
        )

        return HttpResponseRedirect(redirect_url)

    if not customer.user.is_cosmetologist_verified:
        messages.info(
            request,
            ("Цей косметолог не має " "активного підтвердження."),
        )

        return HttpResponseRedirect(redirect_url)

    customer.user.revoke_cosmetologist_verification()

    messages.success(
        request,
        (
            "Підтвердження косметолога скасовано. "
            "Професійні ціни та придбання "
            "препаратів закрито."
        ),
    )

    return HttpResponseRedirect(redirect_url)
