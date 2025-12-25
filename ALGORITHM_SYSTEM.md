# Spin Algorithm System Documentation

## Overview

The spin algorithm system allows you to manage different probability distributions for the wheel game at different times or for different purposes. You can:

- ✅ Switch between 5 pre-built algorithms
- ✅ Manage algorithms from Django admin
- ✅ Control algorithms via REST API
- ✅ Set up time-based or manual switching
- ✅ Track which algorithm is being used for each spin

## Available Algorithms

### 1. **Balanced** (balanced)
- **Description**: Equal probability distribution - good for peak hours
- **Use Case**: When you want consistent, fair gameplay
- **Probabilities**: All 8 segments have 12.5% chance

### 2. **Conservative** (conservative)
- **Description**: Lower probability for big wins - suitable for low-traffic hours
- **Use Case**: Late night or when you want lower payout rates
- **Focus**: More frequent small losses (0.5x) and medium wins (1.5x, 2x)

### 3. **Generous** (generous)
- **Description**: Higher win probability - good for promotions and weekends
- **Use Case**: Promotional periods, competitions, or weekend boosts
- **Focus**: More frequent wins across all tiers

### 4. **Peak Hour** (peak_hour)
- **Description**: Optimized for high-traffic periods with frequent small wins
- **Use Case**: When server is busy, keep players engaged with frequent wins
- **Focus**: 20% chance for 2x, 22% chance for 1.5x

### 5. **Late Night** (late_night)
- **Description**: Conservative late-night algorithm for sustained engagement
- **Use Case**: Encourage longer sessions with fewer big wins
- **Focus**: Higher loss rate (30%), but occasional wins

## Setup Instructions

### 1. Create Migration

```bash
cd wild-wash-api
python manage.py makemigrations casino
python manage.py migrate
```

### 2. Initialize Default Algorithms

```bash
python manage.py init_algorithms
```

This will create default configurations for all 5 algorithms and activate the first one.

### 3. Verify Setup

Check the admin panel:
```
http://your-server/admin/casino/spinalgorithmconfiguration/
```

## Using the API

### Get Available Algorithms

```bash
GET /api/casino/algorithms/available/
```

Response:
```json
{
  "algorithms": [
    {
      "key": "balanced",
      "name": "Balanced",
      "description": "Equal probability distribution - good for peak hours"
    },
    // ... more algorithms
  ],
  "count": 5
}
```

### Get Active Algorithm

```bash
GET /api/casino/algorithms/active/
```

Response:
```json
{
  "active": {
    "id": 1,
    "name": "Balanced - Default",
    "algorithm_key": "balanced",
    "is_active": true,
    "algorithm_info": {
      "key": "balanced",
      "name": "Balanced",
      "description": "...",
      "segments": [...]
    }
  }
}
```

### Switch Active Algorithm (Admin Only)

```bash
POST /api/casino/algorithms/{id}/activate/
Authorization: Token YOUR_ADMIN_TOKEN
```

Response:
```json
{
  "message": "Algorithm \"Balanced - Default\" is now active",
  "algorithm": { ... }
}
```

### Get All Configurations

```bash
GET /api/casino/algorithms/all_configurations/
Authorization: Token YOUR_ADMIN_TOKEN
```

### Perform a Spin (Uses Active Algorithm)

```bash
POST /api/casino/wallet/spin/
Authorization: Token YOUR_USER_TOKEN
Content-Type: application/json

{
  "spin_cost": 20
}
```

Response:
```json
{
  "result": {
    "id": 1,
    "label": "2x",
    "multiplier": 2,
    "color": "#D97706",
    "probability": 0.125
  },
  "spin_cost": 20,
  "winnings": 40,
  "net_result": 20,
  "balance": 1020,
  "algorithm_used": "Balanced - Default",
  "message": "Spin result: 2x. Net: +20 KES"
}
```

## Admin Interface

### Managing Algorithms

In Django Admin (`/admin/casino/spinalgorithmconfiguration/`):

1. **View Configurations**: See all algorithm configurations
2. **Create New**: Add custom algorithm configurations
3. **Activate**: Click on a configuration and set `is_active = True`
4. **Schedule** (Optional): Set `start_time` and `end_time` for automatic scheduling
5. **Filter by Days**: Set `days_of_week` (0=Monday, 6=Sunday)

### Configuration Fields

- **name**: Human-readable name for this configuration
- **algorithm_key**: Which algorithm to use (dropdown from available algorithms)
- **is_active**: Only one can be active at a time
- **start_time**: Optional time to auto-activate (HH:MM format)
- **end_time**: Optional time to auto-deactivate (HH:MM format)
- **days_of_week**: Comma-separated day numbers (0,1,2,3,4,5,6)
- **description**: Notes about when/why to use this configuration

## Creating Custom Algorithms

To create a custom algorithm, edit `casino/algorithms.py`:

```python
class MyCustomAlgorithm(BaseAlgorithm):
    """My custom algorithm description."""
    
    name = "My Custom"
    description = "Description of when to use this"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.20},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.30},
            # ... rest of segments
        ]
    
    def spin(self) -> Dict:
        """Perform spin using custom logic."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()
```

Then register it in `ALGORITHM_REGISTRY`:

```python
ALGORITHM_REGISTRY = {
    # ... existing algorithms
    'my_custom': MyCustomAlgorithm,
}
```

## Frontend Integration

In your React component (`wildwash/app/casino/spin/page.tsx`), update the spin call:

```typescript
// Instead of using the frontend algorithm, call the backend endpoint
const handleSpin = async () => {
    if (!canSpin) return;
    setIsSpinning(true);
    
    try {
        const response = await axios.post(
            `${apiBase}/casino/wallet/spin/`,
            { spin_cost: spinCost },
            {
                headers: {
                    'Authorization': `Token ${token}`
                }
            }
        );
        
        const { result, winnings, balance, algorithm_used } = response.data;
        
        // Use result.multiplier and result.label
        // Animate the wheel to the correct position
        // Update wallet balance
        // Log which algorithm was used
        
    } catch (error) {
        // Handle error
    } finally {
        setIsSpinning(false);
    }
};
```

## Switching Between Frontend and Backend Algorithms

### Current State (Frontend)
- All probability logic is on the client
- Can be manipulated if user inspects network

### New State (Backend)
- All probability logic on the server
- Client only displays the result
- More secure and controllable

To migrate:
1. Keep old endpoint working for backwards compatibility
2. Add new `/api/casino/wallet/spin/` endpoint (already done ✓)
3. Gradually update frontend to use new endpoint
4. Deprecate old endpoint after transition

## Monitoring & Analytics

Track which algorithm is being used:
```bash
# Check transactions to see which algorithm was used
SELECT * FROM casino_gametransaction 
WHERE notes LIKE '%algorithm%' 
ORDER BY created_at DESC;
```

## Examples

### Time-Based Algorithm Switching

1. Create configurations:
   - "Peak Hours" (9 AM - 5 PM): Generous algorithm
   - "Off Hours" (5 PM - 9 AM): Conservative algorithm

2. In admin, set:
   - "Peak Hours": start_time=09:00, end_time=17:00
   - "Off Hours": start_time=17:00, end_time=09:00

3. Use a scheduled task (Celery) to activate algorithms automatically

### A/B Testing

1. Create two configurations:
   - "Test A": Balanced algorithm
   - "Test B": Conservative algorithm

2. Use API to switch based on user segment or time
3. Track results in analytics

## Troubleshooting

### No algorithm is active
```
Error: "No spin algorithm is currently configured"
```

**Solution**:
```bash
python manage.py init_algorithms
```

### Algorithm not using correct segments
- Check `algorithm_key` matches a registered algorithm
- Verify probabilities sum to ~1.0
- Check algorithm code in `casino/algorithms.py`

### Migration errors
```bash
# Reset migrations (development only!)
python manage.py migrate casino zero
python manage.py makemigrations casino
python manage.py migrate
```

## Performance Notes

- Algorithm selection is cached in memory
- Each spin performs a single random() call
- No database queries per spin (only to update wallet)
- Probabilities are pre-calculated, no dynamic computation

## Future Enhancements

- [ ] Time-based algorithm switching (Celery task)
- [ ] User-specific algorithms (VIP players get better odds)
- [ ] A/B testing framework
- [ ] Detailed analytics dashboard
- [ ] Machine learning-based algorithm optimization
- [ ] Seasonal algorithm variations
