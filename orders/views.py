# orders/views.py
from django.db import models
from django.db.models import Prefetch
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer
from users.permissions import LocationBasedPermission

class StaffCreateOrderView(APIView):
    """
    POST -> Create a manual order for a customer (by staff)
    Only accessible by staff members
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if user is staff
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only staff members can create manual orders'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Use the OrderCreateSerializer to handle order creation
        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                order = serializer.save()
                return Response(
                    OrderListSerializer(order, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': f'Failed to create order: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


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

            # Determine incoming values and capture old values for audit BEFORE mutating
            new_status = request.data.get('status')
            old_status = order.status
            status_changed_to_ready = new_status and new_status.lower() == 'ready' and old_status.lower() != 'ready'

            # Capture old values before update
            old_values = {
                'status': old_status,
                'quantity': getattr(order, 'quantity', None),
                'weight_kg': getattr(order, 'weight_kg', None),
                'description': getattr(order, 'description', None),
                'actual_price': getattr(order, 'actual_price', None),
                'delivered_at': getattr(order, 'delivered_at', None),
            }

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

            # Update staff-entered actual price if provided
            actual_price = request.data.get('actual_price')
            if actual_price is not None:
                try:
                    # attempt to coerce into Decimal-compatible numeric string
                    from decimal import Decimal
                    order.actual_price = Decimal(str(actual_price))
                except Exception:
                    # fallback to raw assignment; DB will validate/raise if invalid
                    order.actual_price = actual_price

            order.save()

            # Accept delivered_at from request (rider marking delivery)
            delivered_at = request.data.get('delivered_at')
            if delivered_at is not None:
                try:
                    # Parse and set delivered_at; allow ISO strings
                    from django.utils.dateparse import parse_datetime
                    parsed = parse_datetime(str(delivered_at))
                    if parsed:
                        order.delivered_at = parsed
                        order.save(update_fields=['delivered_at'])
                except Exception:
                    # ignore parse errors
                    pass

            # Record events for changes
            from .models import OrderEvent
            actor = request.user if request.user.is_authenticated else None

            # status change
            if new_status and (old_status != new_status):
                OrderEvent.objects.create(
                    order=order,
                    actor=actor,
                    event_type='status_changed',
                    data={'old': old_status, 'new': new_status}
                )

            # details changed (quantity, weight, description)
            changed_details = {}
            if quantity is not None and quantity != old_values.get('quantity'):
                changed_details['quantity'] = {'old': old_values.get('quantity'), 'new': quantity}
            if weight_kg is not None and weight_kg != old_values.get('weight_kg'):
                changed_details['weight_kg'] = {'old': old_values.get('weight_kg'), 'new': weight_kg}
            if description is not None and description != old_values.get('description'):
                changed_details['description'] = {'old': old_values.get('description'), 'new': description}
            # actual_price changed
            if actual_price is not None:
                # Compare with old value (coerce to string/Decimal as needed)
                old_ap = old_values.get('actual_price')
                # If Decimal objects, string comparison is safe for equality check here
                if str(old_ap) != str(actual_price):
                    changed_details['actual_price'] = {'old': old_ap, 'new': actual_price}
            # delivered_at changed (rider marking delivered)
            delivered_at_req = request.data.get('delivered_at')
            if delivered_at_req is not None:
                old_da = old_values.get('delivered_at')
                # compare as ISO string where possible
                if str(old_da) != str(delivered_at_req):
                    changed_details['delivered_at'] = {'old': old_da, 'new': delivered_at_req}

            if changed_details:
                OrderEvent.objects.create(
                    order=order,
                    actor=actor,
                    event_type='details_updated',
                    data=changed_details
                )
            print(f"[DEBUG] Order saved with status: {order.status}")

            # Handle status change to 'ready'
            if status_changed_to_ready:
                from notifications.models import Notification
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                assigned_rider = None
                
                # For manual orders created by staff, only auto-assign if delivery address was provided
                if order.order_type == 'manual':
                    print(f"[DEBUG] Order {order.code} is a manual order")
                    print(f"[DEBUG] Order created by staff: {order.created_by.username if order.created_by else 'Unknown'}")
                    
                    # Check if delivery address was provided (not the default "To be assigned")
                    has_delivery_address = (
                        order.dropoff_address and 
                        order.dropoff_address.lower() != 'to be assigned' and
                        order.dropoff_address.strip() != ''
                    )
                    
                    if has_delivery_address:
                        print(f"[DEBUG] Delivery address provided: {order.dropoff_address}")
                        print(f"[DEBUG] Assigning to available rider...")
                        # Only auto-assign if delivery address was provided
                        if not order.rider and order.service_location:
                            available_riders = User.objects.filter(
                                role='rider',
                                service_location=order.service_location,
                                is_active=True
                            ).select_related('rider_profile').order_by('rider_profile__completed_jobs')
                            
                            if available_riders.exists():
                                assigned_rider = available_riders.first()
                                order.rider = assigned_rider
                                order.save(update_fields=['rider'])
                                print(f"✓ Order {order.code} assigned to rider {assigned_rider.username}")
                            else:
                                print(f"⚠ No available riders in {order.service_location.name}")
                    else:
                        print(f"[DEBUG] No delivery address - order stays with staff creator")
                        
                # If order doesn't have a rider assigned, assign it to an available rider in the same location
                elif not order.rider and order.service_location:
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

                # record assignment event
                if assigned_rider:
                    from .models import OrderEvent
                    OrderEvent.objects.create(
                        order=order,
                        actor=request.user if request.user.is_authenticated else None,
                        event_type='assigned_rider',
                        data={'rider_id': assigned_rider.id, 'rider_username': assigned_rider.username}
                    )

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
    # We'll enforce authentication for GET (listing) but still allow anonymous POST (create)
    permission_classes = [LocationBasedPermission]

    def get_permissions(self):
        """
        Use stricter permissions for GET requests (require authentication) so
        anonymous users cannot list all orders. Allow anonymous POST to create orders.
        """
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated(), LocationBasedPermission()]
        if self.request.method == 'POST':
            return [permissions.AllowAny(), LocationBasedPermission()]
        return [permissions.IsAuthenticated(), LocationBasedPermission()]

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


class OrderPaymentStatusView(APIView):
    """
    GET -> Get payment status for an order
    Retrieves the payment information associated with an order
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, code, *args, **kwargs):
        try:
            # Try to get the order by code (order reference/id)
            order = Order.objects.get(code=code)
            
            # Check if user has permission to view this order
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {'detail': 'You do not have permission to view this order'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the latest payment for this order
            from payments.models import Payment
            try:
                payment = Payment.objects.filter(order_id=order.id).latest('created_at')
                return Response({
                    'status': payment.status,
                    'message': f'Payment is {payment.status}',
                    'checkout_request_id': payment.provider_reference,
                    'order_id': order.code,
                    'amount': float(payment.amount),
                })
            except Payment.DoesNotExist:
                return Response({
                    'status': 'pending',
                    'message': 'No payment found for this order',
                    'checkout_request_id': '',
                    'order_id': order.code,
                    'amount': 0,
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )