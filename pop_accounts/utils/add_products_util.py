from django.db import IntegrityError
from django.contrib import messages
from auction.models import (PopUpProductSpecification, PopUpProductSpecificationValue)
from auction.forms import (PopUpAddProductForm, PopUpProductImageForm)


def handle_simple_form_submission(request, FormClass, form_type_label, success_message):
    form = FormClass(request.POST)
    if form.is_valid():
        try:
            instance = form.save()
            messages.success(request, success_message.format(name=instance.name))
            return True, instance
        except IntegrityError:
            name = form.cleaned_data.get('name')
            messages.error(request, f"{form_type_label} '{name}' already exists.")
        except Exception as e:
            messages.error(request, f"An error occured while saving the {form_type_label}.lower()")
            print(f"Save error on {form_type_label}:", e)
    else:
        messages.error(request, f"Please correct the errors in the {form_type_label.lower()} form.")
        print(f"{form_type_label} Form errors: {form.errors}")

    return False, None


def handle_full_product_save(request):
    product_form = PopUpAddProductForm(request.POST)
    image_form = PopUpProductImageForm(request.POST, request.FILES)

    if not product_form.is_valid():
        messages.error(request, 'Please correct the erros in the product form.')
        return False
    
    try:
        product = product_form.save()

        # save image if present
        if image_form.is_valid():
            image_file = image_form.cleaned_data.get('image')
            image_url = image_form.cleaned_data.get('image_url')
            if image_file or image_url:
                image_instance = image_form.save(commit=False)
                image_instance.product = product
                image_instance.save()
        else:
            messages.error(request, "There was an error in the product image form")
            print("Product Image Form Errors", image_form.errors)
        
        # Handle existing specs
        for key, value in request.POST.items():
            if key.startswith('spec_') and value.strip():
                spec_id = key.replace('spec_', '')
                try:
                    spec = PopUpProductSpecification.objects.get(id=spec_id)
                    PopUpProductSpecificationValue.objects.create(
                        product=product, specification=spec, value=value.strip()
                    )
                except PopUpProductSpecification.DoesNotExist:
                    print(f"Specifcation with id {spec_id} not found.")
        
        # Handle custom specs
        names = request.POST.getlist('custom_spec_names[]')
        values = request.POST.getlist('custom_spec_values[]')

        for name, value in zip(names, values):
            if name.strip() and value.strip():
                try:
                    spec= PopUpProductSpecification.objects.create(
                        name=name.strip(),
                        product_type=product.product_tupe
                    )
                except IntegrityError:
                    spec = PopUpProductSpecification.objects.get(
                        name=name.strip(), product_type=product.product_type
                    )
                PopUpProductSpecificationValue.objects.create(
                    product = product, specification=spec, value=value.strip()
                )
        messages.success(request, f"Product '{product.product_title}' added successfully!")
        return True
    
    except Exception as e:
        messages.error(request, "An error occurred while saving the product.")
        print(f"Save error on Product: {e}")
        return False
    
