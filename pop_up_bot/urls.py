from django.urls import path
from .views import ProcurementRequestView

app_name = 'pop_up_bot'
urlpatterns = [
    path('procure/', ProcurementRequestView.as_view(), name='procure_product'),
    path('procure/<int:product_id>/', ProcurementRequestView.as_view(), name='procure_product'),
]