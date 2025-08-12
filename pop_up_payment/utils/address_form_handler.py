from django.contrib import messages
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress

def handle_selected_address(request, user, selected_address_id, session_key, success_msg):
    try:
        selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
        request.session[session_key] = str(selected_address.id)
        messages.success(request, success_msg)
    except PopUpCustomerAddress.DoesNotExist:
        messages.error(request, "The selected address could not be found")
    
    return

def handle_update_address(request, form_class, address_id, user, default_flag_name, default_field_name, session_key, success_msg):
    try:
        address_instance = PopUpCustomerAddress.objects.get(id=address_id, customer=user, )
    except PopUpCustomerAddress.DoesNotExist:
        messages.error(request, "Address not found.")
        return None, None
    
    form = form_class(request.POST, instance=address_instance)
    if form.is_valid():
        updated_address = form.save(commit=False)
        if form.cleaned_data.get(default_flag_name):
            PopUpCustomerAddress.objects.filter(custoemr=user, **{default_field_name: True}).exclude(id=updated_address.id).update(**{default_field_name: False})
            setattr(updated_address, default_field_name, True)
        else:
            setattr(updated_address, default_field_name, False)
        
        updated_address.save()
        request.session[session_key] = str(updated_address.id)
        messages.success(request, success_msg)
        return updated_address, None
    else:
        messages.error(request, "Please correct the errors below.")
        return None, form


def handle_new_address(request, form_class, user, default_flag_name, default_field_name, session_key, success_msg):
    form = form_class(request.POST)
    if form.is_valid():
        new_address = form.save(commit=False)
        new_address.customer = user
        if form.cleaned_data.get(default_flag_name):
            PopUpCustomerAddress.objects.filter(customer=user, **{default_field_name: True}).update(**{default_field_name: False})
            setattr(new_address, default_field_name, True)
        else:
            setattr(new_address, default_field_name, False)
        
        new_address.save()
        request.session[session_key] = str(new_address.id)
        messages.success(request, success_msg)
        return new_address, None
    else:
        messages.error(request, "Please correct the errors below.")
        return None, form