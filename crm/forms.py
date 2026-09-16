from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            "full_name",
            "phone_number",
            "customer_type",
            "notes",
            "is_active",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ім’я та прізвище",
                    "autocomplete": "name",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+380...",
                    "autocomplete": "tel",
                }
            ),
            "customer_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Внутрішні нотатки про клієнта"
                    ),
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_full_name(self):
        full_name = self.cleaned_data[
            "full_name"
        ].strip()

        if len(full_name) < 2:
            raise forms.ValidationError(
                "Ім’я повинно містити щонайменше "
                "2 символи."
            )

        return full_name
