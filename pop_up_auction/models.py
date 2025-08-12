from decimal import Decimal
from django.db import models
import uuid
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta

# from .managers import CustomPopUpAccountManager  # Assuming you have a custom user manager

# Create your models here.
class PopUpBrand(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    slug = models.SlugField(max_length=255)

    class Meta:
        ordering = ("-name",)
        verbose_name = _("Pop Up Brand")
        verbose_name_plural = _("Pop Up Brands")
    

    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while PopUpBrand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # def get_absolute_url(self):
    #     return reverse("pop_up_auction:brand_list", args=[self.slug])

    def __str__(self):
        return self.name  


class PopUpCategory(MPTTModel):
    """
    Category Table inplemented with MPTT
    """
    name = models.CharField(
        verbose_name=_("Category Name"),
        help_text=_("Required and unique"),
        max_length=255,
        unique=True,
    )
    slug = models.SlugField(verbose_name=_("Category safe URL"), max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class MPTTMeta:
        order_inspection_by = ["name"]

    class Meta:
        verbose_name = _("Pop Up Category")
        verbose_name_plural = _("Pop Up Categories")

    # def get_absolute_url(self):
    #     return reverse("store:category_list", args=[self.slug])

    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while PopUpCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PopUpProductType(models.Model):
    """
    ProductType Table will proivde a list of the different types of products that are for sale.
    """
    name = models.CharField(verbose_name=_("Product Name"), help_text=_("Required"), max_length=255, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = _("PopUp Product Type")
        verbose_name_plural = _("PopUp Product Types")
    
  
    # def get_absolute_url(self):
    #     return reverse('pop_up_auction:product_list_by_category', args=[self.slug])


    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while PopUpProductType.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class PopUpProductSpecification(models.Model):
    """
    The Product Specification Table contains product specification or features for the product types.
    """
    product_type = models.ForeignKey(PopUpProductType, on_delete=models.RESTRICT)
    name = models.CharField(verbose_name=_("Name"), help_text=_("Required"), max_length=255)

    class Meta:
        verbose_name = _("PopUp Product Specification")
        verbose_name_plural = _("PopUp Product Specifications")
        unique_together = ("product_type", "name")

    def __str__(self):
        return self.name



class PopUpProduct(models.Model):
    """
    The Product table continuing all product items.
    """
    
    INVENTORY_STATUS_CHOICES = (
        ('anticipated', 'Anticipated'),
        ('in_transit', 'In Transit'),
        ('in_inventory', 'In Inventory'),
        ('reserved', 'Reserved'),
        ('sold_out', 'Sold Out')
    )


    product_type = models.ForeignKey(PopUpProductType, on_delete=models.RESTRICT)
    category = models.ForeignKey(PopUpCategory, on_delete=models.RESTRICT)
    product_title = models.CharField(
        verbose_name=_("name"),
        help_text=_("Required"),
        max_length=255,
    )
    secondary_product_title = models.CharField(
        verbose_name=_("secondary_name"),
        max_length=255,
        blank=True,
        unique=False
    )


    description = models.TextField(verbose_name=_("description"), help_text=_("Not Required"), blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    # added buy_now_price -> updated to buy_now_price, because although it's an auction site, users will have the 
    # opportunity to buy the product outright, and that starting price will be calculated by using the retail 
    # price + shipping and handling + $50. 
    buy_now_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    buy_now_start = models.DateTimeField(null=True, blank=True)
    buy_now_end = models.DateTimeField(null=True, blank=True)
    bought_now = models.BooleanField(default=False)
    reserved_until = models.DateTimeField(null=True, blank=True)
    current_highest_bid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Stores the current highest bid for this product."
    )
    

    retail_price = models.DecimalField(verbose_name=_("Retail Price"), max_digits=10, decimal_places=2,)
    brand = models.ForeignKey(PopUpBrand, related_name='products', on_delete=models.CASCADE)
    auction_start_date = models.DateTimeField(null=True, blank=True)
    auction_end_date = models.DateTimeField(null=True, blank=True)
    inventory_status = models.CharField(max_length=30, choices=INVENTORY_STATUS_CHOICES, default="anticipated")
    bid_count = models.PositiveIntegerField(default=0)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='won_auction')
    auction_finalized = models.BooleanField(default=False)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text="Set a minimum price below which product won’t be sold")

    # 'acquistion_cost' this is the price i paid for item + shipping + tax
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                           help_text="Price paid to acquire product, i.e. product + shipping + tax")

    # product_weight_lbs added. Sneaker inside box weighed before being posted. Use weight with USPS API...
    # ... to determine cost of shipping
    product_weight_lbs = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Weight in pounds for shipping calculation"
    )

    # zip_code_stored added. Whenre item being mailed from needed along with weight for USPS API to...
    # ...provide shipping estimate
    zip_code_stored = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="ZIP code of the storage or fulfillment location")

    is_active = models.BooleanField(
        verbose_name=_("Product visibility"),
        help_text=_("Change product visibility"),
        default=True,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("PopUp Product")
        verbose_name_plural = _("PopUp Products")
        indexes = [
            models.Index(fields=["auction_start_date"]),
            models.Index(fields=["auction_end_date"]),
        ]

    
    def get_absolute_url(self):
        return reverse("pop_up_auction:product_detail", args=[self.slug])
    
    

    @property
    def is_buy_now_available(self):
        now_ = now()
        return (
            self.buy_now_start and self.buy_now_end and
            self.buy_now_start <= now_ <= self.buy_now_end and
            not self.bought_now and not self.is_auction_phase()
            )

    def is_auction_phase(self):
        now_ = now()
        return (
            self.auction_start_date and self.auction_end_date and
            self.auction_start_date <= now_ <= self.auction_end_date and
            not self.is_buy_now_available
        )
    
    def is_reserved_expired(self):
        return self.reserved_until and self.reserved_until < timezone.now()


    def can_be_added_to_cart(self):
        if self.inventory_status == 'in_inventory':
            return True
        if self.inventory_status == 'reserved' and self.is_reserved_expired():
            return True
        return False


    def complete_buy_now_purchase(self, user):
        self.inventory_status = 'sold_out'
        self.bought_now = True
        self.auction_finalized = True
        self.winner = user
        self.auction_end_date = timezone.now()
        self.save()


    def display_price(self):
        """
        Determines what price to show to users depending on sale phase.
        """
        if self.bought_now:
            return self.buy_now_price
        elif self.is_buy_now_available:
            return self.buy_now_price
        elif self.auction_status == 'Ongoing':
            return self.current_highest_bid or self.reserve_price or self.retail_price
        elif self.auction_status == "Ended" and self.auction_finalized:
            return self.current_highest_bid if self.winner else None
        return self.retail_price  


    def finalize_auction(self):
        if self.bought_now or self.auction_finalized:
            return # Already sold
        
        highest_bid = self.bids.order_by('-amount').first()
        if highest_bid:
            self.winner = highest_bid.user
            self.inventory_status = 'in_inventory'
        else:
            self.winner = None
        
        self.auction_finalized = True
        self.save()
    

    # Status helper for template logic
    @property
    def sale_outcome(self):
        if self.bought_now:
            return 'Bought Now'
        elif self.auction_finalized:
            return 'Auction Finalized - Winner Pending Purchase' if self.winner else 'Auction Ended - No Bids'
        return self.auction_status

    
    
    @property
    def auction_status(self):
        if self.auction_start_date and self.auction_end_date:
            if now() < self.auction_start_date:
                return "Upcoming"
            elif self.auction_start_date <= now() <= self.auction_end_date:
                return "Ongoing"
            else:
                return "Ended"
        return "Not Available"

    @property
    def auction_duration(self):
        if self.auction_start_date and self.auction_end_date:
            # duration = self.auction_end_date - self.auction_start_date #this passes the test but doesnt work like the line below
            duration = self.auction_end_date - now() # this is needed in order for the countdown in the template
            days = duration.days
            hours = duration.seconds // 3600
            return {"days": days, "hours": hours}
        return None


    def clean(self):
        if self.buy_now_end and self.auction_start_date:
            if self.buy_now_end > self.auction_start_date:
                raise ValidationError('Buy now must end before auction starts')

    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            base_slug = slugify(self.product_title)
            slug = base_slug
            counter = 1
            while PopUpProduct.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_title



class PopUpProductSpecificationValue(models.Model):
    """
    The Product Specification Value table holds each of the products individual specificaiton or bespoke features
    """
    
    product = models.ForeignKey(PopUpProduct, on_delete=models.CASCADE)
    specification = models.ForeignKey(PopUpProductSpecification, on_delete=models.RESTRICT, )
    value = models.CharField(
        verbose_name=_("value"),
        help_text=_("Product specification value (maximum of 255 words)"),
        max_length=255,
    )

    class Meta:
        verbose_name = _("PopUp Product Specification Value")
        verbose_name_plural = _("PopUp Product Specification Values")

    def __str__(self):
        return self.value



class PopUpProductImage(models.Model):
    """
    The Product Image table.
    """
    product = models.ForeignKey(PopUpProduct, on_delete=models.CASCADE, related_name="product_image")
    image = models.ImageField(
        verbose_name=_("image"),
        help_text=_("Upload a product image"),
        upload_to="images/",
        default="images/default.png",
        null=True,
        blank=True
    )

    # External URL
    image_url = models.URLField(
        verbose_name=_("External Image URL"),
        help_text=_("Paste the URL of the image (e.g. S3, Cloudinary)"),
        blank=True,
        null=True,
    )

    alt_text = models.CharField(
        verbose_name=_("Alternative text"),
        help_text=_("Please add alternative text"),
        max_length=255,
        null=True,
        blank=True
    )
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("PopUp Product Image")
        verbose_name_plural = _("PopUp Product Images")
    

    def get_image_url(self):
        if self.image:
            return self.image
        

        # first, verify image_url (URLs externes)
        if self.image_url:
            return self.image_url
        
        # Ensuite vérifier les fichiers uploadés
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except ValueError:
                pass
        
        
        # Default fallback
        return settings.STATIC_URL + 'images/default.png'
    

    @property
    def resolved_image_url(self):
        return self.get_image_url()


    def __str__(self):
        return self.image.url if self.image and hasattr(self.image, 'url') else self.image_url or "No image"


class WinnerReservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(PopUpProduct, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    reserved_at = models.DateTimeField(auto_now_add=True)

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    is_expired = models.BooleanField(default=False)  # For background tasks to update
    notification_sent = models.BooleanField(default=False)

    # New fields
    reminder_24hr_sent = models.BooleanField(default=False)
    reminder_1hr_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "user",)  # Prevents duplicates

