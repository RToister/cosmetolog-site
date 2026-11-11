from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)
from services.models import Procedure

from .models import (
    Booking,
    VisitComment,
)


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
                    "placeholder": ("Введіть ваше ім’я"),
                    "autocomplete": "name",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "placeholder": ("+380991112233"),
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
                        "Ваші побажання або " "додаткова інформація"
                    ),
                }
            ),
        }

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

        self.fields["procedure"].empty_label = "Оберіть процедуру"

        self.fields["start_time"].choices = [
            (
                "",
                ("Спочатку оберіть " "процедуру та дату"),
            )
        ]

        self.fields["date"].widget.attrs[
            "min"
        ] = timezone.localdate().isoformat()

        if user and user.is_authenticated:
            self.fields["client_name"].initial = (
                user.get_full_name() or user.username
            )

            self.fields["client_phone"].initial = user.phone_number

        for field_name, field in self.fields.items():
            if field_name in (
                "procedure",
                "start_time",
            ):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        if self.is_bound:
            selected_time = self.data.get("start_time")

            if selected_time:
                self.fields["start_time"].choices = [
                    (
                        selected_time,
                        selected_time,
                    )
                ]

    def clean_client_name(self):
        client_name = self.cleaned_data["client_name"].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити " "щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        return normalize_phone_number(self.cleaned_data["client_phone"])

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < timezone.localdate():
            raise ValidationError(
                "Неможливо створити запис " "на минулу дату."
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
                    "placeholder": ("Ім’я клієнта"),
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "tel",
                    "placeholder": ("+380991112233"),
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
                    "placeholder": ("Коментар або " "побажання клієнта"),
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

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

        self.fields["procedure"].empty_label = "Оберіть процедуру"

        self.fields["date"].widget.attrs[
            "min"
        ] = timezone.localdate().isoformat()

    def clean_client_name(self):
        client_name = self.cleaned_data["client_name"].strip()

        if len(client_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити " "щонайменше 2 символи."
            )

        return client_name

    def clean_client_phone(self):
        return normalize_phone_number(self.cleaned_data["client_phone"])

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < timezone.localdate():
            raise ValidationError(
                "Неможливо перенести запис " "на минулу дату."
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
                        "Результат огляду або " "коментар після процедури"
                    ),
                }
            ),
            "recommendations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": ("Рекомендації щодо догляду"),
                }
            ),
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()

        if len(comment) < 2:
            raise ValidationError(
                "Коментар повинен містити " "щонайменше 2 символи."
            )

        return comment

    def clean_recommendations(self):
        return self.cleaned_data["recommendations"].strip()
