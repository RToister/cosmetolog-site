from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from services.models import Procedure

from .models import Booking, VisitComment


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
                    "placeholder": (
                        "Ваші побажання або "
                        "додаткова інформація"
                    ),
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        self.fields["procedure"].queryset = (
            Procedure.objects.filter(
                is_active=True,
            )
            .select_related("category")
            .order_by(
                "category__name",
                "name",
            )
        )

        self.fields["procedure"].empty_label = (
            "Оберіть процедуру"
        )
        self.fields["start_time"].choices = [
            (
                "",
                "Спочатку оберіть процедуру та дату",
            )
        ]

        self.fields["date"].widget.attrs["min"] = (
            date.today().isoformat()
        )

        if user and user.is_authenticated:
            self.fields["client_name"].initial = (
                    user.get_full_name()
                    or user.username
            )
            self.fields["client_phone"].initial = (
                user.phone_number
            )

        for field_name, field in self.fields.items():
            if field_name in (
                    "procedure",
                    "start_time",
            ):
                field.widget.attrs["class"] = (
                    "form-select"
                )
            else:
                field.widget.attrs["class"] = (
                    "form-control"
                )

        if self.is_bound:
            selected_time = self.data.get(
                "start_time"
            )

            if selected_time:
                self.fields[
                    "start_time"
                ].choices = [
                    (
                        selected_time,
                        selected_time,
                    )
                ]

    def clean_client_name(self):
        client_name = self.cleaned_data[
            "client_name"
        ].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити "
                "щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        client_phone = self.cleaned_data[
            "client_phone"
        ].strip()

        allowed_characters = "+0123456789 ()-"

        if any(
                character not in allowed_characters
                for character in client_phone
        ):
            raise ValidationError(
                "Номер телефону містить "
                "недопустимі символи."
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
                "Неможливо створити запис "
                "на минулу дату."
            )

        return booking_date


class StaffBookingForm(forms.ModelForm):
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
                    "class": "form-control",
                    "autocomplete": "name",
                    "placeholder": "Ім’я клієнта",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "tel",
                    "placeholder": "+380XXXXXXXXX",
                }
            ),
            "procedure": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "start_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "class": "form-control",
                    "type": "time",
                    "step": "1800",
                },
            ),
            "client_note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Коментар або побажання клієнта"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["procedure"].queryset = (
            Procedure.objects.filter(
                is_active=True,
            )
            .select_related("category")
            .order_by(
                "category__name",
                "name",
            )
        )

        self.fields["procedure"].empty_label = (
            "Оберіть процедуру"
        )
        self.fields["date"].widget.attrs["min"] = (
            date.today().isoformat()
        )

    def clean_client_name(self):
        client_name = self.cleaned_data[
            "client_name"
        ].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити "
                "щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        phone_number = self.cleaned_data[
            "client_phone"
        ].strip()

        allowed_characters = "+0123456789 ()-"

        if any(
                character not in allowed_characters
                for character in phone_number
        ):
            raise ValidationError(
                "Номер телефону містить "
                "недопустимі символи."
            )

        digits = "".join(
            character
            for character in phone_number
            if character.isdigit()
        )

        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                "Введіть коректний номер телефону."
            )

        return phone_number

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < date.today():
            raise ValidationError(
                "Неможливо перенести запис "
                "на минулу дату."
            )

        return booking_date


class VisitCommentForm(forms.ModelForm):
    class Meta:
        model = VisitComment
        fields = (
            "comment",
            "recommendations",
        )
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Результат огляду або "
                        "коментар після процедури"
                    ),
                }
            ),
            "recommendations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Рекомендації щодо догляду"
                    ),
                }
            ),
        }
