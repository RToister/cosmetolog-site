from django import forms


class BootstrapFormMixin:
    """Add Bootstrap 5 CSS classes to every widget of the form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"
            else:
                css_class = "form-control"

            existing_classes = widget.attrs.get("class", "")

            if css_class not in existing_classes.split():
                widget.attrs["class"] = (
                    f"{existing_classes} {css_class}".strip()
                )

    def full_clean(self):
        super().full_clean()

        for field_name in self.errors:
            if field_name not in self.fields:
                continue

            widget = self.fields[field_name].widget
            classes = widget.attrs.get("class", "").split()

            if "is-invalid" not in classes:
                classes.append("is-invalid")
                widget.attrs["class"] = " ".join(classes)
