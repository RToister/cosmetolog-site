from .cart import Cart


def cart(request):
    return {
        "global_cart": Cart(request),
    }
