from .forms import PopUpEmailOnlyForm, PopUpPasswordOnlyForm, PopUpRegistrationForm

def auth_forms(request):
    email_form = PopUpEmailOnlyForm()
    password_form = PopUpPasswordOnlyForm()
    registration_form = PopUpRegistrationForm()
    return {'email_form': email_form, 'password_form':password_form, 'registration_form': registration_form}
