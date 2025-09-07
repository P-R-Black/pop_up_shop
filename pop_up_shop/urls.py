"""
URL configuration for pop_up_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar


urlpatterns = [
    path('', include('pop_up_home.urls', namespace='home')),
    path('pop_accounts/', include('pop_accounts.urls')),
    path('pop_up_email/', include('pop_up_email.urls')),
    path('pop_up_shipping/', include('pop_up_shipping.urls')),
    path('pop_up_finance/', include('pop_up_finance.urls')),
    path('pop_up_auction/', include('pop_up_auction.urls')),
    path('pop_up_order/', include('pop_up_order.urls')),
    path('pop_up_cart/', include('pop_up_cart.urls')),
    path('pop_up_coupon/', include('pop_up_coupon.urls')),
    path('pop_up_reward/', include('pop_up_reward.urls')),
    path('pop_up_payment/', include('pop_up_payment.urls')),
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path('social-auth/', include('social_django.urls', namespace='social'))
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)