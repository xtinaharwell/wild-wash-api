# Game Wallet Implementation

This document describes the complete Game Wallet implementation with M-Pesa STK Push integration.

## Overview

The Game Wallet allows users to top up their balance using M-Pesa STK Push, and play casino games with their balance. Payments are processed via Safaricom's Daraja API.

## Architecture

### Backend (Django)

#### Models
- **GameWallet**: Tracks user balance, total deposits, winnings, and losses
- **GameTransaction**: Records every transaction (deposits, debits, credits, etc.)
- **Payment**: Existing model, extended to support game wallet top-ups
- **MpesaSTKRequest**: Tracks STK request lifecycle

#### API Endpoints

##### Games App
- `GET /games/wallet-balance/` - Get current wallet balance and stats
- `GET /games/wallet/balance/` - Authenticated endpoint for wallet balance
- `GET /games/wallet/transactions/` - Get transaction history
- `GET /games/wallet/full/` - Get full wallet info with transactions

##### Payments App  
- `POST /payments/mpesa/stk-push/` - Initiate STK Push (accepts `order_id: null` for game wallet)
- `POST /payments/mpesa/callback/` - M-Pesa callback (auto-credits wallet on success)
- `GET /payments/payment-status/` - Check payment status by `checkout_request_id`

### Frontend (Next.js)

**File**: `wildwash/app/games/wallet/page.tsx`

Features:
- Fetch real balance from backend on load
- Quick amount selection or custom amount entry
- Phone number input (auto-formatted)
- STK Push initiation
- **Polling mechanism**: Polls payment status every 2 seconds for up to 30 attempts
- Auto-refresh of balance after successful payment

## Flow Diagram

```
User navigates to Wallet Page
       ↓
Fetch balance from /games/wallet-balance/
       ↓
User enters amount + phone
       ↓
POST /payments/mpesa/stk-push/ with { amount, phone, order_id: null }
       ↓
STK prompt appears on user's phone
       ↓
User enters M-Pesa PIN
       ↓
M-Pesa processes and sends callback
       ↓
POST /payments/mpesa/callback/ (payment status updated to 'success')
       ↓
Callback handler credits GameWallet via add_funds()
       ↓
Frontend polling detects success via GET /payments/payment-status/
       ↓
Balance is fetched again and displayed to user
```

## Database Schema

### GameWallet
```
- id (PK)
- user (FK → User, OneToOne)
- balance (Decimal)
- total_deposits (Decimal)
- total_winnings (Decimal)
- total_losses (Decimal)
- created_at (DateTime)
- updated_at (DateTime)
```

### GameTransaction
```
- id (PK)
- wallet (FK → GameWallet)
- transaction_type (CharField: 'deposit', 'debit', 'credit', 'refund', 'withdrawal')
- amount (Decimal)
- source (CharField: e.g., 'mpesa', 'game_play', 'game_winnings')
- payment_id (Int, optional reference to Payment model)
- notes (TextField)
- created_at (DateTime)
- updated_at (DateTime)
```

Indexes:
- (wallet, created_at)
- (transaction_type)

## Configuration

### Environment Variables (Django)

Required M-Pesa Daraja credentials in `.env`:
```
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_BUSINESS_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-domain.com/api/payments/mpesa/callback/
```

### Django Settings

Ensure `games` is in `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'games',
    # ...
]
```

## Usage Examples

### 1. Initiate STK Push for Game Wallet Top-up

**Request:**
```bash
curl -X POST https://api.wildwash.app/api/payments/mpesa/stk-push/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000,
    "phone": "254712345678",
    "order_id": null
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "STK push sent to your phone",
  "checkout_request_id": "ws1234567890",
  "order_id": "GAME_WALLET_TOPUP",
  "amount": 1000
}
```

### 2. Check Payment Status (for frontend polling)

**Request:**
```bash
curl https://api.wildwash.app/api/payments/payment-status/?checkout_request_id=ws1234567890
```

**Response (Pending):**
```json
{
  "status": "pending",
  "amount": 1000,
  "phone": "254712345678",
  "initiated_at": "2025-12-24T10:30:00Z",
  "completed_at": null,
  "error_message": null
}
```

**Response (Success):**
```json
{
  "status": "success",
  "amount": 1000,
  "phone": "254712345678",
  "initiated_at": "2025-12-24T10:30:00Z",
  "completed_at": "2025-12-24T10:32:15Z",
  "error_message": null
}
```

### 3. Get Wallet Balance

**Request:**
```bash
curl https://api.wildwash.app/api/games/wallet-balance/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "balance": 5000.00,
  "total_deposits": 10000.00,
  "total_winnings": 2000.00,
  "total_losses": 7000.00
}
```

### 4. Get Transaction History

**Request:**
```bash
curl https://api.wildwash.app/api/games/wallet/transactions/?limit=10 \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "transaction_type": "deposit",
      "transaction_type_display": "Deposit",
      "amount": "1000.00",
      "source": "mpesa",
      "notes": "M-Pesa top-up via STK Push",
      "created_at": "2025-12-24T10:32:15Z",
      "updated_at": "2025-12-24T10:32:15Z"
    }
  ]
}
```

## Testing

### Local Testing with Sandbox

1. **Start the dev server:**
   ```bash
   cd wild-wash-api
   python manage.py runserver
   ```

2. **Navigate to wallet page:**
   ```
   http://localhost:3000/games/wallet
   ```

3. **Use Daraja sandbox credentials** (get from https://developer.safaricom.co.ke)

4. **Test flow:**
   - Top up with test phone number from Daraja
   - Check phone for STK prompt (in Daraja sandbox UI)
   - Complete payment
   - Verify balance updates

### Unit Tests

Create `wild-wash-api/games/tests.py` to test:
- GameWallet creation
- add_funds() method
- deduct_funds() method
- add_winnings() method
- Transaction creation
- API endpoints

## Admin Interface

Access Django admin at `/admin`:
- **Game Wallets**: View user balances, stats
- **Game Transactions**: Audit all wallet transactions

## Error Handling

### Common Issues

**STK Push Failed:**
- Verify Daraja credentials are correct
- Check phone number format (must be 254xxxxxxxxx)
- Ensure callback URL is accessible from internet

**Balance Not Updating:**
- Check payment status endpoint for error messages
- Verify callback is being received by POST /payments/mpesa/callback/
- Check logs for GameWallet.add_funds() exceptions

**Polling Timeout:**
- If payment succeeds but balance doesn't update, manually refresh page
- Check Django logs for callback processing errors

## Security Notes

- `order_id: null` is allowed specifically for game wallet top-ups (checked via `is_game_wallet` flag in payload)
- Payment status endpoint is publicly accessible but only returns minimal info
- GameWallet CRUD is restricted to authenticated users via API permissions
- Admin access to wallets requires Django staff permissions

## Future Enhancements

- Add withdrawal functionality (reverse flow)
- Implement game playing endpoints that deduct from wallet
- Add webhook-based balance sync instead of polling
- Implement fraud detection (suspicious patterns)
- Add refund mechanism for disputed transactions
- Multi-currency support
