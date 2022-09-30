from django.db import models


class CaseInsensitiveTextChoices(models.TextChoices):
    @classmethod
    def find_enum(cls, string, case_insensitive=True):
        if string is not None:
            if case_insensitive:
                string = string.upper()

            for name, member in cls.__members__.items():
                value = member.value
                if case_insensitive:
                    value = value.upper()

                if string == value:
                    return member


class SpaceInsensitiveTextChoices(models.TextChoices):
    @classmethod
    def find_enum(cls, string, case_insensitive=True, space_insensitive=True):
        if string is not None:
            if case_insensitive:
                string = string.upper()
            if space_insensitive:
                string = string.replace(" ", "")

            for name, member in cls.__members__.items():
                value = member.value
                if case_insensitive:
                    value = value.upper()
                if space_insensitive:
                    value = value.replace(" ", "")

                if string == value:
                    return member
