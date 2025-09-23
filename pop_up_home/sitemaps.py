from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from pop_up_auction.models import PopUpProduct

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["pop_up_home:home", "pop_up_auction:auction", "pop_up_home:contact"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority = 0.7
    changefreg = "weekly"

    def items(self):
        return PopUpProduct.objects.all()
    
    def lastmode(self, obj):
        return obj.updated_at