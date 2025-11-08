# orders/views.py
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer
from users.permissions import LocationBasedPermission

class RequestedOrdersListView(generics.ListAPIView):
    """
    GET -> List all orders with status 'requested'
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get all requested orders regardless of user
        """
        return Order.objects.filter(
            status='requested'
        ).select_related('user', 'service').order_by('-created_at')

class RiderOrderListView(generics.ListAPIView):
    """
    GET -> List orders assigned to the authenticated rider and available orders
    POST -> Accept an order
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get both assigned and available orders for riders
        """
        return Order.objects.filter(
            # Either the order is assigned to the current rider
            # OR it's an available order (no rider and status is requested)
            models.Q(rider=self.request.user, status__in=['picked', 'in_progress']) |
            models.Q(rider__isnull=True, status__in=['requested'])
        ).select_related('user', 'service').order_by('-created_at')

    def post(self, request, *args, **kwargs):
        """Accept an order"""
        order_id = request.data.get('order_id')
        action = request.data.get('action', 'accept')  # 'accept' or 'reject'

        try:
            order = Order.objects.get(
                id=order_id,
                rider__isnull=True,
                status__iexact='requested'  # case-insensitive match
            )
            if action == 'accept':
                order.rider = request.user
                order.status = 'in_progress'  # Change status to in_progress directly
                order.save()
                return Response({'message': 'Order accepted successfully', 'order': OrderListSerializer(order).data})
            else:
                return Response({'message': 'Order rejected'})
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found or already assigned'},
                status=status.HTTP_404_NOT_FOUND
            )

class OrderUpdateView(APIView):
    """
    PATCH -> Update order status
    """
    permission_classes = [permissions.IsAuthenticated, LocationBasedPermission]

    def patch(self, request, *args, **kwargs):
        try:
            order_id = request.query_params.get('id')
            if not order_id:
                return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.get(id=order_id)
            
            # Check if the staff member has permission for this location
            if request.user.is_staff and not request.user.is_superuser:
                if not request.user.service_location or order.service_location != request.user.service_location:
                    return Response({'error': 'You do not have permission to update this order'}, 
                                 status=status.HTTP_403_FORBIDDEN)

            # Update status
            new_status = request.data.get('status')
            if not new_status:
                return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            order.save()

            serializer = OrderListSerializer(order)
            return Response(serializer.data)

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  -> list orders (filtered by location for staff)
    POST -> create order (anonymous allowed)
    """
    queryset = Order.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, LocationBasedPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by order code if provided
        code = self.request.query_params.get("code")
        if code:
            return queryset.filter(code__iexact=code.strip())

        # For staff users, filter by their service location
        if user.is_authenticated and user.is_staff and not user.is_superuser:
            if user.service_location:
                # Filter orders where either:
                # 1. The order's service_location matches staff's service_location, or
                # 2. The customer's location matches staff's service location area
                queryset = queryset.filter(
                    models.Q(service_location=user.service_location) |
                    models.Q(user__location__icontains=user.service_location.name)
                )
            else:
                return Order.objects.none()
        # For regular users, show only their orders
        elif user.is_authenticated and not user.is_staff:
            queryset = queryset.filter(user=user)
            
        return queryset

    def perform_create(self, serializer):
        # Automatically set the service_location based on the pickup address
        # You might want to implement a more sophisticated location assignment logic
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx
