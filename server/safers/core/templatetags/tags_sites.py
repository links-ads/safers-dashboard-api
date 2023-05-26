"""
Template tags related to Sites & SiteProfiles
"""
from django import template
from django.contrib.sites.shortcuts import get_current_site

register = template.Library()


@register.simple_tag(takes_context=True)
def site(context):
    """
    Pass Site instance to templates.  Doing it here instead of a
    context-processor so I only hit the db as needed instead of
    for every request. (Since I only use this in the Admin.)
    """
    current_site = get_current_site(context["request"])
    return current_site