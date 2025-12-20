#!/usr/bin/env python
"""
Test script for Africa's Talking SMS integration
This script tests the SMS service configuration and sends a test message
"""

import os
import sys
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from services.sms_service import AfricasTalkingSMSService
from django.conf import settings


def test_sms_configuration():
    """Test if SMS configuration is properly set"""
    print("=" * 60)
    print("Testing Africa's Talking SMS Configuration")
    print("=" * 60)
    
    print("\n✓ Configuration Settings:")
    print(f"  - API Key: {settings.AFRICAS_TALKING_API_KEY[:20]}...***" if settings.AFRICAS_TALKING_API_KEY else "  - API Key: NOT SET")
    print(f"  - Username: {settings.AFRICAS_TALKING_USERNAME}")
    print(f"  - Sender ID: {settings.AFRICAS_TALKING_SENDER_ID}")
    print(f"  - Admin Phone: {settings.ADMIN_PHONE_NUMBER}")
    
    if not settings.AFRICAS_TALKING_API_KEY:
        print("\n✗ ERROR: AFRICAS_TALKING_API_KEY is not set in .env file")
        return False
    
    if not settings.ADMIN_PHONE_NUMBER:
        print("\n✗ ERROR: ADMIN_PHONE_NUMBER is not set in .env file")
        return False
    
    print("\n✓ All configuration variables are set!")
    return True


def test_send_sms():
    """Test sending an SMS"""
    print("\n" + "=" * 60)
    print("Testing SMS Sending")
    print("=" * 60)
    
    try:
        sms_service = AfricasTalkingSMSService()
        print("\n✓ SMS Service initialized successfully")
        
        # Send test SMS
        test_message = "WILDWASH TEST: SMS integration is working! If you received this, the Africa's Talking setup is correct."
        print(f"\n📱 Sending test SMS to {settings.ADMIN_PHONE_NUMBER}...")
        print(f"   Message: {test_message}")
        
        result = sms_service.send_sms(
            phone_number=settings.ADMIN_PHONE_NUMBER,
            message=test_message
        )
        
        if result['status'] == 'success':
            print("\n✓ SMS sent successfully!")
            print(f"   Response: {result['response']}")
            return True
        else:
            print(f"\n✗ Failed to send SMS: {result['message']}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"\n✗ Exception occurred while testing SMS:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_order_simulation():
    """Simulate an order creation to test the signal"""
    print("\n" + "=" * 60)
    print("Testing Order Creation Signal (SMS Notification)")
    print("=" * 60)
    
    try:
        from orders.models import Order
        from users.models import User
        from services.models import Service
        
        print("\n⚠️  Note: To fully test the order creation signal:")
        print("   1. Create a test user (customer)")
        print("   2. Create a test order")
        print("   3. Check if SMS is received by admin")
        
        print("\nExample:")
        print("   # Get or create a test user")
        print("   user = User.objects.create_user(")
        print("       username='testuser',")
        print("       email='test@example.com',")
        print("       phone='+254712345678',")
        print("       role='customer'")
        print("   )")
        print("")
        print("   # Get a service")
        print("   service = Service.objects.first()")
        print("")
        print("   # Create an order - this will trigger SMS to admin")
        print("   order = Order.objects.create(")
        print("       user=user,")
        print("       service=service,")
        print("       pickup_address='123 Main St',")
        print("       dropoff_address='456 Oak Ave',")
        print("       order_type='online'")
        print("   )")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error in order simulation test: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n🚀 Africa's Talking SMS Integration Test Suite\n")
    
    # Run tests
    config_ok = test_sms_configuration()
    
    if config_ok:
        sms_ok = test_send_sms()
        order_ok = test_order_simulation()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ Configuration: {'PASS' if config_ok else 'FAIL'}")
        print(f"{'✓' if sms_ok else '✗'} SMS Sending: {'PASS' if sms_ok else 'FAIL'}")
        
        if config_ok and sms_ok:
            print("\n✅ All tests passed! SMS integration is working correctly.")
            print("\nNext steps:")
            print("1. Check your phone for the test SMS message")
            print("2. Create a new order to test the order creation notification")
            print("3. You should receive an SMS alert when an order is created")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
    else:
        print("\n❌ Configuration test failed. Please check your .env file.")
