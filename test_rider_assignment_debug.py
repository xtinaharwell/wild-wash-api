#!/usr/bin/env python
"""
Diagnostic test to debug why riders are not being assigned to orders.
Run with: python manage.py shell < test_rider_assignment_debug.py
Or: python test_rider_assignment_debug.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from users.models import Location

User = get_user_model()

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def diagnose_rider_assignment():
    """Diagnose why riders aren't being assigned"""
    
    print_header("RIDER ASSIGNMENT DIAGNOSTIC")
    
    # 1. Check active locations
    print("1️⃣  CHECKING ACTIVE LOCATIONS")
    locations = Location.objects.filter(is_active=True)
    print(f"   Active locations: {locations.count()}")
    for loc in locations:
        print(f"   ✓ {loc.name} (ID: {loc.id})")
    
    if not locations.exists():
        print("   ⚠️  WARNING: No active locations found!")
        print("   → This is likely why riders aren't being assigned")
        return
    
    # 2. Check riders in each location
    print("\n2️⃣  CHECKING RIDERS PER LOCATION")
    for loc in locations:
        riders = User.objects.filter(
            role='rider',
            service_location=loc,
            is_active=True
        )
        print(f"\n   📍 Location: {loc.name}")
        print(f"      Active riders: {riders.count()}")
        for rider in riders:
            profile = rider.rider_profile if hasattr(rider, 'rider_profile') else None
            jobs = profile.completed_jobs if profile else 'N/A'
            print(f"      ✓ {rider.username} (Jobs: {jobs})")
        
        if not riders.exists():
            print(f"      ⚠️  NO RIDERS in {loc.name}")
    
    # 3. Check unassigned orders
    print("\n3️⃣  CHECKING UNASSIGNED ORDERS")
    unassigned = Order.objects.filter(rider__isnull=True, order_type='manual')
    print(f"   Unassigned manual orders: {unassigned.count()}\n")
    
    for order in unassigned[:5]:  # Show first 5
        print(f"   Order: {order.code}")
        print(f"   ├─ Created by: {order.created_by.username if order.created_by else 'N/A'}")
        print(f"   ├─ Service Location: {order.service_location.name if order.service_location else '❌ NONE'}")
        print(f"   ├─ Customer: {order.customer_name}")
        print(f"   ├─ Pickup Address: {order.pickup_address}")
        print(f"   └─ Status: {order.get_status_display()}\n")
    
    # 4. Detailed diagnosis for first unassigned order
    if unassigned.exists():
        order = unassigned.first()
        print_header(f"DETAILED DIAGNOSIS FOR ORDER {order.code}")
        
        print("📋 ORDER DETAILS:")
        print(f"   ID: {order.id}")
        print(f"   Order Type: {order.order_type}")
        print(f"   Rider: {order.rider.username if order.rider else '❌ NOT ASSIGNED'}")
        print(f"   Service Location: {order.service_location.name if order.service_location else '❌ NOT SET'}")
        print(f"   User: {order.user.username if order.user else '❌ NO USER'}")
        print(f"   Customer Name: {order.customer_name}")
        print(f"   Pickup Address: {order.pickup_address}")
        
        # Try to find location from pickup address
        print("\n🔍 LOCATION MATCHING LOGIC:")
        print(f"   Searching for locations in address: '{order.pickup_address}'")
        
        active_locs = Location.objects.filter(is_active=True)
        print(f"   Available locations to match: {[l.name for l in active_locs]}")
        
        matched_loc = None
        for loc in active_locs:
            if loc.name.lower() in order.pickup_address.lower():
                matched_loc = loc
                print(f"   ✓ MATCHED: {loc.name}")
                break
        
        if not matched_loc:
            print(f"   ❌ NO MATCH FOUND")
            print(f"   → Location names don't appear in pickup address")
            print(f"   → This is why rider assignment fails!")
        
        # Try with first active location as fallback
        if not matched_loc and active_locs.exists():
            matched_loc = active_locs.first()
            print(f"   ℹ️  Using fallback location: {matched_loc.name}")
        
        # Now check riders in that location
        if matched_loc:
            print(f"\n👥 RIDERS IN {matched_loc.name}:")
            riders = User.objects.filter(
                role='rider',
                service_location=matched_loc,
                is_active=True
            ).select_related('rider_profile').order_by('rider_profile__completed_jobs')
            
            print(f"   Available: {riders.count()}")
            
            if riders.exists():
                for rider in riders:
                    jobs = rider.rider_profile.completed_jobs if hasattr(rider, 'rider_profile') else 'N/A'
                    print(f"   ✓ {rider.username} (Jobs: {jobs})")
                print(f"\n   ✅ Could assign to: {riders.first().username}")
            else:
                print(f"   ❌ NO AVAILABLE RIDERS")
    
    # 5. Summary
    print_header("SUMMARY")
    print("Possible causes of rider not being assigned:\n")
    print("1. ❌ No active locations in database")
    print("   → Fix: Create locations via Location model")
    print()
    print("2. ❌ Order created without service_location")
    print("   → Fix: Pass service_location when creating order")
    print()
    print("3. ❌ Location doesn't match pickup_address")
    print("   → Fix: Ensure location name is in pickup address")
    print()
    print("4. ❌ No active riders in the location")
    print("   → Fix: Create riders and assign to location")
    print()

if __name__ == "__main__":
    try:
        diagnose_rider_assignment()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
