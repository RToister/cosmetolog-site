from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Product, ProductCategory


def user_is_cosmetologist(user):
    return (
            user.is_authenticated
            and user.user_type == "cosmetologist"
    )


def get_available_products(user):
    products = Product.objects.filter(
        is_active=True,
    ).select_related("category")

    if not user_is_cosmetologist(user):
        products = products.filter(
            availability=Product.Availability.PUBLIC,
            retail_price__isnull=False,
        )

    return products


def set_display_price(product, is_cosmetologist):
    if is_cosmetologist:
        product.display_price = (
            product.professional_price
        )
    else:
        product.display_price = product.retail_price


def product_list(request):
    is_cosmetologist = user_is_cosmetologist(
        request.user
    )

    products = get_available_products(
        request.user
    ).order_by(
        "category__name",
        "name",
    )

    selected_category = request.GET.get(
        "category",
        "",
    )
    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    if selected_category:
        products = products.filter(
            category_id=selected_category,
        )

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(
                usage_recommendations__icontains=(
                    search_query
                )
            )
            | Q(category__name__icontains=search_query)
            | Q(sku__icontains=search_query)
        )

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for product in page_obj:
        set_display_price(
            product,
            is_cosmetologist,
        )

    categories = ProductCategory.objects.order_by(
        "name"
    )

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
        "is_cosmetologist": is_cosmetologist,
    }

    return render(
        request,
        "shop/product_list.html",
        context,
    )


def product_detail(request, pk):
    is_cosmetologist = user_is_cosmetologist(
        request.user
    )

    available_products = get_available_products(
        request.user
    )

    product = get_object_or_404(
        available_products,
        pk=pk,
    )

    set_display_price(
        product,
        is_cosmetologist,
    )

    related_products = list(
        available_products.filter(
            category=product.category,
        )
        .exclude(pk=product.pk)
        .order_by("name")[:3]
    )

    for related_product in related_products:
        set_display_price(
            related_product,
            is_cosmetologist,
        )

    context = {
        "product": product,
        "related_products": related_products,
        "is_cosmetologist": is_cosmetologist,
    }

    return render(
        request,
        "shop/product_detail.html",
        context,
    )
