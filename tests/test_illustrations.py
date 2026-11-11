from types import SimpleNamespace

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

from dr_toister_site.illustrations import (
    PROCEDURE_RULES,
    PRODUCT_RULES,
    course_illustration,
    procedure_illustration,
    product_illustration,
)


class IllustrationTests(SimpleTestCase):
    def test_all_illustration_files_exist(self):
        paths = {path for _, path in PRODUCT_RULES + PROCEDURE_RULES}
        paths |= {
            "img/product-default.svg",
            "img/product-pro.svg",
            "img/procedure-care.svg",
            "img/course-care.svg",
            "img/course-pro.svg",
            "img/hero.svg",
            "img/doctor.svg",
        }

        for path in paths:
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))

    def test_product_matched_by_name(self):
        product = SimpleNamespace(
            name="Сонцезахисний крем SPF 50",
            availability="public",
        )

        self.assertEqual(
            product_illustration(product),
            "img/product-spf.svg",
        )

    def test_professional_product_default(self):
        product = SimpleNamespace(
            name="Невідомий препарат",
            availability="professionals_only",
        )

        self.assertEqual(
            product_illustration(product),
            "img/product-pro.svg",
        )

    def test_procedure_matched_by_category(self):
        procedure = SimpleNamespace(
            name="Корекція",
            category=SimpleNamespace(name="Ін’єкційна косметологія"),
        )

        self.assertEqual(
            procedure_illustration(procedure),
            "img/procedure-injection.svg",
        )

    def test_course_by_audience(self):
        course = SimpleNamespace(audience="cosmetologists")

        self.assertEqual(course_illustration(course), "img/course-pro.svg")
