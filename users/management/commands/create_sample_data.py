from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User, Location
from services.models import Service
from orders.models import Order
import random

class Command(BaseCommand):
    help = 'Creates sample data for the Wildwash application'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")

        # Create Locations
        locations_data = [
            {'name': 'Westlands', 'description': 'Central Nairobi business district'},
            {'name': 'Kilimani', 'description': 'Upper middle-class residential area'},
            {'name': 'Karen', 'description': 'High-end residential area'},
            {'name': 'Riverside', 'description': 'Modern residential and business'},
            {'name': 'South C', 'description': 'Residential area in South Nairobi'},
        ]

        locations = {}
        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults={'description': loc_data['description']}
            )
            locations[loc_data['name']] = location
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created location: {loc_data['name']}"))

        # Create Services
        services_data = [
            {'name': 'Standard Wash', 'description': 'Regular laundry wash', 'price': 500},
            {'name': 'Express Wash', 'description': '24-hour express service', 'price': 800},
            {'name': 'Dry Cleaning', 'description': 'Professional dry cleaning', 'price': 1200},
            {'name': 'Ironing Service', 'description': 'Professional ironing', 'price': 300},
            {'name': 'Folding Service', 'description': 'Neat folding service', 'price': 200},
        ]

        services = {}
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price']
                }
            )
            services[service_data['name']] = service
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created service: {service_data['name']}"))

        # Create Sample Users
        # Customers
        customers = []
        customer_data = [
            {'username': 'john_customer', 'email': 'john@example.com', 'phone': '+254712345671', 'first_name': 'John'},
            {'username': 'jane_customer', 'email': 'jane@example.com', 'phone': '+254712345672', 'first_name': 'Jane'},
            {'username': 'peter_customer', 'email': 'peter@example.com', 'phone': '+254712345673', 'first_name': 'Peter'},
        ]

        for cust in customer_data:
            user, created = User.objects.get_or_create(
                username=cust['username'],
                defaults={
                    'email': cust['email'],
                    'phone': cust['phone'],
                    'first_name': cust['first_name'],
                    'role': 'customer',
                    'location': random.choice(list(locations.values())).name,
                    'pickup_address': f"{random.choice(list(locations.values())).name}, Nairobi",
                }
            )
            customers.append(user)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created customer: {cust['username']}"))

        # Riders
        riders = []
        rider_data = [
            {'username': 'rider_1', 'email': 'rider1@example.com', 'phone': '+254712345674', 'first_name': 'Ahmed'},
            {'username': 'rider_2', 'email': 'rider2@example.com', 'phone': '+254712345675', 'first_name': 'David'},
        ]

        for rider in rider_data:
            user, created = User.objects.get_or_create(
                username=rider['username'],
                defaults={
                    'email': rider['email'],
                    'phone': rider['phone'],
                    'first_name': rider['first_name'],
                    'role': 'rider',
                    'service_location': random.choice(list(locations.values())),
                }
            )
            riders.append(user)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created rider: {rider['username']}"))

        # Washers (Staff)
        washers = []
        washer_data = [
            {'username': 'washer_1', 'email': 'washer1@example.com', 'phone': '+254712345676', 'first_name': 'Ali'},
            {'username': 'washer_2', 'email': 'washer2@example.com', 'phone': '+254712345677', 'first_name': 'Mohamed'},
        ]

        for washer in washer_data:
            user, created = User.objects.get_or_create(
                username=washer['username'],
                defaults={
                    'email': washer['email'],
                    'phone': washer['phone'],
                    'first_name': washer['first_name'],
                    'role': 'washer',
                    'staff_type': 'washer',
                    'service_location': random.choice(list(locations.values())),
                }
            )
            washers.append(user)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created washer: {washer['username']}"))

        # Create Sample Orders
        orders_count = 0
        statuses = ['requested', 'picked', 'in_progress', 'washed', 'ready', 'delivered']
        
        for customer in customers:
            for i in range(3):
                order_code = f"WW-{random.randint(10000, 99999)}"
                
                # Make sure code is unique
                while Order.objects.filter(code=order_code).exists():
                    order_code = f"WW-{random.randint(10000, 99999)}"

                order, created = Order.objects.get_or_create(
                    code=order_code,
                    defaults={
                        'user': customer,
                        'service': random.choice(list(services.values())),
                        'service_location': random.choice(list(locations.values())),
                        'pickup_address': f"{random.choice(list(locations.values())).name}, House {random.randint(1, 100)}",
                        'dropoff_address': f"{random.choice(list(locations.values())).name}, House {random.randint(1, 100)}",
                        'status': random.choice(statuses),
                        'urgency': random.randint(1, 5),
                        'items': random.randint(1, 10),
                        'weight_kg': round(random.uniform(1, 20), 2),
                        'price': random.choice(list(services.values())).price,
                        'rider': random.choice(riders) if random.choice([True, False]) else None,
                        'created_at': timezone.now() - timedelta(days=random.randint(0, 30)),
                    }
                )
                
                if created:
                    # Add services to the order
                    order.services.add(random.choice(list(services.values())))
                    orders_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created order: {order_code}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Sample data created successfully!\n"
                f"Created {len(customers)} customers, {len(riders)} riders, {len(washers)} washers\n"
                f"Created {orders_count} orders across {len(locations)} locations"
            )
        )
