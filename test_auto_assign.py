#!/usr/bin/env python
"""
Test script for order auto-assignment feature.
Run with: python manage.py shell < test_auto_assign.py
Or: python test_auto_assign.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from users.models import Location
from datetime import datetime

User = get_user_model()

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_auto_assign():
    """Test the auto-assignment feature"""
    
    print_header("AUTO-ASSIGNMENT TEST")
    
    # 1. Check if locations exist
    print("1. Checking locations...")
    locations = Location.objects.filter(is_active=True)
    print(f"   Active locations: {locations.count()}")
    for loc in locations:
        print(f"   - {loc.name} (ID: {loc.id})")
    
    if not locations.exists():
        print("   ⚠ WARNING: No active locations found. Creating test location...")
        loc, _ = Location.objects.get_or_create(
            name="Juja",
            defaults={'is_active': True}
        )
        print(f"   ✓ Created location: {loc.name}")
    
    # 2. Check if riders exist
    print("\n2. Checking riders...")
    riders = User.objects.filter(role='rider', is_active=True)
    print(f"   Active riders: {riders.count()}")
    for rider in riders:
        loc = rider.service_location
        jobs = rider.rider_profile.completed_jobs if hasattr(rider, 'rider_profile') else 'N/A'
        print(f"   - {rider.username} (Location: {loc.name if loc else 'None'}, Jobs: {jobs})")
    
    if not riders.exists():
        print("   ⚠ WARNING: No riders found. Creating test rider...")
        loc = locations.first() or Location.objects.get(name="Juja")
        rider = User.objects.create_user(
            username="test_rider_1",
            email="test_rider_1@test.com",
            password="testpass123",
            role='rider',
            service_location=loc,
            is_active=True
        )
        print(f"   ✓ Created rider: {rider.username} in {loc.name}")
        riders = User.objects.filter(role='rider', is_active=True)
    
    # 3. Check if customers exist
    print("\n3. Checking customers...")
    customers = User.objects.filter(role='customer', is_active=True)
    print(f"   Active customers: {customers.count()}")
    
    if not customers.exists():
        print("   ⚠ WARNING: No customers found. Creating test customer...")
        loc = locations.first() or Location.objects.get(name="Juja")
        customer = User.objects.create_user(
            username="test_customer_1",
            email="test_customer_1@test.com",
            password="testpass123",
            role='customer',
            service_location=loc,
            is_active=True
        )
        print(f"   ✓ Created customer: {customer.username}")
        customers = User.objects.filter(role='customer', is_active=True)
    
    # 4. Get a customer and create an order
    print("\n4. Creating test order...")
    customer = customers.first()
    service_location = locations.first()
    
    if customer and service_location:
        # Clear existing test orders
        Order.objects.filter(user=customer, code__startswith='TEST').delete()
        
        order = Order.objects.create(
            user=customer,
            pickup_address="Juja Town, Kenya",
            dropoff_address="Nairobi, Kenya",
            service_location=service_location,
            status='requested',
            urgency=1,
            items=1,
            weight_kg=5.0,
            price=500.0
        )
        print(f"   ✓ Created order: {order.code}")
        print(f"   - Pickup: {order.pickup_address}")
        print(f"   - Dropoff: {order.dropoff_address}")
        print(f"   - Service Location: {order.service_location.name if order.service_location else 'None'}")
        
        # 5. Check assignment
        print("\n5. Checking auto-assignment...")
        order.refresh_from_db()
        
        if order.rider:
            print(f"   ✓ Order assigned to rider: {order.rider.username}")
            print(f"   - Order status: {order.get_status_display()}")
            print(f"   - Assigned location: {order.service_location.name if order.service_location else 'None'}")
            return True
        else:
            print(f"   ✗ Order NOT assigned (rider is None)")
            print(f"   - Order status: {order.get_status_display()}")
            return False
    else:
        print("   ✗ Could not create order: missing customer or location")
        return False

def test_rider_can_see_order():
    """Test that assigned rider can see their orders"""
    print_header("RIDER ORDER VISIBILITY TEST")
    
    # Get a rider with assigned orders
    riders_with_orders = User.objects.filter(
        role='rider',
        orders__isnull=False,
        orders__status__in=['in_progress', 'picked', 'ready', 'delivered']
    ).distinct()
    
    print(f"1. Riders with assigned orders: {riders_with_orders.count()}")
    
    if riders_with_orders.exists():
        rider = riders_with_orders.first()
        orders = Order.objects.filter(
            rider=rider,
            status__in=['in_progress', 'picked', 'ready', 'delivered']
        )
        print(f"\n2. Rider: {rider.username}")
        print(f"   Orders assigned: {orders.count()}")
        for order in orders:
            print(f"   - Order {order.code} ({order.get_status_display()})")
        return True
    else:
        print("   ⚠ No riders with assigned orders found")
        return False

def test_location_matching():
    """Test location matching logic"""
    print_header("LOCATION MATCHING TEST")
    
    print("1. Testing location matching scenarios...\n")
    
    # Scenario 1: Exact location in service_location FK
    loc = Location.objects.filter(is_active=True).first()
    if loc:
        print(f"   Scenario 1: Service Location FK")
        print(f"   - Location: {loc.name}")
        riders = User.objects.filter(service_location=loc, role='rider', is_active=True)
        print(f"   - Riders in location: {riders.count()}\n")
    
    # Scenario 2: Location in user.location field
    print(f"   Scenario 2: User Location Field")
    customers_with_location = User.objects.filter(
        role='customer',
        location__isnull=False
    ).exclude(location='')
    print(f"   - Customers with location field: {customers_with_location.count()}")
    if customers_with_location.exists():
        cust = customers_with_location.first()
        print(f"   - Example: {cust.username} has location '{cust.location}'")
    
    # Scenario 3: Location in pickup_address
    print(f"\n   Scenario 3: Location in Pickup Address")
    orders_with_address = Order.objects.filter(pickup_address__isnull=False).exclude(pickup_address='')[:3]
    print(f"   - Sample orders with addresses:")
    for order in orders_with_address:
        print(f"   - {order.code}: {order.pickup_address[:50]}")

if __name__ == "__main__":
    try:
        # Run tests
        success = test_auto_assign()
        test_rider_can_see_order()
        test_location_matching()
        
        print_header("TEST SUMMARY")
        if success:
            print("✓ Auto-assignment appears to be working!")
        else:
            print("✗ Auto-assignment may have issues. Check the diagnostics above.")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
