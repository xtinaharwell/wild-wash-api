# Multi-Spin Feature Documentation

## Overview

Users can now purchase multiple spins at once (1-50 spins) and watch them execute automatically. Each spin uses the active algorithm and displays results in real-time.

## Features

✅ **Buy Multiple Spins** - Purchase 1 to 50 spins in one transaction
✅ **Automatic Execution** - Spins execute automatically with smooth animations (0.8s between each)
✅ **Live Results Display** - See each spin result as it completes
✅ **Summary Statistics** - Get detailed stats after all spins complete
✅ **Balance Protection** - Server validates sufficient balance before executing
✅ **Algorithm Support** - Uses currently active algorithm for fairness
✅ **Transaction Logging** - All spins logged in game history and backend

## User Interface

### Multi-Spin Control Panel

Located below the main "SPIN" button:

```
┌─────────────────────────────────┐
│   QUICK MULTI-SPIN              │
├─────────────────────────────────┤
│   −  5 spins  +                │  ← Adjust count (1-50)
├─────────────────────────────────┤
│   Total Cost: KES 100            │  ← Shows cost calculation
│   @ KES 20 per spin              │
├─────────────────────────────────┤
│   [BUY 5 SPINS]                 │  ← Purple button
└─────────────────────────────────┘
```

### During Multi-Spin Execution

Shows real-time progress:
```
┌─────────────────────────────────┐
│ Multi-Spin Results (3/5)        │
├─────────────────────────────────┤
│  Spin #1  │ Spin #2  │ Spin #3 │  ← Results in grid
│  [2x]     │ [LOSE]   │ [1.5x]  │
│  +20 KES  │ -20 KES  │ +10 KES │
└─────────────────────────────────┘
```

### Final Summary

After all spins complete:

```
Total Cost:    -KES 100
Total Won:     +KES 180
Net Result:    +KES 80
Win Rate:      60%
```

## How It Works

### Frontend Flow

1. **User adjusts spin count** (1-50)
2. **Clicks "BUY X SPINS"** button
3. **Frontend validates:**
   - User has sufficient balance
   - Spending limits not exceeded
   - Not already spinning
4. **Calls backend endpoint:** `POST /api/casino/wallet/multi_spin/`
5. **Receives response with all spin results**
6. **Animates results one-by-one** (0.8s delay between spins)
7. **Displays summary statistics**
8. **Updates wallet and game history**

### Backend Flow

1. **Receives multi-spin request** with `num_spins` and `spin_cost`
2. **Validates:**
   - Number of spins (1-100)
   - Spin cost is positive
   - User has sufficient balance for total cost
   - Algorithm is configured
3. **Performs N spins using active algorithm**
4. **Calculates total cost and winnings**
5. **Deducts cost from wallet**
6. **Adds winnings to wallet**
7. **Returns all results + summary statistics**

## API Endpoint

### Request

```bash
POST /api/casino/wallet/multi_spin/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "num_spins": 5,
  "spin_cost": 20
}
```

### Response

```json
{
  "spins": [
    {
      "spin_number": 1,
      "result": {
        "id": 1,
        "label": "2x",
        "multiplier": 2,
        "color": "#D97706",
        "probability": 0.125
      },
      "spin_cost": 20,
      "winnings": 40,
      "net_result": 20
    },
    // ... more spins
  ],
  "summary": {
    "total_spins": 5,
    "total_cost": 100,
    "total_winnings": 180,
    "net_result": 80,
    "wins": 3,
    "losses": 1,
    "breaks_even": 1,
    "win_rate": "60.0%"
  },
  "balance": {
    "current": 1080,
    "total_deposits": 1200,
    "total_winnings": 450,
    "total_losses": 370
  },
  "algorithm_used": "Balanced - Default",
  "message": "Completed 5 spins. Net result: +80 KES"
}
```

## Frontend State Management

### New State Variables

```typescript
// Multi-spin control
const [isMultiSpinMode, setIsMultiSpinMode] = useState(false);
const [multiSpinCount, setMultiSpinCount] = useState(5);

// Multi-spin results
const [multiSpinResults, setMultiSpinResults] = useState<any[]>([]);
const [multiSpinSummary, setMultiSpinSummary] = useState<any>(null);
```

### New Functions

```typescript
// Execute multi-spin
const handleMultiSpin = async () => { ... }

// Check if multi-spin is allowed
const canMultiSpin = wallet >= (spinCost * multiSpinCount) && 
                     !isSpinning && 
                     !isMultiSpinMode;
```

## Examples

### Example 1: Quick 5-Spin Session

1. Click "+" button 4 times → Count = 5
2. See cost: KES 100
3. Click "BUY 5 SPINS"
4. Watch spins execute automatically
5. See final result: +80 KES profit

### Example 2: High Volume Testing

1. Set count to 20
2. Cost shows: KES 400
3. Click "BUY 20 SPINS"
4. Watch all 20 spins (16 seconds total)
5. Analyze win rate and patterns

### Example 3: Insufficient Balance

1. Balance: KES 150
2. Try to buy 10 spins (KES 200 cost)
3. Error: "Insufficient funds. You need KES 200 for 10 spins."
4. Button disabled (can't afford)

## Limits & Validation

- **Minimum Spins:** 1
- **Maximum Spins:** 50 (frontend), 100 (backend)
- **Spin Cost:** KES 20 (configurable)
- **Animation Delay:** 0.8 seconds between spins
- **Total Animation Time:** Up to 40 seconds for 50 spins

## Backend Validation

```python
# Number of spins validation
if num_spins < 1 or num_spins > 100:
    return error: "Number of spins must be between 1 and 100"

# Balance validation
if wallet.balance < total_cost:
    return error: "Insufficient balance"

# Algorithm validation
if not active_config:
    return error: "No spin algorithm is currently configured"
```

## Database & Logging

### Transaction Recording

Each multi-spin purchase creates:
- **One debit transaction** for total cost
  - Source: `multi_spin`
  - Notes: `"Multi-spin: 5 spins at 20 each"`
  
- **One credit transaction** for total winnings
  - Source: `game_winnings`
  - Notes: `"Multi-spin winnings: 5 spins using Balanced - Default"`

### Game History

All spins added to local game history:
- Each spin has unique timestamp
- Stored in reverse order (newest first)
- Synced with backend on next refresh

## Performance Considerations

- **Fast Animation:** 0.8 seconds between spins
- **Parallel Processing:** All spin logic done server-side (fast)
- **Network Efficient:** Single API call for all spins
- **UI Responsive:** Results displayed as they arrive
- **Memory Safe:** Results garbage collected after display

## Error Handling

### Server Errors

```
"Error performing multi-spin: ..."
```

Returns error detail and resets multi-spin state:
- Clears results
- Clears summary
- Re-enables controls

### Network Errors

Shows user-friendly error message and rolls back UI state.

### Validation Errors

```json
{
  "detail": "Insufficient balance. Required: 200, Available: 150"
}
```

## Technical Implementation

### Frontend Multi-Spin Flow

```
1. Validate locally (balance, spin count)
2. Call API endpoint with num_spins & spin_cost
3. Receive array of results in response
4. Loop through results with 0.8s delay
5. For each result:
   - Update multiSpinResults state
   - Animate wheel (visual feedback)
   - Wait 0.8 seconds
6. Display final summary
7. Update wallet and game history
8. Clean up and reset state
```

### Backend Multi-Spin Flow

```
1. Validate input (num_spins, spin_cost)
2. Check user balance (total_cost)
3. Get active algorithm
4. For each spin:
   - Call algorithm.spin()
   - Calculate winnings
   - Add to results array
5. Deduct total cost from wallet
6. Add total winnings to wallet
7. Log transactions
8. Calculate summary stats
9. Return response
```

## Customization

### Change Animation Speed

In `spin/page.tsx`, find the delay:
```typescript
await new Promise(resolve => setTimeout(resolve, 800)); // Change this
```

Options:
- 500ms = Faster, more exciting
- 1000ms = Slower, more deliberate
- 1500ms = Very slow, dramatic

### Change Max Spins

Frontend (user UI limit):
```typescript
setMultiSpinCount(prev => Math.min(50, prev + 1)) // Change 50
```

Backend (hard limit):
```python
if num_spins < 1 or num_spins > 100:  # Change 100
```

### Change Button Colors

Purple theme in spin/page.tsx:
```tsx
// Primary button (BUY X SPINS)
from-purple-600 via-purple-700 to-purple-600

// Results card
border-purple-400/40
text-purple-300
```

## Future Enhancements

- [ ] Preset quick-buy buttons (5, 10, 20 spins)
- [ ] Pause/resume during multi-spin execution
- [ ] Variable animation speeds (slow/normal/fast)
- [ ] Bulk discount pricing (5% off 10+ spins, etc.)
- [ ] Multi-spin history/statistics tracking
- [ ] Export results to CSV
- [ ] Replay animation
- [ ] Soundscape for multi-spins

## Testing

### Manual Testing Checklist

- [ ] Buy 1 spin - verify execution
- [ ] Buy 5 spins - verify all complete
- [ ] Buy max (50) - verify completes in ~40s
- [ ] Insufficient balance - verify error
- [ ] Spending limit exceeded - verify block
- [ ] Change spin count - verify cost updates
- [ ] Cancel mid-spin - verify state resets
- [ ] Check game history - verify entries added
- [ ] Check backend transactions - verify recorded
- [ ] Switch algorithms - verify correct algorithm used

### API Testing

```bash
# Test 5 spins
curl -X POST http://localhost:8000/api/casino/wallet/multi_spin/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "num_spins": 5,
    "spin_cost": 20
  }'

# Test invalid (too many spins)
curl -X POST http://localhost:8000/api/casino/wallet/multi_spin/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "num_spins": 101,
    "spin_cost": 20
  }'

# Test insufficient balance
curl -X POST http://localhost:8000/api/casino/wallet/multi_spin/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "num_spins": 1000,
    "spin_cost": 20
  }'
```

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-12-25
