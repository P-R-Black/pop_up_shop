from django import template
import re

register = template.Library()

@register.filter
def compute_number(value_a, value_b):
   return int(value_a) + int(value_b)
