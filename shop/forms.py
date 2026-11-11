from django import forms
from django.core.exceptions import ValidationError

from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        label="Кількість",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
            }
        ),
    )

    def __init__(
        self,
        *args,
        product,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.product = product

        self.fields["quantity"].widget.attrs["max"] = product.stock_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]

        if self.product.stock_quantity < 1:
            raise ValidationError("Товару наразі немає " "в наявності.")

        if quantity > self.product.stock_quantity:
            raise ValidationError(
                "Обрана кількість перевищує " "залишок товару на складі."
            )

        return quantity


class CheckoutForm(forms.Form):
    client_name = forms.CharField(
        label="Ваше ім’я",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": ("Введіть ваше ім’я"),
                "autocomplete": "name",
            }
        ),
    )

    client_phone = forms.CharField(
        label="Номер телефону",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": ("+380991112233"),
                "autocomplete": "tel",
            }
        ),
    )

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if user and user.is_authenticated:
            self.fields["client_name"].initial = (
                user.get_full_name() or user.username
            )

            self.fields["client_phone"].initial = user.phone_number

    def clean_client_name(self):
        client_name = self.cleaned_data["client_name"].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити " "щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        return normalize_phone_number(self.cleaned_data["client_phone"])
