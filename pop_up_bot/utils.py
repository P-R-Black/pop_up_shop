

# US Men's shoe sizes 6–15 including half sizes
MENS_SHOE_SIZES = [
    '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5',
    '10', '10.5', '11', '11.5', '12', '12.5',
    '13', '13.5', '14', '14.5', '15'
]

# US Women's shoe sizes 5–12 including half sizes
WOMENS_SHOE_SIZES = [
    '5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5',
    '9', '9.5', '10', '10.5', '11', '11.5', '12'
]

CLOTHING_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']

GAMING_SYSTEM_EDITIONS = ['Standard Edition', 'Digital Edition', 'Bundle']

MISCELLANEOUS_OPTIONS = ['Standard', 'One Size']


def get_sizes_for_product_type(product):
    """
    Returns a list of size/variant options for the procurement form
    based on the product's type slug.

    Since procurement items are not yet in inventory, we can't read
    size specs from PopUpProductSpecificationValue — so we return a
    sensible hardcoded list per product type and let the bot handle
    availability at runtime.

    Args:
        product (PopUpProduct): the product being procured

    Returns:
        list[str]: size/variant options for the <select> dropdown,
                   or an empty list if type is unrecognised
    """
    if not product.product_type:
        return MISCELLANEOUS_OPTIONS

    slug = product.product_type.slug.lower()

    if slug == 'shoe':
        # Return men's and women's sizes combined with labels so the
        # user can pick the right gendered size.
        # Format: "M-10", "W-8.5" — the bot parses the prefix.
        mens   = [f"Men's {s}"   for s in MENS_SHOE_SIZES]
        womens = [f"Women's {s}" for s in WOMENS_SHOE_SIZES]
        return mens + womens

    if slug == 'clothing':
        return CLOTHING_SIZES

    if slug == 'gaming-system':
        return GAMING_SYSTEM_EDITIONS

    if slug == 'miscellaneous':
        return MISCELLANEOUS_OPTIONS

    # Fallback — unknown product type gets a generic option
    return MISCELLANEOUS_OPTIONS


def get_procurement_service_product():
    """
    Returns the singleton PopUpProduct representing the $15 procurement
    service fee. Run create_procurement_product management command first.
    """
    from pop_up_auction.models import PopUpProduct
    return PopUpProduct.objects.get(slug='procurement-service-fee')