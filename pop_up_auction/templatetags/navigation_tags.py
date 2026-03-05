from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag(takes_context=True)
def active_page(context, url_name):
    request = context['request']
    url = reverse(url_name)
    if request.path == url:
        return 'aria-current="page"'
    return ''