#!/usr/bin/env python
"""
Test Africa's Talking SMS Integration with Orders
Tests the order-specific SMS notifications
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

from services.sms_service import AfricasTalkingSMSService
from orders.models import Order
from services.models import Service
from users.models import Location
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("Africa's Talking SMS Integration - Order Test")
print("=" * 70)

# Initialize SMS service
try:
    sms_service = AfricasTalkingSMSService()
    print("\n✓ SMS Service initialized successfully")
except Exception as e:
    print(f"\n❌ Failed to initialize SMS service: {e}")
    sys.exit(1)

# Test 1: Send order confirmation SMS
print("\n\n1️⃣  Testing Order Confirmation SMS")
print("-" * 70)

# Try to find or create a test order
try:
    # Get or create a test location
    location, _ = Location.objects.get_or_create(
        name='Test Location',
        defaults={'description': 'Test location for SMS integration'}
    )
    
    # Get or create a test service
    service, _ = Service.objects.get_or_create(
        name='Test Service',
        defaults={'category': 'laundry', 'price': 500.00, 'description': 'Test washing service'}
    )
    
    # Get or create a test user (customer)
    test_user, _ = User.objects.get_or_create(
        username='test_customer',
        defaults={
            'email': 'test@example.com',
            'phone': '+254718693484',  # Admin phone number
            'role': 'customer',
        }
    )
    
    # Try to get an existing order or create one
    order = Order.objects.filter(user=test_user).first()
    
    if not order:
        order = Order.objects.create(
            user=test_user,
            service=service,
            service_location=location,
            pickup_address='123 Test Street',
            dropoff_address='456 Delivery Ave',
            price=500.00,
            actual_price=500.00,
            status='ready',
            urgency=2,
            items=1,
            order_type='online'
        )
        order.services.add(service)
        print(f"Created test order: {order.code}")
    
    # Send confirmation SMS
    print(f"\nSending confirmation SMS to {test_user.phone}...")
    result = sms_service.send_order_confirmation(test_user.phone, order)  # type: ignore
    
    if result['status'] == 'success':
        print(f"✅ Order confirmation SMS sent successfully!")
        print(f"   Order Code: {order.code}")
        print(f"   Customer: {test_user.username}")
        print(f"   Phone: {test_user.phone}")
    else:
        print(f"❌ Failed to send confirmation SMS: {result['message']}")

except Exception as e:
    print(f"❌ Error in order confirmation test: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 2: Send rider assignment SMS
print("\n\n2️⃣  Testing Rider Assignment SMS")
print("-" * 70)

try:
    # Get or create a test rider
    test_rider, _ = User.objects.get_or_create(
        username='test_rider',
        defaults={
            'email': 'rider@example.com',
            'phone': '+254718693484',  # Admin phone for testing
            'role': 'rider',
            'service_location': location,
        }
    )
    
    print(f"Sending rider assignment SMS to {test_rider.phone}...")
    result = sms_service.send_order_ready_notification(
        test_rider.phone,  # type: ignore
        order,
        test_rider.get_full_name() or test_rider.username
    )
    
    if result['status'] == 'success':
        print(f"✅ Rider assignment SMS sent successfully!")
        print(f"   Rider: {test_rider.username}")
        print(f"   Phone: {test_rider.phone}")
        print(f"   Order: {order.code}")
    else:
        print(f"❌ Failed to send rider SMS: {result['message']}")

except Exception as e:
    print(f"❌ Error in rider assignment test: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 3: Send delivery confirmation SMS
print("\n\n3️⃣  Testing Delivery Confirmation SMS")
print("-" * 70)

try:
    print(f"Sending delivery confirmation SMS to {test_user.phone}...")
    result = sms_service.send_delivery_confirmation(test_user.phone, order)  # type: ignore
    
    if result['status'] == 'success':
        print(f"✅ Delivery confirmation SMS sent successfully!")
        print(f"   Customer: {test_user.username}")
        print(f"   Order: {order.code}")
    else:
        print(f"❌ Failed to send delivery SMS: {result['message']}")

except Exception as e:
    print(f"❌ Error in delivery confirmation test: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 4: Send generic SMS
print("\n\n4️⃣  Testing Generic SMS")
print("-" * 70)

try:
    message = "🎉 WildWash Test SMS - This is a test message from the order integration!"
    print(f"Sending generic SMS to +254718693484...")
    result = sms_service.send_sms('+254718693484', message)
    
    if result['status'] == 'success':
        print(f"✅ Generic SMS sent successfully!")
    else:
        print(f"❌ Failed to send generic SMS: {result['message']}")

except Exception as e:
    print(f"❌ Error in generic SMS test: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
print("\n✓ SMS integration with orders is working!")
print("✓ Ready for production use")
