from django.db.models import Prefetch
from django.shortcuts import render

from academy.models import Course
from services.models import (
    Procedure,
    ProcedureCategory,
)
from shop.models import Product


def home(request):
    procedures = (
        Procedure.objects.filter(
            is_active=True,
        )
        .select_related("category")
        .order_by(
            "category__name",
            "name",
        )[:6]
    )

    public_courses = (
        Course.objects.filter(
            is_published=True,
            audience=Course.Audience.EVERYONE,
        )
        .order_by(
            "start_date",
            "title",
        )[:3]
    )

    professional_courses = (
        Course.objects.filter(
            is_published=True,
            audience=(
                Course.Audience.COSMETOLOGISTS
            ),
        )
        .order_by(
            "start_date",
            "title",
        )[:3]
    )

    products = (
        Product.objects.filter(
            is_active=True,
            availability=(
                Product.Availability.PUBLIC
            ),
        )
        .select_related("category")
        .order_by("name")[:4]
    )

    return render(
        request,
        "home.html",
        {
            "procedures": procedures,
            "public_courses": public_courses,
            "professional_courses": (
                professional_courses
            ),
            "products": products,
        },
    )


def about(request):
    return render(
        request,
        "about.html",
    )


def service_list(request):
    active_procedures = (
        Procedure.objects.filter(
            is_active=True,
        )
        .select_related("category")
        .order_by("name")
    )

    categories = (
        ProcedureCategory.objects.filter(
            procedures__is_active=True,
        )
        .distinct()
        .order_by("name")
        .prefetch_related(
            Prefetch(
                "procedures",
                queryset=active_procedures,
                to_attr="active_procedures",
            )
        )
    )

    return render(
        request,
        "services.html",
        {
            "categories": categories,
        },
    )


def results(request):
    return render(
        request,
        "results.html",
    )
