from django import forms

from academy.models import CourseEnrollment
from appointments.models import Booking
from shop.models import Order


class BookingStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус запису",
        choices=Booking.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус замовлення",
        choices=Order.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    payment_method = forms.ChoiceField(
        label="Спосіб оплати",
        choices=(
            ("", "Не вибрано"),
            *Order.PaymentMethod.choices,
        ),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        payment_method = cleaned_data.get("payment_method")

        if status == Order.Status.PAID and not payment_method:
            self.add_error(
                "payment_method",
                ("Для оплаченого замовлення " "оберіть спосіб оплати."),
            )

        return cleaned_data


class CourseApplicationStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус заявки",
        choices=CourseEnrollment.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
