from .models import PopUpCategory

def categories(request):
    return { 'categories': PopUpCategory.objects.all()}