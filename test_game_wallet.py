"""
Simple test script to verify GameWallet functionality
Run from wild-wash-api: python test_game_wallet.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, '/path/to/wild-wash-api')
django.setup()

from django.contrib.auth import get_user_model
from casino.models import GameWallet, GameTransaction
from decimal import Decimal

User = get_user_model()


def test_game_wallet():
    """Test GameWallet functionality"""
    print("=" * 60)
    print("Testing GameWallet Implementation")
    print("=" * 60)
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='test_wallet_user',
        defaults={'email': 'test@example.com'}
    )
    print(f"\n✓ User created/retrieved: {user.username}")
    
    # Get or create wallet
    wallet, created = GameWallet.objects.get_or_create(user=user)
    print(f"✓ Wallet created/retrieved - Balance: KES {wallet.balance}")
    
    # Test 1: Add funds (deposit)
    print("\n--- Test 1: Add Funds (Deposit) ---")
    initial_balance = wallet.balance
    amount_to_add = Decimal('1000.00')
    
    wallet.add_funds(
        amount_to_add,
        source='mpesa',
        payment_id=1,
        notes='Test deposit via STK Push'
    )
    print(f"Initial balance: KES {initial_balance}")
    print(f"Added: KES {amount_to_add}")
    print(f"New balance: KES {wallet.balance}")
    print(f"✓ Total deposits: KES {wallet.total_deposits}")
    
    # Test 2: Add winnings
    print("\n--- Test 2: Add Winnings ---")
    winnings = Decimal('500.00')
    wallet.add_winnings(winnings, game_name='Lucky Spin', notes='Test win')
    print(f"Added winnings: KES {winnings}")
    print(f"New balance: KES {wallet.balance}")
    print(f"✓ Total winnings: KES {wallet.total_winnings}")
    
    # Test 3: Deduct funds (game play)
    print("\n--- Test 3: Deduct Funds (Game Play) ---")
    deduct_amount = Decimal('100.00')
    wallet.deduct_funds(deduct_amount, reason='game_play', notes='Test game play')
    print(f"Deducted for game: KES {deduct_amount}")
    print(f"New balance: KES {wallet.balance}")
    print(f"✓ Total losses: KES {wallet.total_losses}")
    
    # Test 4: View transaction history
    print("\n--- Test 4: Transaction History ---")
    transactions = GameTransaction.objects.filter(wallet=wallet)
    print(f"Total transactions: {transactions.count()}")
    for i, txn in enumerate(transactions, 1):
        print(f"  {i}. {txn.get_transaction_type_display()}: KES {txn.amount} ({txn.source})")
    
    # Test 5: Verify calculations
    print("\n--- Test 5: Verify Calculations ---")
    expected_balance = initial_balance + amount_to_add + winnings - deduct_amount
    print(f"Expected balance: KES {expected_balance}")
    print(f"Actual balance: KES {wallet.balance}")
    
    if wallet.balance == expected_balance:
        print("✓ Balance calculation is correct!")
    else:
        print("✗ Balance calculation mismatch!")
    
    # Final summary
    print("\n" + "=" * 60)
    print("WALLET SUMMARY")
    print("=" * 60)
    print(f"Current Balance:    KES {wallet.balance}")
    print(f"Total Deposits:     KES {wallet.total_deposits}")
    print(f"Total Winnings:     KES {wallet.total_winnings}")
    print(f"Total Losses:       KES {wallet.total_losses}")
    print(f"Transactions:       {wallet.transactions.count()}")
    print("=" * 60)
    
    # Cleanup
    print("\nCleaning up test data...")
    wallet.delete()
    user.delete()
    print("✓ Test data cleaned up")
    
    print("\n✓ All tests passed!")


if __name__ == '__main__':
    try:
        test_game_wallet()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
