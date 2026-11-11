"""Brand illustrations used when an item has no uploaded photo.

All files live in ``static/img`` and share one visual style. Items are matched
by keywords in their name; the first matching rule wins.
"""

PRODUCT_RULES = (
    (("spf", "сонцезахис"), "img/product-spf.svg"),
    (("маск",), "img/product-mask.svg"),
    (("сироват", "serum", "ампул"), "img/product-serum.svg"),
    (("гель", "пінк", "очищ", "тонік", "міцеляр"), "img/product-gel.svg"),
    (("крем", "бальзам"), "img/product-cream.svg"),
)

PROCEDURE_RULES = (
    (("консультац", "діагност"), "img/procedure-consultation.svg"),
    (("мезо", "біоревіталіз"), "img/procedure-mesotherapy.svg"),
    (("ботул", "ін’єкц", "ін'єкц", "філер", "контур"),
     "img/procedure-injection.svg"),
    (("пілінг",), "img/procedure-peeling.svg"),
    (("чистк",), "img/procedure-cleansing.svg"),
)


def match_illustration(text, rules, default):
    text = (text or "").lower()

    for keywords, path in rules:
        if any(keyword in text for keyword in keywords):
            return path

    return default


def product_illustration(product):
    default = (
        "img/product-pro.svg"
        if product.availability == "professionals_only"
        else "img/product-default.svg"
    )

    return match_illustration(product.name, PRODUCT_RULES, default)


def procedure_illustration(procedure):
    return match_illustration(
        f"{procedure.name} {procedure.category.name}",
        PROCEDURE_RULES,
        "img/procedure-care.svg",
    )


def course_illustration(course):
    if course.audience == "cosmetologists":
        return "img/course-pro.svg"

    return "img/course-care.svg"
