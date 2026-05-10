from .pop_up_home_copy.footer_links_copy.footer_links_copy import (
    FOOTER_COLUMN_ABOUT, BOTTOM_FOOTER_LINKS, FOOTER_COLUMN_HELP, FOOTER_COLUMN_REGISTER)
from django.utils import timezone

def footer_links(request):
    footer_column_about = FOOTER_COLUMN_ABOUT
    footer_column_help = FOOTER_COLUMN_HELP
    footer_column_register = FOOTER_COLUMN_REGISTER
    bottom_footer_links = BOTTOM_FOOTER_LINKS

    curr_date = timezone.now().date()
    curr_year = curr_date.year
    
    return {"bottom_footer_links": bottom_footer_links, "footer_column_about": footer_column_about, 
            "footer_column_help": footer_column_help, "footer_column_register": footer_column_register,
            "curr_year": curr_year}