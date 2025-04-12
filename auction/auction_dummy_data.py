"""
    class PopUpProduct(models.Model):
    
    # The Product table continuing all product items.
    
    INVENTORY_STATUS_CHOICES = (
        ('anticipated', 'Anticipated'),
        ('in_transit', 'In Transit'),
        ('in_inventory', 'In Inventory')
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
    # replaced retail_price with starting_price, because although it's an auction site, users will have the 
    # opportunity to buy the product outright, and that starting price will be calculated by using the retail 
    # price + shipping and handling + $50. 
    starting_price = models.DecimalField( verbose_name=_("Regular price"), max_digits=10, decimal_places=2)

    
    # Don't need discount price
    # discount_price = models.DecimalField(
    #     verbose_name=_("Discount price"),
    #     help_text=_("Maximum 999.99"),
    #     error_messages={
    #         "name": {
    #             "max_length": _("The price must be between 0 and 999.99."),
    #         },
    #     },
    #     max_digits=5,
    #     decimal_places=2,
    # )

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
            duration = self.auction_end_date - self.auction_start_date
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
"""

test_account_data = [

    {
        "id": "0123232445",
        "product_type": "shoe",
        "category": "Jordan 11",
        "product_title": "Jordan 11 Retro",
        "secondary_product_title": "Gamma Blue",
        "description": "The top of the Retro Gamma Blue has a black finish throughout and is made of a customary combination of ballistic net and slick patent leather. The sneaker's branding features include the number '23' engraved in Varsity Maize and a turquoise Jumpman on the heel tab. A top-loaded full-length Air unit is added to the plush Phylon midsole, which is supported by a carbon fiber spring plate. Herringbone suction pods are used on a translucent rubber outsole.",
        "slug": "jordan-11-retro-gamma-blue",
        "regular_price": "255.00",
        "retail_price":"185.00",
        "brand":"Jordan",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_inventory",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": True,
        "style_number": "378037-006",
        "colorway": "Black/Gamma Blue-Varsity Maize",
        "model_year": "2013",
        "release_date": "12/21/2013",
        "size": "9",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744429406/the_pop_up/j11._zfitg7.png",
        "alternative_text": "Jordan 11 Retro Gamma Blue",
        "is_feature": "True"

   },
   {
        "id": "0135246451",
        "product_type": "shoe",
        "category": "Jordan 11",
        "product_title": "Jordan 11 Retro",
        "secondary_product_title": "Legend Blue",
        "description": "The Jordan 11 Retro Legend Blue (2024), also known as the Columbia 11s, is easily one of the most well known and beloved colorways of the Jordan 11 ever produced. Dating back to 1996, this sneaker has only retro'd twice since then, with the latest version being 10 years ago in 2014..",
        "slug": "jordan-11-retro-legend-blue",
        "regular_price": "310.00",
        "retail_price": "230",
        "brand": "Jordan",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_inventory",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": True,
        "style_number": "CT8012-104",
        "colorway": "White/Legend Blue/Black",
        "model_year": "2024",
        "release_date": "12/14/2024",
        "size": "8",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430166/the_pop_up/SneakerTwo_wliina.png",
        "alternative_text": "Jordan 11 Retro Gamma Blue",
        "is_feature": "True"

   }
]