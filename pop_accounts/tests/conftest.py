from pop_up_auction.models import PopUpProductSpecificationValue, PopUpProductSpecification
from pop_accounts.models import (PopUpCustomer,PopUpBid, CustomPopUpAccountManager, SoftDeleteManager, PopUpCustomerAddress)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType)
from decimal import Decimal
from django.utils.timezone import now
from datetime import datetime, timedelta


def create_seed_data():
    brand = PopUpBrand.objects.create(name='Jordan', slug='jordan')
    cat = PopUpCategory.objects.create(name='Jordan 1', slug='jordan-1')
    prod_type = PopUpProductType.objects.create(name='shoe', slug='shoe')
    product = PopUpProduct.objects.create(
        # id=uuid.uuid4(),
        product_type=prod_type,
        category=cat,
        product_title='Jordan 1',
        secondary_product_title = 'Retro High',
        description = 'Test shoe',
        slug='j1-retro',
        buy_now_price=Decimal('250'),
        retail_price=Decimal('120'),
        brand=brand,
        auction_start_date=now() - timedelta(days=1),
        auction_end_date=now() + timedelta(days=6),
        inventory_status='in_inventory',
        is_active=True
    )

    # Create default specifications for this product type
    color_spec = PopUpProductSpecification.objects.create(
        product_type=prod_type,
        name='colorway'
    )
    size_spec = PopUpProductSpecification.objects.create(
        product_type=prod_type,
        name='size'
    )

    # Optionally, you can attach default values to the product
    PopUpProductSpecificationValue.objects.create(
        product=product,
        specification=color_spec,
        value='Black/Red'
    )
    PopUpProductSpecificationValue.objects.create(
        product=product,
        specification=size_spec,
        value='10'
    )

    user1 = PopUpCustomer.objects.create_user(
        email="user1@example.com", password="passWord!1", first_name="One", last_name="User", is_active=True
    )

    user2 = PopUpCustomer.objects.create_user(
        email="user2@example.com", password="passWord@2", first_name="Two", last_name="User", is_active=True
    )
    return product, color_spec, size_spec, user1, user2
