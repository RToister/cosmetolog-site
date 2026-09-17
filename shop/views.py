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

from dr_toister_site.telegram_notifications import (
    notify_order_created,
)

from .cart import Cart
from .forms import (
    CartAddProductForm,
    CheckoutForm,
)
from .models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)


def user_is_cosmetologist(user):
    return bool(user.is_authenticated and user.is_cosmetologist)


def user_has_professional_access(user):
    return bool(user.is_authenticated and user.can_buy_professional_products)


def user_is_awaiting_verification(user):
    return bool(
        user_is_cosmetologist(user) and not user.is_cosmetologist_verified
    )


def product_is_professional(product):
    return product.availability == Product.Availability.PROFESSIONALS_ONLY


def user_can_buy_product(user, product):
    if product_is_professional(product):
        return user_has_professional_access(user)

    return product.retail_price is not None


def get_visible_products():
    return Product.objects.filter(
        is_active=True,
    ).select_related("category")


def get_purchasable_products(user):
    products = get_visible_products()

    if user_has_professional_access(user):
        return products

    return products.filter(
        availability=Product.Availability.PUBLIC,
        retail_price__isnull=False,
    )


def set_product_display_data(
    product,
    has_professional_access,
):
    product.is_professional_product = product_is_professional(product)

    product.can_view_price = (
        not product.is_professional_product or has_professional_access
    )

    product.can_purchase = (
        product.can_view_price and product.stock_quantity > 0
    )

    if not product.can_view_price:
        product.display_price = None
    elif has_professional_access:
        product.display_price = product.professional_price
    else:
        product.display_price = product.retail_price


def get_access_context(user):
    return {
        "is_cosmetologist": (user_is_cosmetologist(user)),
        "has_professional_access": (user_has_professional_access(user)),
        "is_awaiting_verification": (user_is_awaiting_verification(user)),
    }


def product_list(request):
    access_context = get_access_context(request.user)

    products = get_visible_products().order_by(
        "availability",
        "category__name",
        "name",
    )

    selected_group = request.GET.get(
        "group",
        "",
    )

    selected_category = request.GET.get(
        "category",
        "",
    )

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    valid_groups = {
        Product.Availability.PUBLIC,
        Product.Availability.PROFESSIONALS_ONLY,
    }

    if selected_group in valid_groups:
        products = products.filter(
            availability=selected_group,
        )
    else:
        selected_group = ""

    if selected_category:
        products = products.filter(
            category_id=selected_category,
        )

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=(search_query))
            | Q(usage_recommendations__icontains=(search_query))
            | Q(category__name__icontains=(search_query))
            | Q(sku__icontains=search_query)
        )

    paginator = Paginator(
        products,
        9,
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    for product in page_obj:
        set_product_display_data(
            product,
            access_context["has_professional_access"],
        )

    categories = (
        ProductCategory.objects.filter(
            products__is_active=True,
        )
        .distinct()
        .order_by("name")
    )

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "selected_group": selected_group,
        "selected_category": selected_category,
        "search_query": search_query,
        **access_context,
    }

    return render(
        request,
        "shop/product_list.html",
        context,
    )


def product_detail(request, pk):
    access_context = get_access_context(request.user)

    product = get_object_or_404(
        get_visible_products(),
        pk=pk,
    )

    set_product_display_data(
        product,
        access_context["has_professional_access"],
    )

    related_products = list(
        get_visible_products()
        .filter(
            availability=product.availability,
        )
        .exclude(pk=product.pk)
        .order_by("name")[:3]
    )

    for related_product in related_products:
        set_product_display_data(
            related_product,
            access_context["has_professional_access"],
        )

    cart_form = None

    if product.can_purchase:
        cart_form = CartAddProductForm(
            product=product,
        )

    context = {
        "product": product,
        "related_products": related_products,
        "cart_form": cart_form,
        **access_context,
    }

    return render(
        request,
        "shop/product_detail.html",
        context,
    )


def add_access_denied_message(request):
    if not request.user.is_authenticated:
        messages.warning(
            request,
            (
                "Увійдіть або зареєструйтеся "
                "як косметолог. Професійний доступ "
                "відкривається після підтвердження."
            ),
        )
    elif user_is_awaiting_verification(request.user):
        messages.warning(
            request,
            (
                "Ваш обліковий запис косметолога "
                "очікує підтвердження. Перевірка "
                "зазвичай займає до 24 годин."
            ),
        )
    else:
        messages.warning(
            request,
            (
                "Професійні препарати доступні "
                "для придбання лише підтвердженим "
                "косметологам."
            ),
        )


@require_POST
def cart_add(request, product_id):
    visible_product = get_object_or_404(
        get_visible_products(),
        pk=product_id,
    )

    if not user_can_buy_product(
        request.user,
        visible_product,
    ):
        add_access_denied_message(request)

        return redirect(
            "shop:product-detail",
            pk=visible_product.pk,
        )

    product = get_object_or_404(
        get_purchasable_products(request.user),
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
            quantity=(form.cleaned_data["quantity"]),
        )

        messages.success(
            request,
            (f"Товар «{product.name}» " f"додано до кошика."),
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
    visible_product = get_object_or_404(
        get_visible_products(),
        pk=product_id,
    )

    if not user_can_buy_product(
        request.user,
        visible_product,
    ):
        cart = Cart(request)
        cart.remove(visible_product)

        add_access_denied_message(request)

        return redirect("shop:cart-detail")

    product = get_object_or_404(
        get_purchasable_products(request.user),
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
            quantity=(form.cleaned_data["quantity"]),
            override_quantity=True,
        )

        messages.success(
            request,
            "Кількість товару оновлено.",
        )
    else:
        messages.error(
            request,
            ("Не вдалося оновити " "кількість товару."),
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
        (f"Товар «{product.name}» " f"видалено з кошика."),
    )

    return redirect("shop:cart-detail")


def cart_detail(request):
    cart = Cart(request)
    cart_items = list(cart)

    restricted_products = []

    for item in cart_items:
        product = item["product"]

        if not user_can_buy_product(
            request.user,
            product,
        ):
            restricted_products.append(product)
            continue

        item["update_form"] = CartAddProductForm(
            product=product,
            initial={
                "quantity": (item["quantity"]),
            },
        )

    if restricted_products:
        for product in restricted_products:
            cart.remove(product)

        add_access_denied_message(request)

        return redirect("shop:cart-detail")

    return render(
        request,
        "shop/cart_detail.html",
        {
            "cart": cart,
            "cart_items": cart_items,
        },
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

    for item in cart_items:
        product = item["product"]

        if not user_can_buy_product(
            request.user,
            product,
        ):
            cart.remove(product)
            add_access_denied_message(request)

            return redirect("shop:cart-detail")

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
                    ("Недостатньо товару " f"«{product.name}» " "на складі."),
                )

                return redirect("shop:cart-detail")

        with transaction.atomic():
            order = Order.objects.create(
                client=(
                    request.user if request.user.is_authenticated else None
                ),
                client_name=(form.cleaned_data["client_name"]),
                client_phone=(form.cleaned_data["client_phone"]),
                source=Order.Source.ONLINE,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                )

        transaction.on_commit(
            lambda order_id=order.pk: (notify_order_created(order_id))
        )

        cart.clear()

        request.session["last_order_id"] = order.pk

        return redirect(
            "shop:order-success",
            order_id=order.pk,
        )

    return render(
        request,
        "shop/checkout.html",
        {
            "form": form,
            "cart": cart,
            "cart_items": cart_items,
        },
    )


def order_success(request, order_id):
    last_order_id = request.session.get("last_order_id")

    if last_order_id != order_id:
        raise Http404("Замовлення не знайдено.")

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=order_id,
    )

    return render(
        request,
        "shop/order_success.html",
        {
            "order": order,
        },
    )
