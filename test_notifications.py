#!/usr/bin/env python
"""
Test script for rider notifications feature.
Verifies that notifications are created when orders are assigned to riders.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from notifications.models import Notification
from users.models import Location

User = get_user_model()

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_notifications():
    """Test that notifications are created"""
    
    print_header("NOTIFICATION TEST")
    
    # Get a rider
    rider = User.objects.filter(role='rider', is_active=True).first()
    if not rider:
        print("✗ No active riders found")
        return False
    
    print(f"1. Testing with rider: {rider.username}")
    
    # Count existing notifications for this rider
    existing_count = Notification.objects.filter(user=rider).count()
    print(f"   Existing notifications: {existing_count}")
    
    # Get a customer
    customer = User.objects.filter(role='customer', is_active=True).first()
    if not customer:
        print("✗ No active customers found")
        return False
    
    print(f"\n2. Testing with customer: {customer.username}")
    
    # Get location
    location = Location.objects.filter(is_active=True).first()
    if not location:
        print("✗ No active locations found")
        return False
    
    print(f"   Location: {location.name}")
    
    # Create an order (this should trigger auto-assignment signal)
    print(f"\n3. Creating test order...")
    order = Order.objects.create(
        user=customer,
        pickup_address="Test Pickup Address",
        dropoff_address="Test Dropoff Address",
        service_location=location,
        status='requested',
        urgency=1,
        items=1,
        weight_kg=1.0,
        price=100.0
    )
    print(f"   ✓ Order created: {order.code}")
    print(f"   - Status: {order.get_status_display()}")
    print(f"   - Rider: {order.rider.username if order.rider else 'None'}")
    
    # Check if rider was assigned
    if not order.rider:
        print(f"   ✗ Order was not assigned to a rider!")
        return False
    
    print(f"   ✓ Order was auto-assigned to: {order.rider.username}")
    
    # Check if notification was created
    print(f"\n4. Checking for new notifications...")
    
    # Get all notifications for the assigned rider
    rider_notifications = Notification.objects.filter(user=order.rider).order_by('-created_at')
    print(f"   Total notifications for {order.rider.username}: {rider_notifications.count()}")
    
    # Get notifications for this order
    order_notifications = rider_notifications.filter(order=order)
    print(f"   Notifications for this order: {order_notifications.count()}")
    
    if order_notifications.exists():
        for notif in order_notifications:
            print(f"   ✓ Notification created:")
            print(f"     - Message: {notif.message}")
            print(f"     - Type: {notif.notification_type}")
            print(f"     - Is Read: {notif.is_read}")
            print(f"     - Created: {notif.created_at}")
        return True
    else:
        print(f"   ✗ No notification found for order {order.code}")
        
        # Debug: Check all recent notifications
        print(f"\n5. Debug - Last 5 notifications in system:")
        recent = Notification.objects.all().order_by('-created_at')[:5]
        for notif in recent:
            print(f"   - {notif.user.username}: {notif.message[:50]}...")
        
        return False

def test_notification_retrieval():
    """Test fetching notifications for a rider"""
    
    print_header("NOTIFICATION RETRIEVAL TEST")
    
    # Get a rider
    rider = User.objects.filter(role='rider', is_active=True).first()
    if not rider:
        print("✗ No active riders found")
        return False
    
    print(f"1. Checking notifications for rider: {rider.username}")
    
    # Get unread notifications
    unread = Notification.objects.filter(user=rider, is_read=False)
    print(f"   Unread notifications: {unread.count()}")
    
    # Get new order notifications
    new_orders = unread.filter(notification_type='new_order')
    print(f"   New order notifications: {new_orders.count()}")
    
    if new_orders.exists():
        print(f"   ✓ Sample notifications:")
        for notif in new_orders[:3]:
            print(f"     - Order {notif.order.code}: {notif.message[:50]}...")
        return True
    else:
        print(f"   ℹ No new order notifications (this is OK if orders haven't been created)")
        return True

if __name__ == "__main__":
    try:
        success1 = test_notifications()
        success2 = test_notification_retrieval()
        
        print_header("SUMMARY")
        if success1:
            print("✅ Notifications are working correctly!")
        else:
            print("⚠ Notification creation may have issues")
            print("\nDebug steps:")
            print("1. Check if orders/signals.py is being imported in orders/apps.py")
            print("2. Verify Notification model is imported in signals")
            print("3. Check Django logs for signal errors")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
