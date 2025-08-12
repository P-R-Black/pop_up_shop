from django.db import IntegrityError
from django.contrib import messages
from pop_up_auction.models import PopUpProductSpecification, PopUpProductSpecificationValue
from pop_up_auction.forms import (PopUpAddProductForm, PopUpProductImageForm)

def save_existing_specifications(self, request, product_instance):
    """
    Manage saving existing specifications
    """
    for key, value in request.POST.items():
        if key.startswith('spec_') and value.strip():
            spec_id = key.replace('spec_', '')
            try:
                specification = PopUpProductSpecification.objects.get(id=spec_id)
                PopUpProductSpecificationValue.objects.create(
                    product=product_instance,
                    specification=specification,
                    value=value.strip()
                )
                print(f'Updated spec {specification.name}: {value}')
            except PopUpProductSpecification.DoesNotExist:
                print(f"Specification with id {spec_id} not found!")


def save_custom_specifications(self, request, product_instance):
    """
    Manage saving custom specifications
    """
    custom_names = request.POST.getlist('custom_spec_name[]')
    custom_values = request.POST.getlist('custom_spec_value[]')

    for name, value in zip(custom_names, custom_values):
        if name.strip() and value.strip():
            try:
                new_spec = PopUpProductSpecification.objects.create(
                    name=name.strip(),
                    product_type=product_instance.product_type
                )
                PopUpProductSpecificationValue.objects.create(
                    product=product_instance,
                    specification=new_spec,
                    value=value.strip()
                )
                print(f"Created custom spec {name}: {value}")
            except IntegrityError:
                existing_spec = PopUpProductSpecification.objects.get(
                    name=name.strip(),
                    product_type=product_instance.product_type
                )
                PopUpProductSpecificationValue.objects.create(
                    product=product_instance,
                    specification=existing_spec,
                    value=value.strip()
                )
                print(f"Used existing spec {name}: {value}")
