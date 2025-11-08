# orders/urls.py

from django.urls import path
from .views import (
    OrderListCreateView, 
    OrderUpdateView, 
    RiderOrderListView,
    RequestedOrdersListView
)

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list'),
    path('update/', OrderUpdateView.as_view(), name='order-update'),
    path('rider/', RiderOrderListView.as_view(), name='rider-order-list'),
    path('requested/', RequestedOrdersListView.as_view(), name='requested-orders-list'),
]
