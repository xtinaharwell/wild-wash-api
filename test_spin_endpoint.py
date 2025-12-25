#!/usr/bin/env python
"""Test the new spin endpoint"""
import os
import sys
import django

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from casino.models import GameWallet
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

# Create test user
user, created = User.objects.get_or_create(
    username='spin_test_user',
    defaults={'email': 'spin@test.com'}
)

# Create wallet with balance
wallet, _ = GameWallet.objects.get_or_create(user=user)
wallet.balance = 1000
wallet.save()

# Create token
token, _ = Token.objects.get_or_create(user=user)

print("=" * 70)
print("Testing Record Spin Endpoint")
print("=" * 70)
print(f"\n✓ Test user: {user.username}")
print(f"✓ Initial balance: KES {wallet.balance}")
print(f"✓ Token: {token.key[:20]}...")

# Initialize test client
client = Client()

# Test 1: Record a winning spin
print("\n--- Test 1: Record Winning Spin (5x multiplier) ---")
response = client.post(
    '/api/casino/wallet/record_spin/',
    data=json.dumps({
        'spin_cost': 20,
        'winnings': 100,
        'multiplier': 5,
        'result_label': '5x'
    }),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Token {token.key}'
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ Response: {json.dumps(data, indent=2)}")
    print(f"✓ New balance: KES {data['balance']}")
    print(f"✓ Net result: KES {data['net_result']}")
else:
    print(f"✗ Error: {response.content}")

# Refresh wallet from DB
wallet.refresh_from_db()
print(f"✓ Backend balance: KES {wallet.balance}")
print(f"✓ Total losses: KES {wallet.total_losses}")
print(f"✓ Total winnings: KES {wallet.total_winnings}")

# Test 2: Record a losing spin
print("\n--- Test 2: Record Losing Spin (0.5x multiplier = loss) ---")
response = client.post(
    '/api/casino/wallet/record_spin/',
    data=json.dumps({
        'spin_cost': 20,
        'winnings': 10,  # 0.5x of cost
        'multiplier': 0.5,
        'result_label': '0.5x'
    }),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Token {token.key}'
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ New balance: KES {data['balance']}")
    print(f"✓ Net result: KES {data['net_result']}")
else:
    print(f"✗ Error: {response.content}")

wallet.refresh_from_db()
print(f"✓ Backend balance: KES {wallet.balance}")

# Test 3: Record a LOSE result
print("\n--- Test 3: Record Lose Spin (0x multiplier = total loss) ---")
response = client.post(
    '/api/casino/wallet/record_spin/',
    data=json.dumps({
        'spin_cost': 20,
        'winnings': 0,
        'multiplier': 0,
        'result_label': 'LOSE'
    }),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Token {token.key}'
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ New balance: KES {data['balance']}")
    print(f"✓ Net result: KES {data['net_result']}")
else:
    print(f"✗ Error: {response.content}")

wallet.refresh_from_db()
print(f"✓ Backend balance: KES {wallet.balance}")

# Test 4: Insufficient balance
print("\n--- Test 4: Test Insufficient Balance ---")
response = client.post(
    '/api/casino/wallet/record_spin/',
    data=json.dumps({
        'spin_cost': 10000,  # More than available balance
        'winnings': 0,
        'multiplier': 0,
        'result_label': 'LOSE'
    }),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Token {token.key}'
)

print(f"Status: {response.status_code}")
if response.status_code == 400:
    data = response.json()
    print(f"✓ Correctly rejected: {data['detail']}")
else:
    print(f"✗ Expected 400, got {response.status_code}")

# Test 5: No authentication
print("\n--- Test 5: Test Without Authentication ---")
response = client.post(
    '/api/casino/wallet/record_spin/',
    data=json.dumps({
        'spin_cost': 20,
        'winnings': 100,
        'multiplier': 5,
        'result_label': '5x'
    }),
    content_type='application/json'
)

print(f"Status: {response.status_code}")
if response.status_code == 401:
    print(f"✓ Correctly rejected (requires auth)")
else:
    print(f"✗ Expected 401, got {response.status_code}")

# Final summary
print("\n" + "=" * 70)
print("FINAL WALLET STATE")
print("=" * 70)
wallet.refresh_from_db()
print(f"Current Balance:    KES {wallet.balance}")
print(f"Total Deposits:     KES {wallet.total_deposits}")
print(f"Total Winnings:     KES {wallet.total_winnings}")
print(f"Total Losses:       KES {wallet.total_losses}")
print(f"Transactions:       {wallet.transactions.count()}")
print("=" * 70)

# Cleanup
print("\nCleaning up test data...")
wallet.delete()
user.delete()
print("✓ Test complete!")
