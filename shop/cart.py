from decimal import Decimal

from .models import Product

CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.user = request.user

        cart = self.session.get(CART_SESSION_ID)

        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}

        self.cart = cart

    @property
    def user_has_professional_access(self):
        return bool(
            self.user.is_authenticated
            and self.user.can_buy_professional_products
        )

    def add(
        self,
        product,
        quantity=1,
        override_quantity=False,
    ):
        product_id = str(product.pk)

        if product_id not in self.cart:
            self.cart[product_id] = {
                "quantity": 0,
            }

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = self.cart[product_id]["quantity"] + quantity

        self.cart[product_id]["quantity"] = min(
            new_quantity,
            product.stock_quantity,
        )

        if self.cart[product_id]["quantity"] < 1:
            del self.cart[product_id]

        self.save()

    def remove(self, product):
        product_id = str(product.pk)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.cart = self.session[CART_SESSION_ID]
        self.save()

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def __iter__(self):
        product_ids = list(self.cart.keys())

        products = Product.objects.filter(
            pk__in=product_ids,
            is_active=True,
        ).select_related("category")

        if not self.user_has_professional_access:
            products = products.filter(
                availability=(Product.Availability.PUBLIC),
                retail_price__isnull=False,
            )

        products_by_id = {str(product.pk): product for product in products}

        invalid_product_ids = set(self.cart.keys()) - set(
            products_by_id.keys()
        )

        for product_id in invalid_product_ids:
            del self.cart[product_id]

        if invalid_product_ids:
            self.save()

        for product_id in list(self.cart.keys()):
            product = products_by_id.get(product_id)

            if product is None:
                continue

            cart_item = self.cart[product_id].copy()

            quantity = cart_item.get(
                "quantity",
                0,
            )

            if quantity < 1:
                del self.cart[product_id]
                self.save()
                continue

            if quantity > product.stock_quantity:
                quantity = product.stock_quantity
                self.cart[product_id]["quantity"] = quantity
                self.save()

            if quantity < 1:
                del self.cart[product_id]
                self.save()
                continue

            if self.user_has_professional_access:
                price = product.professional_price
            else:
                price = product.retail_price

            cart_item["quantity"] = quantity
            cart_item["product"] = product
            cart_item["price"] = price
            cart_item["total_price"] = price * quantity

            yield cart_item

    def get_total_price(self):
        return sum(
            (item["total_price"] for item in self),
            Decimal("0.00"),
        )

    def is_empty(self):
        return len(self.cart) == 0
