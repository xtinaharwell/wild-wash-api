# Examples: Creating Orders That Trigger Rider Notifications

## Prerequisites

Before creating orders that notify riders, ensure your data is set up:

```python
# 1. Create a Location
from users.models import Location
location = Location.objects.create(
    name="Nairobi Downtown",
    description="Central business district"
)

# 2. Create a Rider assigned to that location
from users.models import User
rider = User.objects.create_user(
    username="john_rider",
    email="john@wildwash.com",
    password="secure123",
    phone="+254712345678",
    role="rider",
    service_location=location,
    is_active=True
)

# 3. Create Services
from services.models import Service
wash_service = Service.objects.create(
    name="Hand Wash",
    description="Professional hand washing",
    price=500.00
)

dry_clean_service = Service.objects.create(
    name="Dry Clean",
    description="Professional dry cleaning",
    price=800.00
)

# 4. Create a Customer
customer = User.objects.create_user(
    username="alice_customer",
    email="alice@example.com",
    password="customer123",
    phone="+254798765432",
    role="customer"
)
```

---

## Example 1: Simple Order (Single Service)

```python
from orders.models import Order

order = Order.objects.create(
    user=customer,
    service_location=location,  # 🔴 CRITICAL: Must match rider's location!
    pickup_address="123 Main Street, Nairobi",
    dropoff_address="456 Park Lane, Nairobi",
    urgency=2,
    items=5,
    package=1,
    weight_kg=2.5,
    status='requested'
)

# Attach service (M2M relationship)
order.services.add(wash_service)

# Set primary service for backward compatibility
order.service = wash_service
order.save()

print(f"Order {order.code} created!")
print(f"✅ Notifications sent to {order.service_location.staff_members.filter(role='rider').count()} riders")
```

**Result:**

- ✅ Order code: `WW-ABC123`
- ✅ John (rider) gets notification: "New order WW-ABC123 in your area. Pickup: 123 Main Street..."
- 🔊 Sound plays on John's rider dashboard
- 🔔 Browser notification shows

---

## Example 2: Multiple Services Order

```python
order = Order.objects.create(
    user=customer,
    service_location=location,  # 🔴 CRITICAL!
    pickup_address="789 Oak Avenue, Nairobi",
    dropoff_address="321 Elm Street, Nairobi",
    urgency=3,  # More urgent
    items=8,
    package=2,
    weight_kg=4.0,
    status='requested'
)

# Multiple services
order.services.add(wash_service, dry_clean_service)

# Set primary service
order.service = wash_service
order.save()

print(f"Order {order.code} with 2 services created!")
print(f"Total price: KES {order.get_total_price()}")
```

**Result:**

- ✅ Riders see: "New order WW-XYZ789 in your area"
- ✅ Order includes both Wash and Dry Clean services
- ✅ Total price: KES 1300.00
- 🔊 Sound plays

---

## Example 3: Via REST API (From Your Backend)

```python
# Django shell or script
from rest_framework.test import APIClient
from django.contrib.auth.models import Token

client = APIClient()

# Get rider's token
token = Token.objects.get(user=rider)
client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

# Create order endpoint
order_data = {
    'services': [wash_service.id, dry_clean_service.id],
    'pickup_address': '999 King Road, Nairobi',
    'dropoff_address': '111 Queen Avenue, Nairobi',
    'urgency': 2,
    'items': 6,
    'package': 1,
    'weight_kg': 3.5
}

response = client.post('/orders/', order_data, format='json')
print(response.json())
```

---

## Example 4: Django Admin Command

Create a management command to generate test orders:

**File: `orders/management/commands/create_test_orders.py`**

```python
from django.core.management.base import BaseCommand
from users.models import User, Location
from services.models import Service
from orders.models import Order

class Command(BaseCommand):
    help = 'Create test orders to trigger rider notifications'

    def handle(self, *args, **options):
        # Get or create location
        location, _ = Location.objects.get_or_create(
            name="Nairobi",
            defaults={"description": "Central Nairobi"}
        )

        # Get services
        services = Service.objects.all()[:2]

        # Get customer
        customer = User.objects.filter(role='customer').first()
        if not customer:
            self.stdout.write(self.style.ERROR('No customer found!'))
            return

        # Create test order
        order = Order.objects.create(
            user=customer,
            service_location=location,
            pickup_address="123 Test Street",
            dropoff_address="456 Test Ave",
            urgency=2,
            items=5,
            status='requested'
        )

        # Add services
        for service in services:
            order.services.add(service)

        order.service = services[0]
        order.save()

        # Count riders notified
        rider_count = User.objects.filter(
            role='rider',
            service_location=location,
            is_active=True
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Order {order.code} created! '
                f'{rider_count} rider(s) notified'
            )
        )

# Run with:
# python manage.py create_test_orders
```

---

## Example 5: Checking Notifications in Django Shell

```python
from django.core.management import execute_from_command_line
from notifications.models import Notification
from users.models import User

# Get a rider
rider = User.objects.get(username='john_rider')

# Check their notifications
notifications = Notification.objects.filter(user=rider)
print(f"Total notifications: {notifications.count()}")

# Check new orders
new_orders = notifications.filter(notification_type='new_order')
print(f"New order notifications: {new_orders.count()}")

# Display latest
for notif in new_orders[:5]:
    print(f"- {notif.message}")
    print(f"  Order: {notif.order.code}")
    print(f"  Read: {notif.is_read}")
    print()
```

---

## Example 6: Verify Notification Via API

```bash
#!/bin/bash

# Get rider token
RIDER_TOKEN="your_rider_token_here"
API_URL="http://127.0.0.1:8000"

# Fetch notifications
curl -H "Authorization: Token $RIDER_TOKEN" \
  "$API_URL/notifications/" | jq '.'

# Filter new orders
curl -H "Authorization: Token $RIDER_TOKEN" \
  "$API_URL/notifications/?notification_type=new_order" | jq '.'

# Mark specific notification as read
NOTIF_ID=1
curl -X POST \
  -H "Authorization: Token $RIDER_TOKEN" \
  "$API_URL/notifications/$NOTIF_ID/mark_read/"
```

---

## Example 7: Complete Workflow (Step-by-Step)

```python
# 1. Setup
from users.models import User, Location
from services.models import Service
from orders.models import Order
from notifications.models import Notification

# Create location
location = Location.objects.create(name="Downtown")

# Create rider
rider = User.objects.create_user(
    username="rider1",
    password="pass123",
    role="rider",
    service_location=location,
    is_active=True,
    phone="254712345678"
)

# Create customer
customer = User.objects.create_user(
    username="customer1",
    password="pass123",
    role="customer",
    phone="254798765432"
)

# Create service
service = Service.objects.create(name="Wash", price=500)

# 2. Create Order (automatically triggers notification)
order = Order.objects.create(
    user=customer,
    service_location=location,
    pickup_address="Main St",
    dropoff_address="Park Ave",
    status='requested'
)
order.services.add(service)
order.service = service
order.save()

# 3. Verify notification was created
notification = Notification.objects.get(user=rider, order=order)
print(f"✅ Notification created: {notification.message}")
print(f"✅ Type: {notification.notification_type}")
print(f"✅ Read: {notification.is_read}")

# 4. Simulate rider marking as read (happens automatically in frontend)
# In real usage, the frontend hook does this:
# fetch('/notifications/1/mark_read/', { method: 'POST', ... })

print(f"\n🔊 Sound would play in rider's browser")
print(f"🔔 Browser notification would show")
```

---

## Troubleshooting Examples

### Issue: Order created but rider not notified

```python
# Check 1: Does order have service_location?
print(f"Order location: {order.service_location}")

# Check 2: Does rider have matching location?
print(f"Rider location: {rider.service_location}")
print(f"Match: {order.service_location == rider.service_location}")

# Check 3: Is rider active?
print(f"Rider active: {rider.is_active}")

# Check 4: Is notification in database?
notif = Notification.objects.filter(order=order, user=rider).first()
print(f"Notification exists: {notif is not None}")

# Check 5: What's the notification message?
if notif:
    print(f"Message: {notif.message}")
    print(f"Type: {notif.notification_type}")
```

### Issue: Multiple riders but only some get notified

```python
# Check all riders at location
riders = User.objects.filter(
    service_location=order.service_location,
    role='rider',
    is_active=True
)
print(f"Total riders: {riders.count()}")
for r in riders:
    print(f"  - {r.username}: is_active={r.is_active}")

# Check notifications created
notifs = Notification.objects.filter(order=order)
print(f"Notifications created: {notifs.count()}")
for n in notifs:
    print(f"  - {n.user.username}")
```

---

## Key Points

✅ **Always set `service_location`** on order - this links to riders
✅ **Rider must have matching `service_location`** - location comparison
✅ **Rider must be `is_active=True`** - inactive riders don't get notifications
✅ **Rider must have `role='rider'`** - system filters by role
✅ **Add services to M2M** - either through `.add()` or via API
✅ **Set primary `service` field** - for backward compatibility

---

## Running Your Test

```bash
# 1. Open two terminals

# Terminal 1: Start Django shell
cd wild-wash-api
python manage.py shell

# Terminal 2: Start rider dashboard
cd ../wildwash
npm run dev

# In Terminal 1: Create order using examples above
# In Browser (Terminal 2):
#   - Login as rider
#   - Open Network tab (F12)
#   - Listen for sound!
```
