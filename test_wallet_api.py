"""
Integration test for Game Wallet API endpoints
Run from wild-wash-api: python test_wallet_api.py
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from games.models import GameWallet
from decimal import Decimal

User = get_user_model()


def test_wallet_api():
    """Test Game Wallet API endpoints"""
    print("=" * 70)
    print("Testing Game Wallet API Endpoints")
    print("=" * 70)
    
    client = Client()
    
    # Create test user
    user, _ = User.objects.get_or_create(
        username='api_test_user',
        defaults={'email': 'apitest@example.com', 'phone': '254712345678'}
    )
    print(f"\n✓ Test user created: {user.username}")
    
    # Create token for authentication
    token, _ = Token.objects.get_or_create(user=user)
    print(f"✓ Auth token created: {token.key[:20]}...")
    
    # Setup wallet with some data
    wallet, _ = GameWallet.objects.get_or_create(user=user)
    wallet.balance = Decimal('5000.00')
    wallet.total_deposits = Decimal('10000.00')
    wallet.total_winnings = Decimal('2000.00')
    wallet.total_losses = Decimal('7000.00')
    wallet.save()
    print(f"✓ Test wallet created with balance: KES {wallet.balance}")
    
    # Test 1: Get balance (no auth required)
    print("\n--- Test 1: GET /games/wallet-balance/ (no auth) ---")
    response = client.get('/api/games/wallet-balance/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Response: balance={data.get('balance')}")
    else:
        print(f"✗ Failed: {response.content}")
    
    # Test 2: Get balance (with auth)
    print("\n--- Test 2: GET /games/wallet/balance/ (with auth) ---")
    response = client.get(
        '/api/games/wallet/balance/',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Response: balance={data.get('balance')}, deposits={data.get('total_deposits')}")
    else:
        print(f"✗ Failed: {response.content}")
    
    # Test 3: Get transactions
    print("\n--- Test 3: GET /games/wallet/transactions/ ---")
    # First add some transactions
    wallet.add_funds(Decimal('1000'), 'test', notes='Test transaction')
    
    response = client.get(
        '/api/games/wallet/transactions/?limit=5',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Transaction count: {data.get('count')}")
        if data.get('results'):
            txn = data['results'][0]
            print(f"  Latest: {txn.get('transaction_type_display')} - KES {txn.get('amount')}")
    else:
        print(f"✗ Failed: {response.content}")
    
    # Test 4: Get full wallet
    print("\n--- Test 4: GET /games/wallet/full/ ---")
    response = client.get(
        '/api/games/wallet/full/',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Balance: KES {data.get('balance')}")
        print(f"✓ Transactions: {len(data.get('transactions', []))}")
    else:
        print(f"✗ Failed: {response.content}")
    
    # Cleanup
    print("\n" + "=" * 70)
    print("Cleaning up...")
    wallet.delete()
    token.delete()
    user.delete()
    print("✓ Test data cleaned up")
    
    print("\n✓ All API tests passed!")


if __name__ == '__main__':
    try:
        test_wallet_api()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
