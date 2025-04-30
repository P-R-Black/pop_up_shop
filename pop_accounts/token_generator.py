from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)

        )
    
    # def _make_hash_value(self, user, timestamp):
    #     print('_make_hash_value user is', user, '_make_hash_value timestamp', timestamp)
    #     # Use fields from your custom user model
    #     login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
    #     print('login_timestamp', login_timestamp)
    #     return str(user.pk) + str(user.password) + str(login_timestamp) + str(timestamp)

custom_token_generator = CustomPasswordResetTokenGenerator()
print('custom_token_generator', custom_token_generator)