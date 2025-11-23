"""
Management command to assign any pending unassigned orders to riders
Run with: python manage.py assign_pending_orders
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from orders.models import Order
from users.models import Location
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Assign pending unassigned orders to available riders'

    def handle(self, *args, **options):
        # Find all unassigned orders (no rider assigned)
        unassigned_orders = Order.objects.filter(rider__isnull=True)
        
        if not unassigned_orders.exists():
            self.stdout.write(self.style.SUCCESS('No unassigned orders found'))
            return
        
        self.stdout.write(f'Found {unassigned_orders.count()} unassigned orders')
        
        assigned_count = 0
        failed_count = 0
        
        for order in unassigned_orders:
            try:
                service_location = order.service_location
                
                # If no service_location, try to infer from user's location or pickup address
                if not service_location:
                    # Try to match from user's location field
                    if order.user and order.user.location:
                        user_location = order.user.location.lower().strip()
                        service_location = Location.objects.filter(
                            name__icontains=user_location,
                            is_active=True
                        ).first()
                    
                    # If still no location, try to extract from pickup_address
                    if not service_location:
                        locations = Location.objects.filter(is_active=True)
                        for loc in locations:
                            if loc.name.lower() in order.pickup_address.lower():
                                service_location = loc
                                break
                    
                    # If still no match, use the first active location
                    if not service_location:
                        service_location = Location.objects.filter(is_active=True).first()
                
                if service_location:
                    # Try to find riders in the same location
                    riders = User.objects.filter(
                        role='rider',
                        service_location=service_location,
                        is_active=True
                    ).select_related('rider_profile').order_by('rider_profile__completed_jobs')
                    
                    if riders.exists():
                        assigned_rider = riders.first()
                    else:
                        # No riders in location, use any available rider
                        all_riders = User.objects.filter(
                            role='rider',
                            is_active=True
                        ).select_related('rider_profile').order_by('rider_profile__completed_jobs')
                        assigned_rider = all_riders.first()
                    
                    if assigned_rider:
                        order.rider = assigned_rider
                        order.service_location = service_location
                        order.status = 'in_progress'
                        order.save()
                        
                        # Create notification
                        Notification.objects.create(
                            user=assigned_rider,
                            order=order,
                            message=f"Order {order.code} assigned to you. Pickup: {order.pickup_address[:50]}...",
                            notification_type='new_order'
                        )
                        
                        self.stdout.write(self.style.SUCCESS(f'✓ Assigned order {order.code} to {assigned_rider.username}'))
                        assigned_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'✗ No riders available for order {order.code}'))
                        failed_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'✗ Could not determine location for order {order.code}'))
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error assigning order {order.code}: {e}'))
                failed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nAssignment complete: {assigned_count} assigned, {failed_count} failed'))
