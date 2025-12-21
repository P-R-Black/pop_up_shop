from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from pop_up_auction.models import PopUpCategory, PopUpProduct
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import Mock, patch
from django.core.cache import cache
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from django.utils.text import slugify
from django.views import View
from django.http import JsonResponse
import json
from django.template import Context, Template
from django.http import Http404
from pop_up_cart.cart import Cart
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand)

User = get_user_model()

