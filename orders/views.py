# orders/views.py
from django.db import models
from django.db.models import Prefetch
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer
from users.permissions import LocationBasedPermission

class RequestedOrdersListView(generics.ListAPIView):
    """
    GET -> List all unassigned orders with status 'requested'
    Only for admin/staff to see pending orders
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get all unassigned requested orders
        """
        return Order.objects.filter(
            status='requested',
            rider__isnull=True
        ).select_related('user', 'service', 'service_location').prefetch_related('services').order_by('-created_at')

class RiderOrderListView(generics.ListAPIView):
    """
    GET -> List orders assigned to the authenticated rider
    Excludes orders with: Cleaning, fumigation, cctv installation, shower installation
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get orders assigned to the authenticated rider
        Exclude orders containing specific services
        """
        excluded_services = ['Cleaning', 'fumigation', 'cctv installation', 'shower installation']
        
        queryset = Order.objects.filter(
            # Orders assigned to the current rider
            rider=self.request.user,
            status__in=['in_progress', 'picked', 'ready', 'delivered']
        ).exclude(
            services__name__in=excluded_services
        ).distinct().select_related('user', 'service', 'rider', 'service_location').prefetch_related('services').order_by('-created_at')
        
        # Debug logging
        print(f"\n[DEBUG RiderOrders] Rider {self.request.user.username} (ID: {self.request.user.id}) querying orders")
        print(f"[DEBUG] Total orders assigned to this rider: {queryset.count()}")
        for order in queryset[:10]:
            print(f"  - Order {order.code} (ID: {order.id}, Status: {order.status}, Rider: {order.rider.username})")
        
        return queryset

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
    PATCH -> Update order status, quantity, weight, and description
    Sends notification to rider when status changes to 'ready' (ready for delivery)
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

            # Check if status is changing to 'ready'
            new_status = request.data.get('status')
            old_status = order.status
            status_changed_to_ready = new_status and new_status.lower() == 'ready' and old_status.lower() != 'ready'

            print(f"\n[DEBUG OrderUpdate] Order {order.code}")
            print(f"[DEBUG] Old status: {old_status}, New status: {new_status}")
            print(f"[DEBUG] Status changed to ready: {status_changed_to_ready}")
            print(f"[DEBUG] Current rider: {order.rider.username if order.rider else 'None'}")

            # Update status if provided
            if new_status:
                order.status = new_status

            # Update rider-provided details
            quantity = request.data.get('quantity')
            if quantity is not None:
                order.quantity = quantity

            weight_kg = request.data.get('weight_kg')
            if weight_kg is not None:
                order.weight_kg = weight_kg

            description = request.data.get('description')
            if description is not None:
                order.description = description

            order.save()
            print(f"[DEBUG] Order saved with status: {order.status}")

            # Handle status change to 'ready'
            if status_changed_to_ready:
                from notifications.models import Notification
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                assigned_rider = None
                
                # If order doesn't have a rider assigned, assign it to an available rider in the same location
                if not order.rider and order.service_location:
                    print(f"[DEBUG] No rider assigned yet, finding available rider...")
                    available_riders = User.objects.filter(
                        role='rider',
                        service_location=order.service_location,
                        is_active=True
                    ).select_related('rider_profile').order_by('rider_profile__completed_jobs')
                    
                    print(f"[DEBUG] Available riders in {order.service_location.name}: {available_riders.count()}")
                    
                    if available_riders.exists():
                        assigned_rider = available_riders.first()
                        order.rider = assigned_rider
                        order.save(update_fields=['rider'])
                        print(f"✓ Order {order.code} assigned to rider {assigned_rider.username}")
                    else:
                        print(f"⚠ No available riders in {order.service_location.name} for order {order.code}")
                else:
                    # Rider already assigned, use existing rider
                    assigned_rider = order.rider
                    if assigned_rider:
                        print(f"[DEBUG] Rider already assigned: {assigned_rider.username}")
                
                # Send notification to rider if assigned
                if assigned_rider:
                    message = f"Order {order.code} is ready for delivery! Pickup from: {order.pickup_address}"
                    notification = Notification.objects.create(
                        user=assigned_rider,
                        order=order,
                        message=message,
                        notification_type='order_update'
                    )
                    print(f"✓ Notification (ID: {notification.id}) sent to rider {assigned_rider.username} for order {order.code}")
                else:
                    print(f"⚠ No rider to send notification to for order {order.code}")

            serializer = OrderListSerializer(order)
            return Response(serializer.data)

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[ERROR] Exception in OrderUpdateView: {str(e)}")
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
        
        # Optimize queries
        queryset = queryset.select_related('user', 'service', 'rider', 'service_location').prefetch_related('services')
        
        # Filter by order code if provided
        code = self.request.query_params.get("code")
        if code:
            return queryset.filter(code__iexact=code.strip())

        # For staff users, filter by their service location
        if user.is_authenticated and user.is_staff and not user.is_superuser:
            print(f"\n[DEBUG Orders] Staff user: {user.username} (ID: {user.id})")
            print(f"[DEBUG Orders] Staff service_location: {user.service_location} (ID: {user.service_location.id if user.service_location else 'None'})")
            
            if user.service_location:
                # Filter orders where either:
                # 1. The order's service_location matches staff's service_location, or
                # 2. The customer's location matches staff's service location area
                queryset = queryset.filter(
                    models.Q(service_location=user.service_location) |
                    models.Q(user__location__icontains=user.service_location.name)
                )
                print(f"[DEBUG Orders] Applied location filter for: {user.service_location}")
                print(f"[DEBUG Orders] Total orders matching location: {queryset.count()}")
                for order in queryset[:5]:
                    print(f"  - Order {order.code}: service_location={order.service_location}, status={order.status}")
            else:
                print(f"[DEBUG Orders] ⚠️ Staff has no service_location assigned, returning no orders")
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
