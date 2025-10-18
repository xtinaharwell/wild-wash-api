# orders/views.py
from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  -> list orders (OrderListSerializer)
    POST -> create order (OrderCreateSerializer)
    """
    queryset = Order.objects.all().order_by("-created_at")
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx
