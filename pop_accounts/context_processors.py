from .forms import (PopUpEmailOnlyForm, PopUpPasswordOnlyForm, PopUpRegistrationForm, 
                    PopUpEmailPasswordResetForm, PopUpPasswordResetForm)

def auth_forms(request):
    email_form = PopUpEmailOnlyForm()
    password_form = PopUpPasswordOnlyForm()
    registration_form = PopUpRegistrationForm()
    email_password_reset_form = PopUpEmailPasswordResetForm()
    password_reset_form = PopUpPasswordResetForm()
    return {
        'email_form': email_form, 'password_form':password_form, 
        'registration_form': registration_form, 'email_password_reset_form': email_password_reset_form, 
        'password_reset_form': password_reset_form
        }
