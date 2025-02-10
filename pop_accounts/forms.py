from django import forms
from .models import PopUpCustomer, PopUpCustomerAddress
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm, SetPasswordForm)
# from django_countries.data import COUNTRIES




"""" The Pop Up"""
# class ThePopUpUserAddressForm(forms.ModelForm):
#     class Meta:
#         model = PopUpCustomerAddress
#         fields = ['full_name', 'phone', 'address_line', 'address_line2', 'town_city', 'postcode']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['full_name'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Full Name'}
#         )
#         self.fields['phone'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Phone'})

#         self.fields['address_line'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Address'})

#         self.fields['address_line2'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Address 2'})

#         self.fields['town_city'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Town/City/State'})

#         self.fields['postcode'].widget.attrs.update(
#             {'class': 'form-control mb-2 account-form', 'placeholder': 'Postal Code'})


# class PopUpUserLoginForm(AuthenticationForm):
#     username = forms.CharField(widget=forms.TextInput(
#         attrs={
#             'class': 'form-control mb-3',
#             'placeholder': 'Username',
#             'id': 'login-username'
#         }
#     ))
#     password = forms.CharField(widget=forms.PasswordInput(
#         attrs={
#             'class': 'form-control',
#             'placeholder': 'Password',
#             'id': 'login-pwd'
#         }
#     ))


# class PopUpRegistrationForm(forms.ModelForm):
#     user_name = forms.CharField(label='Enter Username', min_length=4, max_length=50, help_text='Required')
#     email = forms.CharField(max_length=100, help_text='Required',
#                             error_messages={'required': 'Sorry, you will need an email'})
#     password = forms.CharField(label='Password', widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Repeat Password', widget=forms.PasswordInput)

#     class Meta:
#         model = PopUpCustomer
#         fields = ('user_name', 'email',)

#     def clean_username(self):
#         user_name = self.cleaned_data['user_name'].lower()
#         r = PopUpCustomer.objects.filter(user_name=user_name)
#         if r.count():
#             raise forms.ValidationError('Username already exists')
#         return user_name

#     def clean_passowrd2(self):
#         cd = self.cleaned_data
#         if cd['password'] != cd['password2']:
#             raise forms.ValidationError('Passwords do not match')
#         return cd['password2']

#     def clean_email(self):
#         email = self.cleaned_data['email']
#         if PopUpCustomer.objects.filter(email=email).exists():
#             raise forms.ValidationError(
#                 "Please use another Email, the email you've entered has already been taken"
#             )
#         return email

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['user_name'].widget.attrs.update(
#             {'class': 'form-control mb-3', 'placeholder': 'Username'})
#         self.fields['email'].widget.attrs.update(
#             {'class': 'form-control mb-3', 'placeholder': 'E-mail', 'name': 'email', 'id': 'id_email'})
#         self.fields['password'].widget.attrs.update(
#             {'class': 'form-control mb-3', 'placeholder': 'Password'})
#         self.fields['password2'].widget.attrs.update(
#             {'class': 'form-control mb-3', 'placeholder': 'Repeat Password'})


# class PopUpUserEditForm(forms.ModelForm):
#     email = forms.EmailField(
#         label='Account email (can not be changed)', max_length=200, widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control mb-3',
#                 'placholder': 'email',
#                 'id': 'form-email',
#                 'readonly': 'readonly'
#             }
#         )
#     )

#     user_name = forms.CharField(
#         label='Username', min_length=4, max_length=50, widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control mb-3',
#                 'placholder': 'Username',
#                 'id': 'form-firstname',
#                 'readonly': 'readonly'
#             }
#         )
#     )

#     first_name = forms.CharField(
#         label='First Name', min_length=4, max_length=50, widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control mb-3',
#                 'placholder': 'Firstname',
#                 'id': 'form-lastname',
#             }
#         )
#     )

#     class Meta:
#         model = PopUpCustomer
#         fields = ('email', 'user_name', 'first_name',)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['user_name'].required = True
#         self.fields['email'].required = True


# class PopUpPwdResetForm(PasswordResetForm):
#     email = forms.EmailField(max_length=245, widget=forms.TextInput(
#         attrs={
#             'class': 'form-control mb-3',
#             'placeholder': 'Email',
#             'id': 'form-email'
#         }
#     ))

#     def clean_email(self):
#         email = self.cleaned_data['email']
#         u = PopUpCustomer.objects.filter(email=email)
#         if not u:
#             raise forms.ValidationError(
#                 'Unfortunately we can not find that account'
#             )

#         return email


# class PopUpPwdResetConfirmForm(SetPasswordForm):
#     new_password1 = forms.CharField(
#         label ='New Password', widget=forms.PasswordInput(
#             attrs={
#                 'class': 'form-control mb-3',
#                 'placeholder': 'New Password',
#                 'id': 'form-newpass'
#             }
#         )
#     )

#     new_password2 = forms.CharField(
#         label='Repeat Password', widget=forms.PasswordInput(
#             attrs={
#                 'class': 'form-control mb-3',
#                 'placeholder': 'New Password',
#                 'id': 'form-new-pass2'
#             }
#         )
#     )