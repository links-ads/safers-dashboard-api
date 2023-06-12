import re
from itertools import chain


class PathMatcher(object):
    """
    class used for SILKY_IGNORE_PATHS to exclude certain URL Patterns from
    silky profiling (inspired by https://stackoverflow.com/a/71313038/1060339)
    """
    def __init__(self, *url_patterns):
        self.url_patterns = list(chain(*url_patterns))

    def __contains__(self, path):
        for pattern in self.url_patterns:
            if pattern.match(path):
                return True


class RegexPathMatcher(PathMatcher):
    """
    Like PathMatcher but rather than take URL Patterns, uses regular expressions
    """
    def __contains__(self, path):
        for pattern in self.url_patterns:
            if re.match(pattern, path):
                return True