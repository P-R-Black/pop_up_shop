from django.apps import AppConfig


class PopUpAuctionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pop_up_auction'


    def ready(self):
        import pop_up_cart.signals