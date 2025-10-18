# orders/views.py

from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderListSerializer

# ✅ Public API to list all orders — no authentication required
class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-created_at')  # show newest first
    serializer_class = OrderListSerializer
    permission_classes = [permissions.AllowAny]  # remove auth requirement
