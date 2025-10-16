from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
from users.models import User


class IsRiderOrOwner(permissions.BasePermission):
    """Allow riders or the order owner (or staff) to update status/details."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if getattr(request.user, 'is_rider', False):
            return True
        return obj.user == request.user


class OrderViewSet(viewsets.ModelViewSet):
    """Create orders (customers), and allow riders/admins to update status."""
    queryset = Order.objects.all().select_related('service', 'user')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create']:
            return OrderCreateSerializer
        if self.action in ['update_status']:
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        # riders and staff can see all orders; regular users see only their orders
        if getattr(user, 'is_rider', False) or user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='status', permission_classes=[permissions.IsAuthenticated, IsRiderOrOwner])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Optionally trigger notification via signals/tasks
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='assign-rider', permission_classes=[permissions.IsAdminUser])
    def assign_rider(self, request, pk=None):
        order = self.get_object()
        rider_id = request.data.get('rider_id')
        rider = get_object_or_404(User, pk=rider_id, is_rider=True)
        order.assigned_rider = rider
        order.save()
        return Response(OrderSerializer(order).data)