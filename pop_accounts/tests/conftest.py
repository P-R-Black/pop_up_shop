from pop_up_auction.models import PopUpProductSpecificationValue, PopUpProductSpecification
from pop_accounts.models import (PopUpCustomerProfile, SoftDeleteManager, 
                                 PopUpCustomerAddress, PopUpBid)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType)
from decimal import Decimal
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


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

    user1 = User.objects.create_user(
        email="user1@example.com", password="passWord!1", first_name="One", middle_name="M", last_name="User", is_active=True
    )
    profile_one = PopUpCustomerProfile.objects.get(user=user1)    
    profile_one.shoe_size = "9"
    profile_one.size_gender = "male"
    profile_one.save()

    user2 = User.objects.create_user(
        email="user2@example.com", password="passWord@2", first_name="Two",middle_name="T", last_name="User", is_active=True
    )
    profile_two = PopUpCustomerProfile.objects.get(user=user2)    
    profile_two.shoe_size = "6"
    profile_two.size_gender = "female"
    profile_two.save()
    return product, color_spec, size_spec, user1, profile_one, user2, profile_two


def create_seed_data_two():
    brand = PopUpBrand.objects.create(name='Lebron', slug='lebron')
    cat = PopUpCategory.objects.create(name='Lebron 1', slug='lebron-1')
    prod_type = PopUpProductType.objects.create(name='shoe', slug='shoe')

    product = PopUpProduct.objects.create(
        # id=uuid.uuid4(),
        product_type=prod_type,
        category=cat,
        product_title='Lebron 1',
        secondary_product_title = 'Rookie Retro',
        description = 'Test shoe',
        slug='l1-rookie-retro',
        buy_now_price=Decimal('250'),
        retail_price=Decimal('120'),
        brand=brand,
        auction_start_date=now() - timedelta(days=1),
        auction_end_date=now() + timedelta(days=6),
        inventory_status='in_inventory',
        is_active=True
    )

    product_two = PopUpProduct.objects.create(
        # id=uuid.uuid4(),
        product_type=prod_type,
        category=cat,
        product_title='Lebron 1',
        secondary_product_title = 'Witness Retro',
        description = 'Test shoe',
        slug='l1-witness-retro',
        buy_now_price=Decimal('270'),
        retail_price=Decimal('150'),
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

     # Optionally, you can attach default values to the product
    PopUpProductSpecificationValue.objects.create(
        product=product_two,
        specification=color_spec,
        value='White/Red'
    )

    PopUpProductSpecificationValue.objects.create(
        product=product_two,
        specification=size_spec,
        value='9'
    )

    user1 = User.objects.create_user(
        email="user1@example.com", password="passWord!1", first_name="One", middle_name="M", last_name="User", is_active=True
    )
    profile_one = PopUpCustomerProfile.objects.get(user=user1)    
    profile_one.shoe_size = "9"
    profile_one.size_gender = "male"
    profile_one.favorite_brand="nike"
    profile_one.save()

    user2 = User.objects.create_user(
        email="user2@example.com", password="passWord@2", first_name="Two",middle_name="T", last_name="User", is_active=True
    )
    profile_two = PopUpCustomerProfile.objects.get(user=user2)    
    profile_two.shoe_size = "6"
    profile_two.size_gender = "female"
    profile_two.favorite_brand = "puma"
    profile_two.save()

    return product, product_two, color_spec, size_spec, user1, profile_one, user2, profile_two
