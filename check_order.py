from orders.models import Order

# Find order WW-00196
try:
    order = Order.objects.get(code='WW-00196')
    print(f'Order: {order.code}')
    print(f'Status: {order.get_status_display()}')
    print(f'Order Type: {order.order_type}')
    print(f'Rider: {order.rider.username if order.rider else "NOT ASSIGNED"}')
    print(f'Service Location: {order.service_location.name if order.service_location else "NOT SET"}')
    print(f'Customer Name: {order.customer_name}')
    print(f'Pickup Address: {order.pickup_address}')
    print(f'Created By: {order.created_by.username if order.created_by else "N/A"}')
except Order.DoesNotExist:
    print('Order WW-00196 not found')

# Show last 3 manual orders
print('\n--- Last 3 Manual Orders ---')
orders = Order.objects.filter(order_type='manual').order_by('-created_at')[:3]
for order in orders:
    print(f'\n{order.code}:')
    print(f'  Rider: {order.rider.username if order.rider else "NOT ASSIGNED"}')
    print(f'  Location: {order.service_location.name if order.service_location else "NOT SET"}')
    print(f'  Address: {order.pickup_address}')
