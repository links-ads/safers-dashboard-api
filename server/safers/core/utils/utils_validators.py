from jsonschema import validate

from django.core.exceptions import ValidationError


def validate_reserved_words(value, reserved_words, case_insensitive=False):
    if (case_insensitive and value.lower()
        in map(str.lower, reserved_words)) or (value in reserved_words):
        msg = f"{value} is a reserved word."
        raise ValidationError(msg)


def validate_schema(value, schema):
    try:
        validate(instance=value, schema=schema)
    except Exception as e:
        msg = str(e)
        raise ValidationError(msg)
