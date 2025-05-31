from django.apps import AppConfig


class PopAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pop_accounts'

    def ready(self):
        import pop_accounts.signals
