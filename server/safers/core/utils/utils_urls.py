from collections import defaultdict
from datetime import datetime
from itertools import chain, filterfalse, groupby

from django.conf import settings
from django.urls.resolvers import URLPattern, URLResolver

###################
# path converters #
###################


class DateTimeConverter:

    # ISO 8601
    regex = "(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?"
    format = "%Y-%m-%dT%H:%M:%SZ"

    def to_python(self, value):
        return datetime.strptime(value, self.format)

    def to_url(self, value):
        return value.strftime(self.format)
