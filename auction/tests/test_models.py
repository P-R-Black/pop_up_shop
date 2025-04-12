from django.test import TestCase
from auction.models import PopUpProduct, PopUpProductSize, PoPUpCategory


class TestPopUpCategoryModel(TestCase):

    def setUp(self):
        self.data_one = PoPUpCategory.objects.create(name='shoe', slug='shoe')
    
    def test_category_model_entry(self):
        """
        Test Category model data insertion/types.field attributes
        """
        data = self.data_one
        self.assertTrue(isinstance(data, PoPUpCategory))
    
   





# coverage report | gets coverage report
# coverage html | gets coverage report in html. open index.html file in htmlcov directory
# run --omit='*/venv/*' manage.py test | command to run test