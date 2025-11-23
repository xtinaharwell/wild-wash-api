#!/usr/bin/env python
"""
Test script for order details feature.
Run with: python manage.py shell < test_order_details.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from users.models import Location

User = get_user_model()

def test_order_details():
    """Test saving order details (quantity, weight, description)"""
    
    print("\n" + "="*60)
    print("  ORDER DETAILS TEST")
    print("="*60 + "\n")
    
    # Get or create a test order
    orders = Order.objects.filter(code__startswith='WW-').first()
    
    if not orders:
        print("❌ No orders found. Creating test data...")
        
        # Create location
        loc, _ = Location.objects.get_or_create(
            name="Juja",
            defaults={'is_active': True}
        )
        
        # Create customer
        customer = User.objects.create_user(
            username="test_customer_details",
            email="test_details@test.com",
            password="testpass123",
            role='customer',
            service_location=loc,
            is_active=True
        )
        
        # Create order
        from services.models import Service
        service = Service.objects.first() or Service.objects.create(
            name="Test Service",
            description="Test",
            price=500
        )
        
        order = Order.objects.create(
            user=customer,
            pickup_address="Test Pickup",
            dropoff_address="Test Dropoff",
            service_location=loc,
            status='in_progress'
        )
        order.services.add(service)
        print(f"✓ Created test order: {order.code}")
    else:
        order = orders
    
    # Test 1: Set quantity
    print("\n1. Testing quantity field...")
    order.quantity = 5
    order.save()
    order.refresh_from_db()
    print(f"   ✓ Saved quantity: {order.quantity}")
    assert order.quantity == 5, "Quantity not saved correctly"
    
    # Test 2: Set weight
    print("\n2. Testing weight_kg field...")
    order.weight_kg = 2.5
    order.save()
    order.refresh_from_db()
    print(f"   ✓ Saved weight: {order.weight_kg} kg")
    assert float(order.weight_kg) == 2.5, "Weight not saved correctly"
    
    # Test 3: Set description
    print("\n3. Testing description field...")
    order.description = "Fragile items - handle with care"
    order.save()
    order.refresh_from_db()
    print(f"   ✓ Saved description: {order.description}")
    assert order.description == "Fragile items - handle with care", "Description not saved correctly"
    
    # Test 4: Update status to picked
    print("\n4. Testing status update along with details...")
    order.status = 'picked'
    order.quantity = 10
    order.weight_kg = 5.0
    order.description = "All items picked successfully"
    order.save()
    order.refresh_from_db()
    print(f"   ✓ Updated order:")
    print(f"     - Status: {order.get_status_display()}")
    print(f"     - Quantity: {order.quantity}")
    print(f"     - Weight: {order.weight_kg} kg")
    print(f"     - Description: {order.description}")
    
    # Test 5: Verify serializer includes fields
    print("\n5. Testing serializer output...")
    from orders.serializers import OrderListSerializer
    serializer = OrderListSerializer(order)
    data = serializer.data
    
    print(f"   ✓ Serializer output includes:")
    print(f"     - quantity: {data.get('quantity')}")
    print(f"     - weight_kg: {data.get('weight_kg')}")
    print(f"     - description: {data.get('description')}")
    
    assert 'quantity' in data, "quantity not in serializer output"
    assert 'weight_kg' in data, "weight_kg not in serializer output"
    assert 'description' in data, "description not in serializer output"
    
    print("\n" + "="*60)
    print("  ✅ ALL TESTS PASSED")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_order_details()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
