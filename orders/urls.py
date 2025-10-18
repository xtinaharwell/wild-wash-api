# orders/urls.py

from django.urls import path
from .views import OrderListView

urlpatterns = [
    path('all/', OrderListView.as_view(), name='order-list'),
]
