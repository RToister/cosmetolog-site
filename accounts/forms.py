from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Ім’я",
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Номер телефону",
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
        phone_number = self.cleaned_data["phone_number"]

        if User.objects.filter(
                phone_number=phone_number
        ).exists():
            raise forms.ValidationError(
                "Користувач із таким номером уже існує."
            )

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.COSMETOLOGIST

        if commit:
            user.save()

        return user


class UserProfileForm(forms.ModelForm):
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

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]

        if User.objects.filter(
                phone_number=phone_number
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Користувач із таким номером уже існує."
            )

        return phone_number
