import phonenumbers
from django.core.exceptions import ValidationError

PHONE_ERROR_MESSAGE = (
    "Введіть коректний номер телефону "
    "з кодом країни, наприклад "
    "+380991112233 або +4915112345678."
)


def normalize_phone_number(
        phone_number,
        *,
        default_region="UA",
):
    raw_phone_number = str(
        phone_number or ""
    ).strip()

    if not raw_phone_number:
        raise ValidationError(
            PHONE_ERROR_MESSAGE
        )

    if raw_phone_number.startswith("00"):
        raw_phone_number = (
            f"+{raw_phone_number[2:]}"
        )

    try:
        parsed_phone_number = (
            phonenumbers.parse(
                raw_phone_number,
                default_region,
            )
        )
    except phonenumbers.NumberParseException:
        raise ValidationError(
            PHONE_ERROR_MESSAGE
        )

    if not phonenumbers.is_possible_number(
            parsed_phone_number
    ):
        raise ValidationError(
            PHONE_ERROR_MESSAGE
        )

    if not phonenumbers.is_valid_number(
            parsed_phone_number
    ):
        raise ValidationError(
            PHONE_ERROR_MESSAGE
        )

    return phonenumbers.format_number(
        parsed_phone_number,
        phonenumbers.PhoneNumberFormat.E164,
    )


def validate_phone_number(phone_number):
    normalize_phone_number(phone_number)
