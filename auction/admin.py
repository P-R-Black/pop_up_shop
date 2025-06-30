from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import (PopUpProduct, PopUpCategory, PopUpProductSpecification, PopUpProductType, 
                     PopUpProductSpecificationValue, PopUpProductImage, PopUpBrand, WinnerReservation
)


admin.site.register(PopUpCategory, MPTTModelAdmin)
class ProductSpecificationInline(admin.TabularInline):
    model = PopUpProductSpecification


@admin.register(PopUpProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    inlines = [
        ProductSpecificationInline,
               ]


class ProductImageInline(admin.TabularInline):
    model = PopUpProductImage


class ProductSpecificationValueInline(admin.TabularInline):
    model = PopUpProductSpecificationValue


@admin.register(PopUpProduct)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ProductSpecificationValueInline,
        ProductImageInline,
    ]
    list_display = ['product_title', 'secondary_product_title', 'slug']

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('product_title',)}


@admin.register(PopUpBrand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}
 
    
@admin.register(WinnerReservation)
class WinnerReservationAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "is_paid", "is_expired", "expires_at")
    list_filter = ("is_expired", "is_paid")