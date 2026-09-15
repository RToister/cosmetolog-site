from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from services.models import Procedure

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = (
            "client_name",
            "client_phone",
            "procedure",
            "date",
            "start_time",
            "client_note",
        )
        widgets = {
            "client_name": forms.TextInput(
                attrs={
                    "placeholder": "Введіть ваше ім’я",
                    "autocomplete": "name",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "placeholder": "+380XXXXXXXXX",
                    "autocomplete": "tel",
                }
            ),
            "procedure": forms.Select(),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "start_time": forms.Select(),
            "client_note": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Ваші побажання або додаткова інформація",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        self.fields["procedure"].queryset = (
            Procedure.objects.filter(is_active=True)
            .select_related("category")
            .order_by("category__name", "name")
        )

        self.fields["procedure"].empty_label = "Оберіть процедуру"
        self.fields["start_time"].choices = [
            ("", "Спочатку оберіть процедуру та дату")
        ]

        self.fields["date"].widget.attrs["min"] = date.today().isoformat()

        if user and user.is_authenticated:
            self.fields["client_name"].initial = (
                    user.get_full_name() or user.username
            )
            self.fields["client_phone"].initial = user.phone_number

        for field_name, field in self.fields.items():
            if field_name in ("procedure", "start_time"):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        if self.is_bound:
            selected_time = self.data.get("start_time")

            if selected_time:
                self.fields["start_time"].choices = [
                    (selected_time, selected_time)
                ]

    def clean_client_name(self):
        client_name = self.cleaned_data["client_name"].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        client_phone = self.cleaned_data["client_phone"].strip()

        allowed_characters = "+0123456789 ()-"

        if any(
                character not in allowed_characters
                for character in client_phone
        ):
            raise ValidationError(
                "Номер телефону містить недопустимі символи."
            )

        digits = "".join(
            character
            for character in client_phone
            if character.isdigit()
        )

        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                "Введіть коректний номер телефону."
            )

        return client_phone

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < date.today():
            raise ValidationError(
                "Неможливо створити запис на минулу дату."
            )

        return booking_date
