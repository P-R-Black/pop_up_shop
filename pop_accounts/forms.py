from django import forms
from .models import PopUpCustomer # PopUpCustomerAddress
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

"""
class PopUpUserLoginForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'Sorry, you will need an email'},
        widget=forms.TextInput(attrs={
            'class': 'login_input',
            'placeholder': 'Email',
            'id': 'login_email',
            'type': 'text',
            'name': 'email'
        }
    ))
    
    password = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'login_input',
            'placeholder': 'Password',
            'id': 'login_pwd',
            'type': 'text',
            'name': 'password'
        }
    ))
    
    class Meta:
        model = PopUpCustomer
        fields = ('email','password',)
    
"""


class PopUpEmailOnlyForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'Sorry, you will need an email'}
        )
    class Meta:
        model = PopUpCustomer
        fields = ('email',)


    def clean_email(self):
        email = self.cleaned_data['email']
        return email


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update(
            {'class': 'sign_up_options_form_email', 'placeholder': 'Email', 'name': 'email', 'id': 'id_email_check'})


class PopUpPasswordOnlyForm(forms.ModelForm):
    password = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'sign_up_options_form_password',
            'placeholder': 'Password',
            'id': 'id_password',
            'type': 'password',
            'name': 'password'
        }
    ))

    class Meta:
        model = PopUpCustomer
        fields = ('password',)


class PopUpRegistrationForm(forms.ModelForm):
    
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'Sorry, you will need an email'}
        )
    
    first_name = forms.CharField(
        label='First Name', 
        widget=forms.TextInput(attrs={
            'class': '',
            'placeholder': 'First Name',
            'id': 'id_first_name',
            'type': 'text',
            'name': 'first_name'
        }
    ))
    
    password = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput)
    
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput)

    class Meta:
        model = PopUpCustomer
        fields = ('email', 'first_name', 'password')


    def clean_email(self):
        email = self.cleaned_data['email']
        # if PopUpCustomer.objects.filter(email=email).exists():
        #     raise forms.ValidationError(
        #         "Please use another Email, the email you've entered has already been taken"
        #     )
        return email

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords do not match')
        return cd['password2']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update(
            {'class': 'sign_up_options_form_email', 'placeholder': 'Email', 'name': 'email', 'id': 'id_reg_email'})
        
        self.fields['first_name'].widget.attrs.update(
            {'class': 'sign_up_options_form_email', 'placeholder': 'First Name', 'name': 'name', 'id': 'id_reg_name'})
        
        self.fields['password'].widget.attrs.update(
            {'class': 'sign_up_options_form_email', 'placeholder': 'Password', 'name': 'password', 'type': 'password'})
        
        self.fields['password2'].widget.attrs.update(
            {'class': 'sign_up_options_form_email', 'placeholder': 'Confirm Password', 'name': 'password2', 'type': 'password'})






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