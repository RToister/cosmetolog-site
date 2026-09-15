from django import forms
from django.core.exceptions import ValidationError


class CourseApplicationForm(forms.Form):
    applicant_name = forms.CharField(
        label="Ваше ім’я",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введіть ваше ім’я",
                "autocomplete": "name",
            }
        ),
    )
    applicant_phone = forms.CharField(
        label="Номер телефону",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "+380XXXXXXXXX",
                "autocomplete": "tel",
            }
        ),
    )
    applicant_comment = forms.CharField(
        label="Коментар або побажання",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Напишіть, який формат навчання "
                    "вас цікавить або поставте запитання"
                ),
            }
        ),
    )

    def __init__(
            self,
            *args,
            user=None,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields["applicant_name"].initial = (
                    user.get_full_name()
                    or user.username
            )
            self.fields["applicant_phone"].initial = (
                user.phone_number
            )

    def clean_applicant_name(self):
        applicant_name = self.cleaned_data[
            "applicant_name"
        ].strip()

        if len(applicant_name) < 2:
            raise ValidationError(
                "Ім’я повинно містити щонайменше 2 символи."
            )

        return applicant_name

    def clean_applicant_phone(self):
        applicant_phone = self.cleaned_data[
            "applicant_phone"
        ].strip()

        allowed_characters = "+0123456789 ()-"

        if any(
                character not in allowed_characters
                for character in applicant_phone
        ):
            raise ValidationError(
                "Номер телефону містить недопустимі символи."
            )

        digits = "".join(
            character
            for character in applicant_phone
            if character.isdigit()
        )

        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                "Введіть коректний номер телефону."
            )

        return applicant_phone
