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
        "description": "The Jordan 11 Retro Legend Blue (2024), also known as the Columbia 11s, is easily one of the most well known and beloved colorways of the Jordan 11 ever produced. Dating back to 1996, this sneaker has only retro'd twice since then, with the latest version being 10 years ago in 2014.",
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

   },
    {
        "id": "0135246451",
        "product_type": "shoe",
        "category": "Dunk",
        "product_title": "Nike SB Dunk Low",
        "secondary_product_title": "Yuto Horigome Matcha",
        "description": "The Nike SB Dunk Low Yuto Horigome Matcha brings a fresh, nature-inspired take to a classic skateboarding silhouette. Inspired by the shades of green found in matcha, this sneaker blends earthy tones across its premium suede and leather upper. Deep legion green and burnt sienna accents add contrast, while the light khaki base keeps the design grounded and wearable.",
        "slug": "nike-sb-dunk-low-yuto-horigome-matcha",
        "regular_price": "205.00",
        "retail_price": "135.00",
        "brand": "Nike",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_transit",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "style_number": "HF8022-300",
        "colorway": "Asparagus/Legion Green/Light Khaki/Dark Loden/Sesame/Burnt Sienna",
        "model_year": "2025",
        "release_date": "04/05/2025",
        "size": "9",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430269/the_pop_up/matchDunks_rjpwjd.png",
        "alternative_text": "Nike SB Dunk Low Yuto Horigome Matcha",
        "is_feature": "True"

   },
   {
        "id": "0135246451",
        "product_type": "shoe",
        "category": "Jordan 1",
        "product_title": "Jordan 1 Retro High",
        "secondary_product_title": "OG Rare Air",
        "description": "The Jordan 1 Retro High OG Rare Air pays homage to the original 1985 design with a contemporary twist, blending classic elements with modern updates. This iteration features a white leather base complemented by neutral grey collars and overlays, reminiscent of the OG 'Storm Blue' colorway. Deep royal blue accents on the ankle flaps and outsole inject a vibrant touch, while the wear-away black Swooshes reveal a layer of red beneath, adding a dynamic and customizable aspect to the sneaker’s aesthetic.",
        "slug": "nike-sb-dunk-low-yuto-horigome-matcha",
        "regular_price": "250.00",
        "retail_price": "180.00",
        "brand": "Jordan",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_transit",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "style_number": "DZ5485-100",
        "colorway": "White/Black-Neutral Grey-Deep Royal Blue-Muslin",
        "model_year": "2025",
        "release_date": "04/05/2025",
        "size": "10",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430268/the_pop_up/rare_airs_ith5ns.png",
        "alternative_text": "Jordan 1 Retro High OG Rare Air",
        "is_feature": "True"

   },
   {
        "id": "0135246451",
        "product_type": "shoe",
        "category": "Jordan 3",
        "product_title": "A Ma Maniere x Air Jordan 3",
        "secondary_product_title": '"For The Love"',
        "description": "Release date pending.",
        "slug": "a-ma-maniere-x-air-jordan-3-for-the-love",
        "regular_price": "305.00",
        "retail_price": "225.00",
        "brand": "Jordan",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "anticipated",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "style_number": "HV8571-100",
        "colorway": "White/Diffused Blue-Anthracite-Muslin",
        "model_year": "2025",
        "release_date": "04/15/2025",
        "size": "0",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430191/the_pop_up/j3_ma_maniere_lsqnvo.png",
        "alternative_text": "A Ma Maniere x Air Jordan 3 'For The Love' ",
        "is_feature": "True"
   },
    {
        "id": "0135555451",
        "product_type": "shoe",
        "category": "Jordan 3",
        "product_title": "Jordan 3 Retro",
        "secondary_product_title": "OG Rare Air",
        "description": "Release date pending.",
        "slug": "jordan-3-retro-og-rare-air",
        "regular_price": "280.00",
        "retail_price": "210.00",
        "brand": "Jordan",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "anticipated",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "style_number": "pending",
        "colorway": "Black/Chile Red/Neutral Grey/Military Blue/Coconut Milk",
        "model_year": "2025",
        "release_date": "04/12/2025",
        "size": "pending",
        "product_sex": "Male",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430270/the_pop_up/Jordan3Rares_ubsaep.png",
        "alternative_text": "Jordan 3 Retro OG Rare Air",
        "is_feature": "True"
   },
    {
        "id": "0005555425",
        "product_type": "shoe",
        "category": "Sabrina",
        "product_title": "Nike Sabrina 2",
        "secondary_product_title": "Titan Make Space",
        "description": "Release date pending.",
        "slug": "nike-sabrina-2-titan-make-space",
        "regular_price": "210.00",
        "retail_price": "140.00",
        "brand": "Nike",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "anticipated",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "style_number": "pending",
        "colorway": "Light Bone/Racer Pink/Calypso/Teal Tint/Purple Agate/Twilight Pulse",
        "model_year": "2025",
        "release_date": "04/15/2025",
        "size": "pending",
        "product_sex": "Female",
        "condition": "new",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430268/the_pop_up/S2_fliwvg.png",
        "alternative_text": "Nike Sabrina 2 Titan Make Space",
        "is_feature": "True"
   },
   {
        "id": "2344346401",
        "product_type": "miscellaneous",
        "category": "Collectable",
        "product_title": "Supreme SpyraThree",
        "secondary_product_title": "Water Blaster",
        "description": "Fully automated collectable water blaster.",
        "slug": "supreme-spyrathree-water-blaster",
        "regular_price": "280.00",
        "retail_price": "200.00",
        "brand": "Supreme",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "anticipated",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "sku": "SP332221",
        "color": "Red/black",
        "model_year": "2025",
        "release_date": "05/20/2025",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744510654/the_pop_up/waterG_no1hqo.png",
        "alternative_text": "Supreme SpyraThree Water Blaster",
        "is_feature": "True"
   },
   {
        "id": "2315246451",
        "product_type": "gaming system",
        "category": "PS5",
        "product_title": "Sony PlayStation 5",
        "secondary_product_title": "PS5 Pro Console (U.S.)",
        "description": "The Sony PlayStation 5 PS5 Pro Console (US Plug) brings next-gen gaming to life with enhanced performance features. With a GPU that boasts 67% more Compute Units than the original PS5, this console provides up to 45% faster rendering, ensuring smoother gameplay and more dynamic visuals. Whether you're exploring vast open worlds or battling it out in fast-paced multiplayer games, the PS5 Pro's powerful hardware delivers a truly immersive experience.",
        "slug": "sony-playstation-5-ps5-pro-console-us",
        "regular_price": "779.00",
        "retail_price": "699.00",
        "brand": "Sony",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_transit",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "mpn": "sne8287361e",
        "color": "white",
        "model_year": "2025",
        "battery_life": "N/A",
        "platform": "Sony",
        "power_supply_region": "U.S.",
        "storage_capacity": "2TB",
        "storage_type": "SSD",
        "screen_size": "N/A",
        "ports": "USB Type-C, USB Type-A",
        "graphics": "2160p",
        "release_date": "11/07/2024",
        "memory": "16GB",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430266/the_pop_up/ps5_tw6boc.png",
        "alternative_text": "Sony PlayStation 5 PS5 Pro Console (U.S.)",
        "is_feature": "True"
   },
   {
        "id": "2311588651",
        "product_type": "clothing",
        "category": "Jacket",
        "product_title": "Pacsun Fear of God Wool Varsity Jacket",
        "secondary_product_title": "",
        "description": "Pacsun/Fear of God wool varsity jacket. The wool varsity jacket has front hand pockets, striped detailing, a bold FOG - Fear Of God "F" patch on the chest, a full-length snap button front, and ribbed detailing at the neck, cuffs, and hem. Wool varsity-style jacket FOG - Fear Of God "F" patch on chest.",
        "slug": "pacsun-fear-of-god-wool-varsity-jacket",
        "regular_price": "450.00",
        "retail_price": "300.00",
        "brand": "Pacsun + Fear of God",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "in_transit",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "sytle_number": "fog437168",
        "colorway": "Dark Navy/Gray",
        "model_year": "2020",
        "release_date": "1/1/2020",
        "size": "Medium",
        "condition": "New",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430203/the_pop_up/fogVarsity_nxe5vi.png",
        "alternative_text": "Pacsun Fear of God Wool Varsity Jacket",
        "is_feature": "True"
   },{
        "id": "2300226451",
        "product_type": "gaming system",
        "category": "Switch",
        "product_title": "Nintendo Switch 2",
        "secondary_product_title": "",
        "description": "TThe Nintendo Switch 2 is a hybrid console that can be used as a handheld, a tablet-like device, or docked when connected to an external display, using detachable Joy-Con controllers to switch between modes.",
        "slug": "nintendo-switch-2",
        "regular_price": "519.00",
        "retail_price": "449.00",
        "brand": "Nintendo",
        "auction_start_date":"",
        "auction_end_date":"",
        "inventory_status": "anticipated",
        "bid_count": "0",
        "reserve_price": "",
        "is_active": False,
        "mpn": "0000-000",
        "color": "Black",
        "model_year": "2025",
        "battery_life": "2 - 6.5 hours",
        "platform": "Nintendo",
        "power_supply_region": "U.S.",
        "storage_capacity": "256GB",
        "storage_type": "Internal HD",
        "screen_size": "7.9-inch",
        "ports": "USB, HDMI",
        "graphics": "1080p",
        "release_date": "",
        "memory": "12GB of LPDDR5X RAM",
        "image": "https://res.cloudinary.com/prblack/image/upload/v1744430266/the_pop_up/switch2_gjrsvi.png",
        "alternative_text": "Nintendo Switch 2",
        "is_feature": "True"
   },
]