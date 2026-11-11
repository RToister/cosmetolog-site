from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from dr_toister_site.forms import BootstrapFormMixin
from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)

from .models import User


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class UserRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Ім’я",
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Номер телефону",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "placeholder": "+380991112233",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "phone_number",
            "password1",
            "password2",
        )
        labels = {
            "username": "Логін",
        }

    def clean_phone_number(self):
        phone_number = normalize_phone_number(
            self.cleaned_data["phone_number"]
        )

        if User.objects.filter(
            phone_number=phone_number,
        ).exists():
            raise forms.ValidationError(
                "Користувач із таким номером " "уже існує."
            )

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)

        user.user_type = User.UserType.COSMETOLOGIST
        user.is_cosmetologist_verified = False
        user.cosmetologist_verified_at = None
        user.cosmetologist_verified_by = None

        if commit:
            user.save()

        return user


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
        )
        labels = {
            "first_name": "Ім’я",
            "last_name": "Прізвище",
            "phone_number": "Номер телефону",
        }
        widgets = {
            "phone_number": forms.TextInput(
                attrs={
                    "autocomplete": "tel",
                    "placeholder": "+380991112233",
                }
            ),
        }

    def clean_phone_number(self):
        raw_phone_number = self.cleaned_data["phone_number"].strip()

        if not raw_phone_number:
            return ""

        phone_number = normalize_phone_number(raw_phone_number)

        if (
            User.objects.filter(
                phone_number=phone_number,
            )
            .exclude(
                pk=self.instance.pk,
            )
            .exists()
        ):
            raise forms.ValidationError(
                "Користувач із таким номером " "уже існує."
            )

        return phone_number
