# orders/urls.py

from django.urls import path
from .views import OrderListCreateView, OrderUpdateView, RiderOrderListView

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list'),
    path('update/', OrderUpdateView.as_view(), name='order-update'),
    path('rider/', RiderOrderListView.as_view(), name='rider-order-list'),
]
