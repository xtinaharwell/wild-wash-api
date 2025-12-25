# Algorithm System Implementation - Quick Start

## What Was Added

### 1. **Algorithm Module** (`casino/algorithms.py`)
- 5 pre-built algorithms with different probability distributions
- Base class for creating custom algorithms
- Registry system for managing algorithms

### 2. **Database Model** (`casino/models.py`)
- `SpinAlgorithmConfiguration`: Store and manage algorithm settings
- One-to-one relationship with active algorithm
- Optional scheduling support (start_time, end_time, days_of_week)

### 3. **Admin Interface** (`casino/admin.py`)
- Full Django admin integration for managing algorithms
- Easy switching between algorithms
- Schedule support for time-based activation

### 4. **API Endpoints** (`casino/views.py`, `casino/urls.py`)
- `/api/casino/algorithms/available/` - List all available algorithms
- `/api/casino/algorithms/active/` - Get currently active algorithm
- `/api/casino/algorithms/all_configurations/` - Get all stored configurations
- `/api/casino/algorithms/{id}/activate/` - Switch active algorithm
- `/api/casino/wallet/spin/` - Perform a spin using active algorithm

### 5. **Management Command**
- `python manage.py init_algorithms` - Initialize default algorithm configs

## Step-by-Step Setup

### 1️⃣ Navigate to Backend
```bash
cd wild-wash-api
```

### 2️⃣ Create and Apply Migration
```bash
python manage.py makemigrations casino
python manage.py migrate
```

### 3️⃣ Initialize Algorithms
```bash
python manage.py init_algorithms
```

You should see:
```
Initializing spin algorithms...
✓ Created: Balanced - Default
✓ Created: Conservative - Default
✓ Created: Generous - Default
✓ Created: Peak Hour - Default
✓ Created: Late Night - Default

Algorithm initialization complete!
Active algorithm: Balanced - Default
```

### 4️⃣ Verify in Admin
```
http://localhost:8000/admin/casino/spinalgorithmconfiguration/
```

You should see 5 algorithm configurations, with one marked as "ACTIVE".

## Testing the APIs

### Test 1: Get Available Algorithms
```bash
curl http://localhost:8000/api/casino/algorithms/available/
```

### Test 2: Get Active Algorithm
```bash
curl http://localhost:8000/api/casino/algorithms/active/
```

### Test 3: Perform a Spin (Requires Authentication)
```bash
curl -X POST http://localhost:8000/api/casino/wallet/spin/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"spin_cost": 20}'
```

### Test 4: Switch Algorithm (Requires Admin)
```bash
curl -X POST http://localhost:8000/api/casino/algorithms/2/activate/ \
  -H "Authorization: Token YOUR_ADMIN_TOKEN"
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│   Frontend (React)                      │
│   - Display wheel animation             │
│   - Show algorithm name (optional)      │
└──────────────┬──────────────────────────┘
               │ POST /api/casino/wallet/spin/
               │ { spin_cost: 20 }
               ▼
┌─────────────────────────────────────────┐
│   Backend Views (Django)                │
│   - Validate user balance               │
│   - Get active algorithm                │
│   - Call algorithm.spin()               │
│   - Update wallet & transactions        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Algorithm Module                      │
│   - BalancedAlgorithm                   │
│   - ConservativeAlgorithm               │
│   - GenerousAlgorithm                   │
│   - PeakHourAlgorithm                   │
│   - LateNightAlgorithm                  │
│                                         │
│   perform: algorithm.spin() -> {        │
│     id, label, multiplier, color,       │
│     probability                         │
│   }                                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Database                              │
│   - SpinAlgorithmConfiguration (stores  │
│     which algorithm is active)          │
│   - GameWallet (user balance)           │
│   - GameTransaction (tracks each spin)  │
└─────────────────────────────────────────┘
```

## Algorithm Switching Examples

### Example 1: Switch to Conservative (Late Night)
```bash
# In Django admin, click "Spin Algorithm Configurations"
# Find "Conservative - Default"
# Check the "is_active" checkbox
# Click Save
# 
# OR via API:
curl -X POST http://localhost:8000/api/casino/algorithms/2/activate/ \
  -H "Authorization: Token ADMIN_TOKEN"
```

### Example 2: Create Custom Configuration
1. Go to admin
2. Click "Add Spin Algorithm Configuration"
3. Fill in:
   - Name: "Promotional Event"
   - Algorithm key: "generous"
   - Description: "Used during weekend promotions"
4. Save
5. When ready, activate it

### Example 3: Time-Based Switching
1. Create configuration "Peak Hours"
2. Set algorithm_key to "peak_hour"
3. Set start_time: 09:00, end_time: 17:00
4. Set days_of_week: 0,1,2,3,4 (Monday-Friday)
5. (Optional: Set up Celery task to auto-activate)

## Frontend Integration

**Option A: Minimal Change** (Keep frontend random)
- Frontend generates random result
- Frontend sends to backend for recording
- Uses existing `/api/casino/wallet/record_spin/` endpoint

**Option B: Full Backend Control** (Recommended)
- Frontend only shows animation
- Backend determines result via `/api/casino/wallet/spin/`
- More secure, better control

Update frontend in `wildwash/app/casino/spin/page.tsx`:

```typescript
// Old way (client-side random)
const handleSpin = () => {
  const randomIndex = Math.floor(Math.random() * WHEEL_SEGMENTS.length);
  const result = WHEEL_SEGMENTS[randomIndex];
  // ... rest of logic
};

// New way (server-side algorithm)
const handleSpin = async () => {
  const response = await axios.post(
    `${apiBase}/casino/wallet/spin/`,
    { spin_cost: SPIN_COST },
    { headers: { 'Authorization': `Token ${token}` } }
  );
  const { result } = response.data;
  // Use result from server
};
```

## File Structure

```
wild-wash-api/casino/
├── algorithms.py                    ✅ NEW
├── models.py                        ✅ UPDATED (added SpinAlgorithmConfiguration)
├── serializers.py                   ✅ UPDATED (added SpinAlgorithmConfigurationSerializer)
├── views.py                         ✅ UPDATED (added SpinAlgorithmViewSet, new spin endpoint)
├── urls.py                          ✅ UPDATED (registered new viewset)
├── admin.py                         ✅ UPDATED (added admin for SpinAlgorithmConfiguration)
├── management/                      ✅ NEW
│   ├── __init__.py                  ✅ NEW
│   └── commands/                    ✅ NEW
│       ├── __init__.py              ✅ NEW
│       └── init_algorithms.py        ✅ NEW
└── migrations/
    └── XXXX_add_spinalgoconfiguration.py  ✅ AUTO-GENERATED
```

## Key Concepts

### Algorithm Registry
```python
ALGORITHM_REGISTRY = {
    'balanced': BalancedAlgorithm,
    'conservative': LowProbabilityAlgorithm,
    'generous': GenerousAlgorithm,
    'peak_hour': PeakHourAlgorithm,
    'late_night': LateNightAlgorithm,
}
```

### Getting Algorithm
```python
from casino.algorithms import get_algorithm

# Get by key
algorithm = get_algorithm('balanced')
result = algorithm.spin()

# Result structure
{
    'id': 1,
    'label': '2x',
    'multiplier': 2,
    'color': '#D97706',
    'probability': 0.125
}
```

### Active Algorithm
```python
# Get active
active = SpinAlgorithmConfiguration.objects.filter(is_active=True).first()
algorithm = get_algorithm(active.algorithm_key)

# Activate new one (automatically deactivates others)
config = SpinAlgorithmConfiguration.objects.get(pk=2)
config.is_active = True
config.save()  # Other active configs are auto-deactivated
```

## What's Next

### For You (Admin)
- [ ] Review algorithms in admin
- [ ] Test switching between algorithms
- [ ] Create custom time-based configurations
- [ ] Update frontend to use new spin endpoint

### For Users
- Transparent algorithm system (can see which algorithm is active)
- Better fairness through configurable probabilities
- No changes needed in frontend (backward compatible)

## Troubleshooting

### Error: "No spin algorithm is currently configured"
**Solution**: Run `python manage.py init_algorithms`

### Migration fails
**Solution**: 
```bash
python manage.py makemigrations casino --empty casino --name create_spin_algorithm
```

### Algorithm not switching
- Check database: `SpinAlgorithmConfiguration` table exists
- Verify `is_active` field is boolean
- Check admin shows only one active

## Support

For issues or questions:
1. Check `ALGORITHM_SYSTEM.md` for detailed documentation
2. Review algorithm examples in `casino/algorithms.py`
3. Check API responses format
4. Verify migration was applied: `python manage.py showmigrations casino`

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-12-25
