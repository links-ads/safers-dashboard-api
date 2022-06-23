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


#########
# utils #
#########


def remove_urlpatterns(urlpatterns, pattern_names_to_remove):
    """
    Takes a list of URLPatterns (or URLResolvers) and removes those patterns (or resolvers) listed in
    "pattern_names_to_remove" - Useful when dealing w/ 3rd party libraries w/ hard-coded URLPatterns.
    """
    # yapf: disable

    # split urlpatterns into patterns & resolvers
    urls_to_check = defaultdict(list)
    for k, g in groupby(urlpatterns, key=type):
        urls_to_check[k] += list(g)

    resolvers_to_keep = filterfalse(
        # note the double-looping to check patterns _w/in_ a resolver
        lambda resolver: any(pattern.name in pattern_names_to_remove for pattern in resolver.url_patterns),
        urls_to_check.get(URLResolver, [])
    )

    patterns_to_keep = filterfalse(
        lambda pattern: pattern.name in pattern_names_to_remove,
        urls_to_check.get(URLPattern, [])
    )

    return list(chain(resolvers_to_keep, patterns_to_keep))
