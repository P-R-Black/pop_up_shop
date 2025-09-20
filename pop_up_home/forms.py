from django import forms


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
    

    class Meta:
        fields = ('email_address', 'subject', 'message')
    