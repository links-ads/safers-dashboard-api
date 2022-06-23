import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SafersPasswordValidator:

    UPPERCASE_REGEX = re.compile("(?=.*[A-Z])")
    LOWERCASE_REGEX = re.compile("(?=.*[a-z])")
    NUMERIC_REGEX = re.compile("(?=.*\d)")

    def validate(self, password, user=None):

        if not self.UPPERCASE_REGEX.match(password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter.")
            )
        if not self.LOWERCASE_REGEX.match(password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter.")
            )
        if not self.NUMERIC_REGEX.match(password):
            raise ValidationError(
                _("This password must contain at least one number.")
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one lowercase letter, one uppercase letter, and one number."
        )
