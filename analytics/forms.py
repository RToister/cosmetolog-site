from django import forms
from django.core.exceptions import ValidationError


class AnalyticsPeriodForm(forms.Form):
    start_date = forms.DateField(
        label="Дата від",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )
    end_date = forms.DateField(
        label="Дата до",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                "Початкова дата не може бути пізніше кінцевої."
            )

        return cleaned_data
