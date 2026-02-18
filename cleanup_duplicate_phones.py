#!/usr/bin/env python
"""
Django management script to clean up duplicate phone numbers
Keeps the most recently created user for each phone number
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.contrib.auth import get_user_model
from collections import defaultdict

User = get_user_model()

# Find all duplicate phone numbers
phone_groups = defaultdict(list)
for user in User.objects.all():
    if user.phone:
        phone_groups[user.phone].append(user)

# Process duplicates
deleted_count = 0
for phone, users in phone_groups.items():
    if len(users) > 1:
        print(f"\n📱 Phone: {phone}")
        print(f"   Found {len(users)} users with this phone:")
        
        # Sort by date_joined, keep the most recent one
        users_sorted = sorted(users, key=lambda u: u.date_joined, reverse=True)
        
        for i, user in enumerate(users_sorted, 1):
            print(f"   {i}. {user.username} ({user.email}) - Created: {user.date_joined}")
        
        # Delete all but the first (most recent)
        to_delete = users_sorted[1:]
        for user in to_delete:
            print(f"   ❌ Deleting: {user.username}")
            user.delete()
            deleted_count += 1

print(f"\n✅ Cleanup complete!")
print(f"   Total users deleted: {deleted_count}")
print(f"\nNow run: python manage.py makemigrations users")
print(f"Then run: python manage.py migrate")
