from django import forms
from django.utils import timezone

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
        labels = {
            "client_name": "Ім’я",
            "client_phone": "Номер телефону",
            "procedure": "Процедура",
            "date": "Дата",
            "start_time": "Час",
            "client_note": "Коментар",
        }
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "step": "1800",
                },
            ),
            "client_note": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Необов’язково",
                },
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        self.fields["procedure"].queryset = (
            Procedure.objects.filter(is_active=True)
            .select_related("category")
        )

        self.fields["date"].widget.attrs["min"] = (
            timezone.localdate().isoformat()
        )

        if user and user.is_authenticated:
            self.fields["client_name"].initial = (
                    user.get_full_name() or user.username
            )
            self.fields["client_phone"].initial = (
                user.phone_number
            )

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < timezone.localdate():
            raise forms.ValidationError(
                "Не можна створити запис на минулу дату."
            )

        return booking_date

    def clean_client_name(self):
        client_name = self.cleaned_data["client_name"].strip()

        if len(client_name) < 2:
            raise forms.ValidationError(
                "Вкажіть коректне ім’я."
            )

        return client_name

    def clean_client_phone(self):
        phone_number = self.cleaned_data["client_phone"].strip()

        allowed_characters = set("+0123456789 ()-")

        if not phone_number:
            raise forms.ValidationError(
                "Вкажіть номер телефону."
            )

        if not set(phone_number).issubset(allowed_characters):
            raise forms.ValidationError(
                "Номер телефону містить недопустимі символи."
            )

        digits = "".join(
            character
            for character in phone_number
            if character.isdigit()
        )

        if len(digits) < 9 or len(digits) > 15:
            raise forms.ValidationError(
                "Вкажіть коректний номер телефону."
            )

        return phone_number
