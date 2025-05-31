from decimal import Decimal
from django.db import models
import uuid
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now
from django.utils.text import slugify

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
            base_slug = slugify(self.product_title)
            slug = base_slug
            counter = 1
            while PopUpBrand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("auction:brand_list", args=[self.slug])

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

    def get_absolute_url(self):
        return reverse("store:category_list", args=[self.slug])

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
        verbose_name = _("Product Type")
        verbose_name_plural = _("Product Types")
    
  
    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])


    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            base_slug = slugify(self.product_title)
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
        verbose_name = _("Product Specification")
        verbose_name_plural = _("Product Specifications")
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
    # added starting_price, because although it's an auction site, users will have the 
    # opportunity to buy the product outright, and that starting price will be calculated by using the retail 
    # price + shipping and handling + $50. 
    starting_price = models.DecimalField( verbose_name=_("Regular price"), max_digits=10, decimal_places=2)
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
    # reserve_price - I can set a minimum price below which they won’t sell, add:
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(
        verbose_name=_("Product visibility"),
        help_text=_("Change product visibility"),
        default=True,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        indexes = [
            models.Index(fields=["auction_start_date"]),
            models.Index(fields=["auction_end_date"]),
        ]

    
    def get_absolute_url(self):
        return reverse("auction:product_detail", args=[self.slug])

    @property
    def calculated_starting_price(self):
        return self.retail_price + Decimal(70)
    
    
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

    from datetime import timedelta


    @property
    def auction_duration(self):
        if self.auction_start_date and self.auction_end_date:
            # duration = self.auction_end_date - self.auction_start_date #this passes the test but doesnt work like the line below
            duration = self.auction_end_date - now() # this is needed in order for the countdown in the template
            days = duration.days
            hours = duration.seconds // 3600
            return {"days": days, "hours": hours}
        return None


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
        verbose_name = _("Product Specification Value")
        verbose_name_plural = _("Product Specification Values")

    def __str__(self):
        return self.value
    
    class Meta:
        verbose_name = _("Product Specification Value")
        verbose_name_plural = _("Product Specification Values")

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
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
