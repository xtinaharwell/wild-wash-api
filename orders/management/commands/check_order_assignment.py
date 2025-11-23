"""
Management command to check order assignments
Run with: python manage.py check_order_assignment <order_id>
"""
from django.core.management.base import BaseCommand
from orders.models import Order

class Command(BaseCommand):
    help = 'Check the assignment status of an order'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='Order ID to check')

    def handle(self, *args, **options):
        order_id = options['order_id']
        
        try:
            order = Order.objects.select_related('rider', 'service_location', 'user', 'service').get(id=order_id)
            
            self.stdout.write(self.style.SUCCESS('\n=== Order Assignment Details ==='))
            self.stdout.write(f"Order ID: {order.id}")
            self.stdout.write(f"Order Code: {order.code}")
            self.stdout.write(f"Status: {order.status}")
            self.stdout.write(f"Customer: {order.user.username if order.user else 'N/A'}")
            self.stdout.write(f"Customer Location: {order.user.location if order.user and order.user.location else 'N/A'}")
            self.stdout.write(f"Service Location: {order.service_location.name if order.service_location else 'NOT SET'}")
            
            if order.rider:
                self.stdout.write(self.style.SUCCESS(f"✓ Assigned to Rider: {order.rider.username}"))
                self.stdout.write(f"  - Rider ID: {order.rider.id}")
                self.stdout.write(f"  - Rider Location: {order.rider.service_location.name if order.rider.service_location else 'NOT SET'}")
                self.stdout.write(f"  - Rider is_active: {order.rider.is_active}")
            else:
                self.stdout.write(self.style.WARNING("✗ NOT ASSIGNED - No rider assigned"))
            
            self.stdout.write(f"\nPickup Address: {order.pickup_address}")
            self.stdout.write(f"Created: {order.created_at}")
            self.stdout.write('\n')
            
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order ID {order_id} not found'))
