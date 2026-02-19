#!/usr/bin/env python
import requests
import json
import sys

API_BASE = "http://localhost:8000"

# Test Step 1: Request password reset code
print("=" * 60)
print("Step 1: Testing RequestPasswordResetView")
print("=" * 60)

payload = {"phone": "+254718693484"}
response = requests.post(f"{API_BASE}/users/password-reset/request/", json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

# Get the code from database
sys.path.insert(0, '.')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
import django
django.setup()

from users.models import PasswordResetCode

code_obj = PasswordResetCode.objects.filter(phone="+254718693484", is_used=False).order_by('-created_at').first()
if code_obj:
    code = code_obj.code
    print(f"\nCode generated: {code}")
else:
    print("ERROR: No code found in database!")
    sys.exit(1)

# Test Step 2: Verify password reset code
print("\n" + "=" * 60)
print("Step 2: Testing VerifyPasswordResetCodeView")
print("=" * 60)

payload = {"phone": "+254718693484", "code": code}
response = requests.post(f"{API_BASE}/users/password-reset/verify/", json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

# Test Step 3: Confirm password reset
print("\n" + "=" * 60)
print("Step 3: Testing ConfirmPasswordResetView")
print("=" * 60)

payload = {"phone": "+254718693484", "code": code, "password": "NewPassword123"}
response = requests.post(f"{API_BASE}/users/password-reset/confirm/", json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

print("\n" + "=" * 60)
print("✓ All password reset API tests completed!")
print("=" * 60)
