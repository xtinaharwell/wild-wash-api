# orders/views.py

from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer


# # ✅ Public API to list all orders — no authentication required
# class OrderListView(generics.ListAPIView):
#     queryset = Order.objects.all().order_by('-created_at')  # show newest first
#     serializer_class = OrderListSerializer
#     permission_classes = [permissions.AllowAny]  # remove auth requirement


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  -> list orders (OrderListSerializer)
    POST -> create order (OrderCreateSerializer)
    Permission currently AllowAny (change to IsAuthenticated if you want auth)
    """
    queryset = Order.objects.all().order_by('-created_at')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer
