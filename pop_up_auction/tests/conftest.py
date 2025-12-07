from pop_up_auction.models import PopUpProductSpecificationValue, PopUpProductSpecification
from pop_accounts.models import (PopUpCustomerProfile, SoftDeleteManager, 
                                 PopUpCustomerAddress, PopUpBid)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType)
from pop_up_order.models import (PopUpCustomerOrder)
from pop_up_shipping.models import PopUpShipment
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from pop_up_payment.models import PopUpPayment
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from decimal import Decimal
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify


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


def create_test_user(email, password, first_name, last_name, shoe_size, size_gender, **kwargs):
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        **kwargs
    )
    profile = PopUpCustomerProfile.objects.get(user=user)    
    profile.shoe_size = shoe_size
    profile.size_gender = size_gender
    profile.save()


    return user, profile

def create_test_user_two():
    return User.objects.create_user(
            email="testuse2r@example.com",
            password="securePassword!232",
            first_name="Test2",
            last_name="User2",
        )

# create staff user
def create_test_staff_user(email, password, first_name, last_name, shoe_size, size_gender, **kwargs):
    staff_user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
        is_active=True
    )
    staff_profile = PopUpCustomerProfile.objects.get(user=staff_user)    
    staff_profile.shoe_size = shoe_size
    staff_profile.size_gender = size_gender
    staff_profile.save()


    return staff_user, staff_profile

def create_test_address(customer, first_name, last_name, address_line, address_line2, apartment_suite_number, 
                        town_city, state, postcode, delivery_instructions, default=True, is_default_shipping=False,
                        is_default_billing=False):
    return PopUpCustomerAddress.objects.create(
            customer=customer,
            first_name=first_name,
            last_name=last_name,
            address_line=address_line,
            address_line2=address_line2,
            apartment_suite_number=apartment_suite_number,
            town_city=town_city,
            state=state,
            postcode=postcode,
            delivery_instructions=delivery_instructions,
            default=default,
            is_default_shipping=is_default_shipping,
            is_default_billing=is_default_billing
        )

def create_brand(name):
    return PopUpBrand.objects.create(
        name=name,
        slug=slugify(name)
    )

def create_category(name, is_active):
    return PopUpCategory.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )


def create_product_type(name, is_active):
    return PopUpProductType.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )

def create_test_product(product_type, category, product_title, secondary_product_title, description, slug, 
                        buy_now_price, current_highest_bid, retail_price, brand, auction_start_date, 
                        auction_end_date, inventory_status, bid_count, reserve_price, is_active, *args, **kwargs
                        ):
        
        return PopUpProduct.objects.create(
            product_type=product_type,
            category=category,
            product_title=product_title,
            secondary_product_title= secondary_product_title,
            description=description,
            slug=slug, 
            buy_now_price=buy_now_price, 
            current_highest_bid=current_highest_bid, 
            retail_price=retail_price, 
            brand=brand, 
            auction_start_date=auction_start_date, 
            auction_end_date=auction_end_date, 
            inventory_status=inventory_status, 
            bid_count=bid_count, 
            reserve_price=reserve_price, 
            is_active=is_active
        )



def create_test_product_one(*args, **kwargs):
    # Set default values
    defaults = {
        'product_type': create_product_type('shoe', is_active=True),
        'category': create_category('Jordan 3', is_active=True),
        'product_title': "Past Bid Product 1",
        'secondary_product_title': "Past Bid 1",
        'description': "Brand new sneakers",
        'slug': "past-bid-product-1",
        'buy_now_price': "250.00",
        'current_highest_bid': "0",
        'retail_price': "150.00",
        'brand': create_brand('Jordan'),
        'auction_start_date': None,
        'auction_end_date': None,
        'inventory_status': "sold_out",  # Default value
        'bid_count': 0,
        'reserve_price': "100.00",
        'is_active': False  # Default value
    }
    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpProduct.objects.create(**defaults)


def create_test_product_two(*args, **kwargs):
    # Set default values
    defaults = {
        'product_type': "", 'category': create_category('Jordan IV', is_active=True),
        'product_title': "Past Bid Product 2", 'secondary_product_title': "Past Bid 2",
        'description': "Brand new sneakers", 'slug': "past-bid-product-2", 'buy_now_price': "300.00", 
        'current_highest_bid': "0", 'retail_price': "200.00", 'brand': "", 'auction_start_date': None, 
        'auction_end_date': None, 'inventory_status': "sold_out", 'bid_count': 0, 'reserve_price': "150.00",
        'is_active': False  # Default value
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpProduct.objects.create(**defaults)




def create_test_product_three(*args, **kwargs):
        # Set default values
        defaults = {
            'product_type': create_product_type('gaming system', is_active=True), 
            'category': create_category('Switch', is_active=True), 'product_title': "Switch 2", 
            'secondary_product_title': "", 'description': "New Nintendo Switch 2", 
            'slug': "switch-2", 'buy_now_price': "350.00", 'current_highest_bid': "0", 
            'retail_price': "250.00", 'brand': create_brand('Nintendo'), 'auction_start_date': None, 
            'auction_end_date': None, 'inventory_status': "in_inventory", 'bid_count': 0, 
            'reserve_price': "225.00",
            'is_active': False  # Default value
        }

        # Override defaults with any kwargs passed in
        defaults.update(kwargs)
        
        # Create and return the product
        return PopUpProduct.objects.create(**defaults)



def create_test_shipping_address_one(*args, **kwargs):
    return PopUpCustomerAddress.objects.create(
            first_name='John',
            last_name='Doe',
            address_line='123 Test St',
            town_city='Test City',
            state='Tennessee',
            postcode='12345',
            **kwargs,
        )

def create_test_order_one(*args, **kwargs):
    return PopUpCustomerOrder.objects.create(
            billing_status=True,
            address1="111 Test St",
            city="New York",
            state="NY",
            postal_code="10001",
            total_paid="100.00",
            **kwargs
        )

def create_test_order_two(*args, **kwargs):
    return PopUpCustomerOrder.objects.create(
            billing_status=True,
            address1="123 Test St",
            city="South Ozone Park",
            state="NY",
            postal_code="11434",
            total_paid="100.00",
            **kwargs
    )

def create_test_shipment_one(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': 'USPS', 'tracking_number': '1Z999AA10123456784', 
        'shipped_at': datetime(2024, 1, 15, tzinfo=dt_timezone.utc),
        'estimated_delivery': datetime(2024, 1, 20, tzinfo=dt_timezone.utc), 
        'delivered_at': None, 'status': 'pending',
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpShipment.objects.create(**defaults)

    
    # return PopUpShipment.objects.create(
    #     carrier='USPS',
    #     tracking_number='1Z999AA10123456784',
    #     # shipped_at=None,
    #     # estimated_delivery=None,
    #     shipped_at=datetime(2024, 1, 15, tzinfo=dt_timezone.utc),
    #     estimated_delivery=datetime(2024, 1, 20, tzinfo=dt_timezone.utc),
    #     delivered_at=None,
    #     status=status, # pending, cancelled, in_dispute, shipped, returned, delivered
    #     **kwargs
    # )


def create_test_shipment_pending(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': '',  
        'tracking_number': '',
        'shipped_at': None, 
        'estimated_delivery': None,
        'delivered_at': None, 
        'status': 'pending',  # ✅ Truly pending
    }
    defaults.update(kwargs)
    return PopUpShipment.objects.create(**defaults)


def create_test_shipment_two_pending(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': 'USPS', 'tracking_number': '1Z999AA10123456784', 
        'shipped_at': None,
        'estimated_delivery': None, 
        'delivered_at': None, 'status': 'pending'
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpShipment.objects.create(**defaults)


def create_test_payment_one(order, amount, status, payment_method, suspicious_flagged, notified_ready_to_ship):
        return PopUpPayment.objects.create(
            order=order,
            amount=Decimal(amount),
            status=status,
            payment_method=payment_method,
            suspicious_flagged=suspicious_flagged,
            notified_ready_to_ship=notified_ready_to_ship
        )
