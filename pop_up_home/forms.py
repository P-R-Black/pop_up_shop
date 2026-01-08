from django import forms
import os
import environ

# from django_recaptcha.fields import ReCaptchaField
from django.conf import settings


USE_RECAPTCHA = getattr(settings, "USE_RECAPTCHA", False)

print('USE_RECAPTCHA', USE_RECAPTCHA)

if USE_RECAPTCHA:
    from django_recaptcha.fields import ReCaptchaField
    from django_recaptcha.widgets import (
        ReCaptchaV2Checkbox,
        ReCaptchaV2Invisible,
        ReCaptchaV3,
    )
else:
    ReCaptchaField = None

# from django_recaptcha.widgets import ReCaptchaV2Checkbox, ReCaptchaV2Invisible, ReCaptchaV3

recaptcha_public_key=os.environ.get('RECAPTCHA_PUBLIC_KEY')
recaptcha_private_key=os.environ.get('RECAPTCHA_PRIVATE_KEY')

# Example: if your key is for v2 Checkbox
# captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
# print('captcha 1', captcha)

# If your key is for v2 Invisible
# captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)
# print('captcha 2', captcha)

# If your key is for v3
# captcha = ReCaptchaField(widget=ReCaptchaV3)
# print('captcha 3', captcha)

# Create your forms here

class ContactForm(forms.Form):
    email_address = forms.EmailField(
        max_length=150, required=True, label='email', help_text='Required',
        error_messages={'required': 'An email address is required', 
                        'invalid': 'Enter a valid email address.'},
        widget=forms.EmailInput(attrs={
            'class': 'modal_email_contact_input',
            'placeholder': 'Email',
            'aria-label': 'Email',
            'type': 'email',
            'name': 'email'
        }))

    subject = forms.CharField(
        max_length=150, required=True, label='subject', help_text='Required',
        error_messages={'required': 'What can we help you with'},
        widget=forms.TextInput(attrs={
            'class': 'modal_subject_contact_input',
            'placeholder': 'Subject',
            'aria-label': 'Subject',
            'type': 'text',
        })
        )
    
    message = forms.CharField(
        label='Delivery Instructions', max_length=200, required=True, help_text='Required',
        error_messages={'required': 'Please describe how we can help.'},
        widget=forms.Textarea(attrs={
            'class': 'modal_message_contact_input',
            'placeholder': 'Let us know how we can help...',
            'type': 'text',
            'name': 'message',
            'aria-label': 'message'
        }
    ))
    
    # Example: choose ONE that matches your key type
    # captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)   # if v2 checkbox
    # captcha = ReCaptchaField(widget=ReCaptchaV2Invisible) # if v2 invisible
    # captcha = ReCaptchaField(widget=ReCaptchaV3)          # if v3


 
    # captcha = ReCaptchaField(
    #     public_key=recaptcha_public_key,
    #     private_key=recaptcha_private_key,
    # )


    # ✅ Conditionally add captcha field
    if USE_RECAPTCHA:
        captcha = ReCaptchaField(
            # widget=ReCaptchaV2Checkbox()
        )

    # captcha = ReCaptchaField()

    class Meta:
        fields = ('email_address', 'subject', 'message')
    
