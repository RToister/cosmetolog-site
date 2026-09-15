from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CartAddProductForm, CheckoutForm
from .models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)


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

    cart_form = CartAddProductForm(
        product=product,
    )

    context = {
        "product": product,
        "related_products": related_products,
        "is_cosmetologist": is_cosmetologist,
        "cart_form": cart_form,
    }

    return render(
        request,
        "shop/product_detail.html",
        context,
    )


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        get_available_products(request.user),
        pk=product_id,
    )

    form = CartAddProductForm(
        request.POST,
        product=product,
    )

    if form.is_valid():
        cart = Cart(request)

        cart.add(
            product=product,
            quantity=form.cleaned_data["quantity"],
        )

        messages.success(
            request,
            f"Товар «{product.name}» додано до кошика.",
        )

        return redirect("shop:cart-detail")

    messages.error(
        request,
        "Не вдалося додати товар до кошика.",
    )

    return redirect(
        "shop:product-detail",
        pk=product.pk,
    )


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(
        get_available_products(request.user),
        pk=product_id,
    )

    form = CartAddProductForm(
        request.POST,
        product=product,
    )

    if form.is_valid():
        cart = Cart(request)

        cart.add(
            product=product,
            quantity=form.cleaned_data["quantity"],
            override_quantity=True,
        )

        messages.success(
            request,
            "Кількість товару оновлено.",
        )
    else:
        messages.error(
            request,
            "Не вдалося оновити кількість товару.",
        )

    return redirect("shop:cart-detail")


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    cart = Cart(request)
    cart.remove(product)

    messages.success(
        request,
        f"Товар «{product.name}» видалено з кошика.",
    )

    return redirect("shop:cart-detail")


def cart_detail(request):
    cart = Cart(request)
    cart_items = list(cart)

    for item in cart_items:
        item["update_form"] = CartAddProductForm(
            product=item["product"],
            initial={
                "quantity": item["quantity"],
            },
        )

    context = {
        "cart": cart,
        "cart_items": cart_items,
    }

    return render(
        request,
        "shop/cart_detail.html",
        context,
    )


def checkout(request):
    cart = Cart(request)
    cart_items = list(cart)

    if not cart_items:
        messages.warning(
            request,
            "Ваш кошик порожній.",
        )

        return redirect("shop:product-list")

    form = CheckoutForm(
        request.POST or None,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        for item in cart_items:
            product = item["product"]

            if item["quantity"] > product.stock_quantity:
                messages.error(
                    request,
                    (
                        f"Недостатньо товару "
                        f"«{product.name}» на складі."
                    ),
                )

                return redirect("shop:cart-detail")

        with transaction.atomic():
            order = Order.objects.create(
                client=(
                    request.user
                    if request.user.is_authenticated
                    else None
                ),
                client_name=form.cleaned_data[
                    "client_name"
                ],
                client_phone=form.cleaned_data[
                    "client_phone"
                ],
                source=Order.Source.ONLINE,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                )

        cart.clear()

        request.session["last_order_id"] = order.pk

        return redirect(
            "shop:order-success",
            order_id=order.pk,
        )

    context = {
        "form": form,
        "cart": cart,
        "cart_items": cart_items,
    }

    return render(
        request,
        "shop/checkout.html",
        context,
    )


def order_success(request, order_id):
    last_order_id = request.session.get(
        "last_order_id"
    )

    if last_order_id != order_id:
        raise Http404(
            "Замовлення не знайдено."
        )

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product"
        ),
        pk=order_id,
    )

    return render(
        request,
        "shop/order_success.html",
        {"order": order},
    )
