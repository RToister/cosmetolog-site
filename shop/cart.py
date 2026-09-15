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
    def user_is_cosmetologist(self):
        return (
                self.user.is_authenticated
                and self.user.user_type == "cosmetologist"
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
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        if (
                self.cart[product_id]["quantity"]
                > product.stock_quantity
        ):
            self.cart[product_id]["quantity"] = (
                product.stock_quantity
            )

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
        return sum(
            item["quantity"]
            for item in self.cart.values()
        )

    def __iter__(self):
        product_ids = self.cart.keys()

        products = Product.objects.filter(
            pk__in=product_ids,
            is_active=True,
        ).select_related("category")

        if not self.user_is_cosmetologist:
            products = products.filter(
                availability=Product.Availability.PUBLIC,
                retail_price__isnull=False,
            )

        existing_product_ids = {
            str(product.pk)
            for product in products
        }

        invalid_product_ids = (
                set(self.cart.keys())
                - existing_product_ids
        )

        for product_id in invalid_product_ids:
            del self.cart[product_id]

        if invalid_product_ids:
            self.save()

        for product in products:
            product_id = str(product.pk)
            cart_item = self.cart[product_id].copy()

            if self.user_is_cosmetologist:
                price = product.professional_price
            else:
                price = product.retail_price

            cart_item["product"] = product
            cart_item["price"] = price
            cart_item["total_price"] = (
                    price * cart_item["quantity"]
            )

            yield cart_item

    def get_total_price(self):
        return sum(
            (
                item["total_price"]
                for item in self
            ),
            Decimal("0.00"),
        )

    def is_empty(self):
        return len(self.cart) == 0
