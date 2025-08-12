from django import forms
from pop_up_auction.models import (PopUpBrand, PopUpCategory, PopUpProductType, PopUpProductSpecification, 
                            PopUpProductSpecificationValue, PopUpProduct, PopUpProductImage)
from mptt.forms import TreeNodeChoiceField



class PopUpBrandForm(forms.ModelForm):
    name = forms.CharField(label="Brand Name", max_length=255,  required=False, widget=forms.TextInput(
        attrs={
            'class': 'pop_up_product_brand_name',
            'id': 'pop_up_product_brand_name',
            'placeholder': 'Add New Brand Name',
    }))
    
    class Meta:
        model = PopUpBrand
        fields = ['name']
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name.lower()
        return name


class PopUpCategoryForm(forms.ModelForm):
    name = forms.CharField(label="Category", max_length=255, required=False,
                           widget=forms.TextInput(attrs={
                               'class': 'pop_up_product_category',
                               'id': 'pop_up_product_category',
                               'placeholder': 'Add New Category',
                           }))
    
    is_active = forms.CheckboxInput()
    parent = TreeNodeChoiceField(queryset=PopUpCategory.objects.all(), required=False)


    class Meta:
        model = PopUpCategory
        fields = ['name', 'is_active', 'parent']
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name.lower()
        return name


class PopUpProductTypeForm(forms.ModelForm):
    name = forms.CharField(label="Product Type", max_length=255, required=True, widget=forms.TextInput(
        attrs={
            'class': 'pop_up_product_type',
            'id': 'pop_up_product_type',
            'placeholder': 'Add New Product Type',
            }))
    
    is_active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput())

    class Meta:
        model = PopUpProductType
        fields = ['name', 'is_active']
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name.lower()
        return name



class PopUpProductSpecificationForm(forms.ModelForm):

    class Meta:
        model = PopUpProductSpecification
        fields = ['product_type', 'name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Model Year'}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        product_type = cleaned_data.get("product_type")

        if PopUpProductSpecification.objects.filter(name=name, product_type=product_type).exists():
            raise forms.ValidationError("This specification already exists for the selected product type.")



class PopUpAddProductForm(forms.ModelForm):
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'product_add_checkbox'})
    )

    bought_now = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'product_add_checkbox'})
    )

    auction_finalized = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'product_add_checkbox',})
    )
  
    class Meta:
        model = PopUpProduct
        fields = ['product_type', 'category', 'product_title', 'secondary_product_title', 'description', 
                  'buy_now_price', 'buy_now_start', 'buy_now_end', 'bought_now', 'reserved_until', 
                  'current_highest_bid', 'retail_price', 'brand', 'auction_start_date', 'auction_end_date', 
                  'inventory_status', 'bid_count', 'winner', 'auction_finalized', 'reserve_price', 
                  'product_weight_lbs', 'zip_code_stored', 'is_active',
                  #'acquisition_cost', 
                  ]
    

        widgets = {
                'product_type': forms.Select(attrs={'class': 'product_add_select'}),
                'category': forms.Select(attrs={'class': 'product_add_select'}),
                'product_title': forms.TextInput(attrs={
                    'class': 'product_add_long', 'placeholder': 'Product Title'
                }),
                'secondary_product_title': forms.TextInput(attrs={
                    'class': 'product_add_long', 'placeholder': 'Secondary Product Title', 
                }),
                'description': forms.Textarea(attrs={
                    'class': 'product_add_description', 'placeholder': 'Description', 'rows': 3
                }),
                'buy_now_price': forms.NumberInput(attrs={'class': 'product_add_short',
                                                          'placeholder': 'Buy Now Price'}),
                'buy_now_start': forms.DateTimeInput(attrs={
                    'type': 'datetime-local', 'class': 'product_add_date_time'
                }),
                'buy_now_end': forms.DateTimeInput(attrs={
                    'type': 'datetime-local', 'class': 'product_add_date_time'
                }),
                
                'reserved_until': forms.DateTimeInput(attrs={
                    'type': 'datetime-local', 'class': 'product_add_date_time'
                }),
                'current_highest_bid': forms.NumberInput(attrs={'class': 'product_add_short'}),
                'retail_price': forms.NumberInput(attrs={'class': 'product_add_short', 'placeholder': 'Retail Price'}),
                'brand': forms.Select(attrs={'class': 'product_add_select'}),
                'auction_start_date': forms.DateTimeInput(attrs={
                    'type': 'datetime-local', 'class': 'product_add_date_time'
                }),
                'auction_end_date': forms.DateTimeInput(attrs={
                    'type': 'datetime-local', 'class': 'product_add_date_time'
                }),
                'inventory_status': forms.Select(attrs={'class': 'product_add_select'}),
                'bid_count': forms.NumberInput(attrs={'class': 'product_add_short'}),
                'winner': forms.Select(attrs={'class': 'product_add_select'}),
               
                'reserve_price': forms.NumberInput(attrs={'class': 'product_add_short', 'placeholder': 'Reserve Price'}),
                'product_weight_lbs': forms.NumberInput(attrs={'class': 'product_add_short'}),
                'zip_code_stored': forms.TextInput(attrs={'class': 'product_add_short'}),
            }


class PopUpProductImageForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    is_feature = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'product_add_checkbox'})
    )

    class Meta:
        model = PopUpProductImage
        fields = ['image', 'image_url', 'alt_text', 'is_feature']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'product_add_image_input',
                'title': 'Upload a local image (leave blank if using URL)'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'product_add_short',
                'placeholder': 'https://example-bucket.s3.amazonaws.com/image.jpg'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'product_add_short',
                'placeholder': 'Alt text for accessibility'
            }),
            
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')

        # Check if image actually has content
        has_image = image and hasattr(image, 'size') and image.size > 0
        
        # Check if image_url actually has content
        has_image_url = bool(image_url and image_url.strip())

        if has_image and has_image_url:
            raise forms.ValidationError("Please upload an image OR provide a URL — not both.")
        
        # if has_image_url and not has_image:
        #     raise forms.ValidationError("Please upload an image OR provide a URL — not both.")
            
        # Require at least one
        if not has_image and not has_image_url:
            raise forms.ValidationError("Please provide either an image upload or an image URL.")
        
        return cleaned_data
"""
 cleaned_data = super().clean()
        image = cleaned_data.get("image")
        image_url = cleaned_data.get("image_url")

        # Treat empty file input or empty URL as None
        if not image or image == '':
            image = None
        if not image_url or image_url == '':
            image_url = None

        if not image and not image_url:
            raise forms.ValidationError("Please provide either an uploaded image or an image URL.")
        if image and image_url:
            raise forms.ValidationError("Please provide only one image source: upload OR URL.")

        # Assign back to cleaned_data (in case other logic relies on it)
        cleaned_data['image'] = image
        cleaned_data['image_url'] = image_url

        return cleaned_data
"""
    

class PopUpProductSpecificationValueForm(forms.ModelForm):
    class Meta:
        model = PopUpProductSpecificationValue
        fields = ['product', 'specification', 'value']

        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'specification': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter specification value (e.g. 2023, HDMI, 1TB)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        specification = cleaned_data.get("specification")
        value = cleaned_data.get("value")

        # Prevent duplicate spec entries for the same product/spec combo
        if PopUpProductSpecificationValue.objects.filter(
            product=product, specification=specification
        ).exists():
            raise forms.ValidationError(
                f"This product already has a value for the '{specification}' specification."
            )

        return cleaned_data
