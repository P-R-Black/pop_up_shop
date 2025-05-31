from django import forms
from .models import PopUpCustomer, PopUpCustomerAddress
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm, SetPasswordForm)
import re
from django.core.exceptions import ValidationError
from .utils import validate_password_strength

# from django_countries.data import COUNTRIES




"""" The Pop Up"""
SHOE_SIZE_CHOICES = [
    ('', 'Select size'),
    ('5', '5 US'),
    ('5.5', '5.5 US'),
    ('6', '6 US'),
    ('6.5', '6.5 US'),
    ('7', '7 US'),
    ('7.5', '7.5 US'),
    ('8', '8 US'),
    ('8.5', '8.5 US'),
    ('9', '9 US'),
    ('9.5', '9.5 US'),
    ('10', '10 US'),
    ('10.5', '10.5 US'),
    ('11', '11 US'),
    ('11.5', '11.5 US'),
    ('12', '12 US'),
    ('12.5', '12.5 US'),
    ('13', '13 US'),
    ('13.5', '13.5 US'),
    ('14', '14 US'),
    ('14.5', '14.5 US'),
    ('15', '15 US'),
    ('15.5', '15.5 US'),
    ('16', '16 US'),
]


STATES_SELELCTION = [
    ('', 'State'),
    ('Alabama', 'AL'),
    ('Alaska', 'AK'),
    ('Arizona', 'AZ'),
    ('Arkansas', 'AR'),
    ('California', 'CA'),
    ('Colorado', 'CO'),
    ('Connecticut', 'CT'),
    ('Delaware', 'DE'),
    ('District Of Columbia', 'DC'),
    ('Florida', 'FL'),
    ('Georgia', 'GA'),
    ('Hawaii', 'HI'),
    ('Idaho', 'ID'),
    ('Illinois', 'IL'),
    ('Indiana', 'IN'),
    ('Iowa', 'IA'),
    ('Kansas', 'KS'),
    ('Kentucky', 'KY'),
    ('Louisiana', 'LA'),
    ('Maine', 'ME'),
    ('Maryland', 'MD'),
    ('Massachusetts', 'MA'),
    ('Michigan', 'MI'),
    ('Minnesota', 'MN'),
    ('Mississippi', 'MS'),
    ('Missouri', 'MO'),
    ('Montana', 'MT'),
    ('Nebraska', 'NE'),
    ('Nevada', 'NV'),
    ('New Hampshire', 'NH'),
    ('New Jersey', 'NJ'),
    ('New Mexico', 'NM'),
    ('New York', 'NY'),
    ('North Carolina', 'NC'),
    ('North Dakota', 'ND'),
    ('Ohio', 'OH'),
    ('Oklahoma', 'OK'),
    ('Oregon', 'OR'),
    ('Pennsylvania', 'PA'),
    ('Rhode Island', 'RI'),
    ('South Carolina', 'SC'),
    ('South Dakota', 'SD'),
    ('Tennessee', 'TN'),
    ('Texas', 'TX'),
    ('Utah', 'UT'),
    ('Vermont', 'VT'),
    ('Virginia', 'VA'),
    ('Washington', 'WA'),
    ('West Virginia', 'WV'),
    ('Wisconsin', 'WI'),
    ('Wyoming', 'WY')
]


class ThePopUpUserAddressForm(forms.ModelForm):
    prefix = forms.ChoiceField(
        label='Prefix',
        choices=[("", "Select Prefix")] + PopUpCustomerAddress.PREFIX_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': 'personal_info_input_prefix',
            'id': 'prefix', # prefix
            'name': 'prefix',
        })
    )

    first_name = forms.CharField(
        label='First Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_input_first_name', # personal_info_first_name_input
            'placeholder': 'First Name',
            'id': '',
            'name': 'first_name'
        })
    )

    middle_name = forms.CharField(
        label='Middle Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_input_middle_name', # personal_info_first_name_input
            'id': '',
            'placeholder': 'Middle Name',
            'name': 'middle_name'
        })
    )

    last_name = forms.CharField(
        label='Last Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_input_last_name', # personal_info_last_name_input
            'placeholder': 'Last Name',
            'id': '',
            'name': 'last_name'
        })
    )

    suffix = forms.ChoiceField(
        label='Suffix',
        choices=[("", "Select Suffix")] + PopUpCustomerAddress.SUFFIX_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': 'personal_info_input_suffix',
            'id': '', # suffix
            'name': 'suffix',
        })
    )

    street_address_1 = forms.CharField(
        label='Street Address 1', max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_street_address_one_input',
            'id': '',
            'placeholder': 'Street Address 1',
            'type': 'text',
            'name': 'street_address_1'
        }
    ))

    street_address_2 = forms.CharField(
        label='Street Address 2', max_length=200, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_street_address_two_input',
            'id': '',
            'placeholder': 'Street Address 2',
            'type': 'text',
            'name': 'street_address_2'
        }
    ))

    apt_ste_no = forms.CharField(
        label='Apt/Ste', max_length=200, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_apt_inputs', # personal_info_apt_inputs
            'id': '',
            'placeholder': 'Apt/Ste',
            'type': 'text',
            'name': 'apt_ste'
        }
    ))

    city_town = forms.CharField(
        label='City/Town', min_length=2, max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_address_city_input', #personal_info_address_city_input
            'id': '',
            'placeholder': 'City',
            'type': 'text',
            'name': 'city'
        }
    ))


    state = forms.ChoiceField(
        label='State', required=True,
        choices=STATES_SELELCTION, 
        widget=forms.Select(attrs={
            'class': 'personal_info_address_state', # personal_info_address_state
            'id': '',
            'placeholder': 'State',
            'name': 'state'
        }
    ))

    postcode = forms.CharField(
        label='Postal Code', max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_address_zip_input', # personal_info_address_zip_input
            'id': '',
            'placeholder': 'Postal Code',
            'type': 'text',
            'name': 'postcode'
        }
    ))

    delivery_instructions = forms.CharField(
        label='Delivery Instructions', max_length=200, required=False,
        widget=forms.Textarea(attrs={
            'class': 'delivery_instruct_text',
            'id': '',
            'placeholder': 'Delivery Instructions',
            'type': 'text',
            'name': 'deliv_instructions'
        }
    ))

    address_default = forms.BooleanField(
        label = 'Default Address',
        required=False,
        widget = forms.CheckboxInput(attrs={
            'class': 'personal_info_default_address', # personal_info_default_address
            'id': ''
        })  
    )


    class Meta:
        model = PopUpCustomerAddress
        fields = ['prefix', 'first_name', 'middle_name', 'last_name', 'suffix', 'street_address_1', 
                  'street_address_2', 'apt_ste_no', 'city_town', 'state', 'postcode', 'delivery_instructions']




class PopUpUserLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'An email address must be entered'},
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
            'type': 'password',
            'name': 'password'
        }
    ))
    
    class Meta:
        fields = ('email','password',)
    


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
            {'class': 'sign_up_options_form_email', 'type': 'email', 'placeholder': 'Email', 'name': 'email', 'id': 'id_email_check'})


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
    
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password2 and not password:
            self.add_error("password", "Please enter a password.")
        elif password and not password2:
            self.add_error("password2", "Please confirm your password.")
        elif password and password2 and password != password2:
            self.add_error("password2", "Passwords do not match.")
        
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password_strength(password)
        return password

    def clean_password2(self):
        cd = self.cleaned_data
        password = cd.get('passsword')
        password2 = cd.get('password2')


        if not password2:
            raise forms.ValidationError("Please confirm your password.")
    
        if not password:
            # Let clean_password handle empty password case or password strength issues
            return password2

        if password and password2:
            if password != password2:
                self.add_error("password2", "Passwords do not match")
        elif password and not password2:
            self.add_error("password2", "Please confirm your password.")

        return password2


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



class PopUpEmailPasswordResetForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'Sorry, you will need an email'},
         widget=forms.PasswordInput(attrs={
            'class': 'email_password_reset_form',
            'placeholder': 'Email',
            'id': 'id_email_password_reset_form',
            'type': 'email',
            'name': 'email_reset'
        }
    ))

    class Meta:
        model = PopUpCustomer
        fields = ('email',)


    def clean_email(self):
        email = self.cleaned_data['email']
        return email



class PopUpPasswordResetForm(forms.ModelForm):
    """
    Email not needed since token used to verify user
    email = forms.EmailField(
        label='Email',
        max_length=100, 
        help_text='Required',
        error_messages={'required': 'Sorry, you will need an email'},
        widget=forms.EmailInput(attrs={
            'class': 'email_for_password_reset_one',
            'placeholder': 'Email',
            'id': 'id_email_for_password_reset_one',
            'type': 'email',
            'name': 'email'
        }
    ))
    """
    
     
  
    password = forms.CharField(
        label='Password',
        help_text='Required',
        required=True,
        error_messages={'required': 'Sorry, you will need an email'},
        widget=forms.PasswordInput(attrs={
            'class': 'password_reset_one',
            'placeholder': 'New Password',
            'id': 'id_password_reset_one',
            'type': 'password',
            'name': 'password'
        }
        
    ))

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'password_reset_one',
            'placeholder': 'Confirm Password',
            'id': 'id_password_reset_two',
            'type': 'password',
            'name': 'password2'
        }
        
    ))

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password_strength(password)
        return password

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords do not match')
        return cd['password2']

    class Meta:
        model = PopUpCustomer
        fields = ('password',)



class PopUpUserEditForm(forms.Form):
    first_name = forms.CharField(
        label='First Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_first_name_input',
            'placeholder': 'First Name',
            'id': 'edit-form-first-name',
        })
    )

    middle_name = forms.CharField(
        label='Middle Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_first_name_input',
            'placeholder': 'Middle Name',
            'id': 'edit-form-middle-name',
        })
    )

    last_name = forms.CharField(
        label='Last Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_last_name_input',
            'placeholder': 'Last Name',
            'id': 'edit-form-last-name',
        })
    )


    shoe_size = forms.ChoiceField(
        label='Shoe Size',
        choices=SHOE_SIZE_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': '',
            'id': 'shoe_size',
            'name': 'shoe_size',
        })
    )

    size_gender = forms.ChoiceField(
        label='Size Gender', required=False,
        choices=[('male', 'Male'), ('female', 'Female')],
        widget=forms.Select(attrs={
            'class': 'edit_form_name',
            'id': 'gen_option',
        })
    )

    favorite_brand = forms.ChoiceField(
        label='Favorite Brand', required=False,
        choices=[
            ('', 'Favorite Brand'),
            ('adidas', 'Adidas'),
            ('asics', 'Asics'),
            ('balenciaga', 'Balenciaga'),
            ('brooks', 'Brooks'),
            ('fear_of_god', 'Fear of God'),
            ('gucci', 'Gucci'),
            ('jordan', 'Jordan'),
            ('new_balance', 'New Balance'),
            ('nike', 'Nike'),
            ('prada', 'Prada'),
            ('puma', 'Puma'),
            ('reebok', 'Reebok'),
            ('saucony', 'Saucony'),
            ('yeezy', 'Yeezy'),
        ],
        widget=forms.Select(attrs={
            'class': 'edit-form-favorite-brand',
            'id': 'edit-form-favorite-brand',
            'name': 'brand',
        })
    )

    mobile_phone = forms.CharField(
        label = 'Mobile Phone', min_length=10, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'personal_info_mobile_phone',
            'id': 'personal_info_mobile_phone',
            'placeholder': 'Mobile Phone (xxx-xxx-xxxx)',
            'name': 'Phone'
        })
    )

    mobile_notification = forms.BooleanField(
        label = 'Permission to Text',
        required = False,
        widget = forms.CheckboxInput(attrs={
            'class': 'mobile_notification',
            'id': 'mobile_notification'
        })  
    )

    class Meta:
        model = PopUpCustomer
        fields = ('first_name', 'last_name', 'middle_mane', 'shoe_size', 'size_gender', 'favorite_brand', 'mobile_notification')
    



class PopUpUpdateShippingInformationForm(forms.ModelForm):

    prefix = forms.ChoiceField(
        label='Prefix',
        choices=[("", "Select Prefix")] + PopUpCustomerAddress.PREFIX_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': '',
            'id': 'prefix',
            'name': 'prefix',
        })
    )

    first_name = forms.CharField(
        label='First Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal_first_name_input',
            'placeholder': 'First Name',
            'id': '',
            'name': 'first_name'
        })
    )

    middle_name = forms.CharField(
        label='Middle Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal_first_name_input',
            'placeholder': 'Middle Name',
            'id': '',
            'name': 'middle_name'
        })
    )

    last_name = forms.CharField(
        label='Last Name', min_length=2, max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal_first_name_input',
            'placeholder': 'Last Name',
            'id': '',
            'name': 'last_name'
        })
    )

    suffix = forms.ChoiceField(
        label='Suffix',
        choices=[("", "Select Suffix")] + PopUpCustomerAddress.SUFFIX_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': '',
            'id': 'suffix',
            'name': 'suffix',
        })
    )

    address_line = forms.CharField(
        label='Street Address 1', max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'modal_street_address_one_input',
            'id': '',
            'placeholder': 'Street Address 1',
            'type': 'text',
            'name': 'address_line'
        }
    ))

    address_line2 = forms.CharField(
        label='Street Address 2', max_length=200, required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal_street_address_two_input',
            'id': '',
            'placeholder': 'Street Address 2',
            'type': 'text',
            'name': 'address_line2'
        }
    ))

    apartment_suite_number = forms.CharField(
        label='Apt/Ste', max_length=200, required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal_address_zip_input',
            'id': '',
            'placeholder': 'Apt/Ste',
            'type': 'text',
            'name': 'apartment_suite_number'
        }
    ))

    town_city = forms.CharField(
        label='City/Town', min_length=2, max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'modal_address_city_input',
            'id': '',
            'placeholder': 'City',
            'type': 'text',
            'name': 'city'
        }
    ))


    state = forms.ChoiceField(
        label='State', required=True,
        choices=STATES_SELELCTION, 
        widget=forms.Select(attrs={
            'class': '',
            'id': 'state',
            'placeholder': 'State',
            'type': 'text',
            'name': 'state'
        }
    ))

    postcode = forms.CharField(
        label='Postal Code', max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'modal_address_zip_input',
            'id': '',
            'placeholder': 'Postal Code',
            'type': 'text',
            'name': 'postcode'
        }
    ))

    delivery_instructions = forms.CharField(
        label='Delivery Instructions', max_length=200, required=False,
        widget=forms.Textarea(attrs={
            'class': 'modal_address_delivery_instructions',
            'id': '',
            'placeholder': 'Delivery Instructions',
            'type': 'text',
            'name': 'deliv_instructions'
        }
    ))


    address_default = forms.BooleanField(
        label = 'Default Address',
        required=False,
        widget = forms.CheckboxInput(attrs={
            'class': 'personal_info_default_address',
            'id': ''
        }
    ))



    class Meta:
        model = PopUpCustomerAddress
        fields = ['first_name', 'middle_name', 'last_name',
            'address_line', 'address_line2', 'apartment_suite_number', 
            'town_city', 'state', 'postcode', 'delivery_instructions',
            ]
    