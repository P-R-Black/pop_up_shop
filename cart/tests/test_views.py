from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from auction.models import PoPUpCategory, PopUpProduct

class TestCartView(TestCase):
    def setUp(self):
        User.objects.create(username='admin')
        PoPUpCategory.objects.create(name='shoe', slug='shoe')
        PopUpProduct.objects.create(category_id=1, name='air jordan 1', slug='air-jordan-1', price='200.00', image='')
        self.client.post(
            reverse('cart:cart_add'), {'productid': 1, 'productqty': 1, 'action': "post"}, xhr=True
        )
        self.client.post(reverse('cart:cart_add'), {'productid': 2, 'productqty': 2, 'action': "post"}, xhr=True)


    def test_cart_url(self):
        """
        Test homepage response status
        """
        response = self.client.get(reverse('cart:cart_summary'))
        self.assertEqual(response.status_code, 200)

    def test_cart_add(self):
        """
        Test adding items to cart
        """
        response = self.client.post(reverse('cart:cart_add'), {'productid': 1, 'productqty': 3, 'action': 'post'}, xhr=True)
        self.assertEqual(response.json(), {'qty': 2})
        response = self.client.post(reverse('cart:cart_add'), {'productid': 2, 'productqty': 2, 'action': 'post'}, xhr=True)
        self.assertEqual(response.json(), {'qty': 3})


    def test_cart_delete(self):
        """
        Test deleting items from the basket
        """
        response = self.client.post(reverse('cart:cart_delete'), {'productid': 2, 'action': 'post'}, xhr=True)
        self.assertEqual(response.json()), {'qty': 1, 'subtotal': '200.00'}