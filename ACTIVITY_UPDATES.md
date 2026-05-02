# TrailMate Activity & Trekking Route Updates

## Summary of Changes

All activities and trekking routes have been updated with exact pricing and comprehensive photo galleries. This document details all modifications made to the system.

---

## 1. Activity Model Enhancement

### Database Changes
- **New Field**: `photo_urls` (JSONField)
- **Migration**: `trips/0004_activity_photo_urls` (already applied)
- **Purpose**: Store multiple photo URLs for each activity to support activity galleries

### Activity Serializer Update
The `ActivitySerializer` now includes the `photo_urls` field in API responses:
```python
"photo_urls": [
    "/static/core/photos/places/pokhara/hot-air-balloon-1.jpg",
    "/static/core/photos/places/pokhara/hot-air-balloon-2.jpg",
    ...
]
```

---

## 2. Kathmandu Activities - Updated Pricing & Photos

All Kathmandu activities now have exact USD pricing and 2-3 photos each:

| Activity | Price (USD) | Duration | Photos |
|----------|-----------|----------|--------|
| Heritage Walking & Responsible Cultural Workshop | $25.00 | 3 hours | 3 |
| City Mountain Biking (Nagarjun Trails) | $45.00 | 4 hours | 3 |
| Rooftop Yoga & Sunrise Session | $18.00 | 1 hour | 2 |
| Thamel Bike Rental & Self-Guided City Loop | $12.00 | 6 hours | 2 |
| Guided Rock Climbing Intro (Local Crags) | $65.00 | 4 hours | 3 |
| Culinary Street Food Responsible Tour | $30.00 | 2.5 hours | 3 |
| Chandragiri Cable Car + Short Hike | $35.00 | 3 hours | 2 |
| Photography & Conservation Walk | $22.00 | 2.5 hours | 2 |
| Evening Cultural Dance Show & Workshop | $28.00 | 2 hours | 2 |
| Responsible Volunteer Half-Day Experience | $0.00 (Free) | 4 hours | 2 |

---

## 3. Pokhara Activities - Updated Pricing & Photos

All Pokhara activities now have exact USD pricing and adventure-specific photos:

| Activity | Price (USD) | Duration | Photos | Notes |
|----------|-----------|----------|--------|-------|
| Tandem Paragliding from Sarangkot | $125.00 | 1 hour | 3 | World-famous sport |
| **Seasonal Hot Air Balloon** | **$280.00** | **1 hour** | **5** | **5 photos including balloon views** |
| Kusma (Khimti) Bungee & Canyon Swing | $180.00 | 1.5 hours | 3 | |
| Seti/Trishuli Day White-Water Rafting | $95.00 | 6 hours | 3 | |
| Zipline & Canopy Adventure | $68.00 | 2 hours | 2 | |
| Seasonal Skydiving Festival (Tandem) | $450.00 | 1 hour | 3 | Premium extreme sport |
| Motorbike Rental & Off-Road Annapurna Foothills Tour | $55.00 | 6 hours | 2 | |
| Lake Boat Rental & Sunset Cruise | $25.00 | 1.5 hours | 2 | |
| Mountain Biking Trails Around Begnas & Phewa | $60.00 | 5 hours | 2 | |
| Caving & Gupteshwor Exploration | $20.00 | 1 hour | 2 | |

### Hot Air Balloon - Premium Activity
The hot air balloon activity now features **5 dedicated photos** for a complete visual experience:
- `hot-air-balloon-1.jpg` - Balloon preparation
- `hot-air-balloon-2.jpg` - Pre-flight views
- `hot-air-balloon-3.jpg` - Aerial landscape views
- `hot-air-balloon-4.jpg` - Mountain panorama from altitude
- `hot-air-balloon-5.jpg` - Sunrise/sunset views

---

## 4. Trekking Routes - Pricing Added

All 8 trekking routes now include exact pricing in both USD and NPR:

| Trek Name | Duration | Difficulty | Price (USD) | Price (NPR) |
|-----------|----------|-----------|------------|-------------|
| Poon Hill Trek | 3 days | Easy | $599 | ₨78,870 |
| Annapurna Base Camp Trek | 7 days | Moderate | $1,199 | ₨157,740 |
| Langtang Valley Trek | 5 days | Moderate | $899 | ₨118,410 |
| Everest Base Camp Trek | 14 days | Hard | $1,599 | ₨210,570 |
| Manaslu Circuit Trek | 12 days | Hard | $1,299 | ₨170,910 |
| Mardi Himal Trek | 5 days | Moderate | $799 | ₨105,270 |
| Upper Mustang Trek | 10 days | Hard | $1,399 | ₨184,140 |
| Gokyo Lakes Trek | 11 days | Hard | $1,699 | ₨223,770 |

**Pricing Fields Added**:
- `price_usd`: Price in US dollars
- `price_npr`: Price in Nepalese Rupees (at ~131.5 NPR per USD)

---

## 5. Frontend Integration

### API Endpoint Response Example

GET `/api/trips/activities/`

```json
{
  "id": 1,
  "destination": 2,
  "name": "Seasonal Hot Air Balloon (Lake & Mountain Views)",
  "description": "Occasional hot-air balloon operations over the Pokhara valley in clear-season windows; book early and follow safety briefings.",
  "tags": "hotairballoon,seasonal,scenic,photography",
  "cost_estimate": "280.00",
  "duration_hours": "1.0",
  "indoor": false,
  "family_friendly": true,
  "photo_urls": [
    "/static/core/photos/places/pokhara/hot-air-balloon-1.jpg",
    "/static/core/photos/places/pokhara/hot-air-balloon-2.jpg",
    "/static/core/photos/places/pokhara/hot-air-balloon-3.jpg",
    "/static/core/photos/places/pokhara/hot-air-balloon-4.jpg",
    "/static/core/photos/places/pokhara/hot-air-balloon-5.jpg"
  ]
}
```

### Activity Card Display Recommendation

For frontend components displaying activities:

```javascript
// Example: Display activity with photo gallery
const activity = {
  name: "Seasonal Hot Air Balloon",
  cost_estimate: 280.00,
  photo_urls: [...] // Array of photo URLs
};

// Show primary photo
const primaryPhoto = activity.photo_urls[0];

// On click, show gallery with all photos
const gallery = activity.photo_urls;
```

---

## 6. Trekking Route API Response Example

GET `/api/trips/trekking/routes/poon_hill/`

The trekking catalog now includes:

```json
{
  "id": "poon_hill",
  "name": "Poon Hill Trek",
  "price_usd": 599,
  "price_npr": 78870,
  "difficulty": "Easy",
  "duration_days": 3,
  "max_altitude": "3,210m",
  ...
}
```

---

## 7. File Structure

### Activity Photos Location
```
backend/core/static/core/photos/places/
├── kathmandu/
│   ├── heritage-tour-1.jpg
│   ├── heritage-tour-2.jpg
│   ├── mountain-biking-1.jpg
│   └── ... (more activity photos)
└── pokhara/
    ├── hot-air-balloon-1.jpg (5 photos for balloon activity)
    ├── hot-air-balloon-2.jpg
    ├── hot-air-balloon-3.jpg
    ├── hot-air-balloon-4.jpg
    ├── hot-air-balloon-5.jpg
    ├── paragliding-1.jpg
    └── ... (more activity photos)
```

### Modified Code Files
1. **`trips/models.py`** - Added `photo_urls` JSONField to Activity model
2. **`trips/views.py`** - Updated ActivitySerializer to include `photo_urls`
3. **`trips/trekking_catalog.py`** - Added `price_usd` and `price_npr` to all 8 trekking routes
4. **`scripts/add_activities.py`** - Updated with exact pricing and photo URL arrays for all 20 activities
5. **`trips/migrations/0004_activity_photo_urls.py`** - Database migration (auto-generated)

---

## 8. Database Migration History

```bash
# Apply migration (already done)
python manage.py migrate

# Migration details:
# - Added JSONField column: photo_urls (default: [])
# - All existing activities maintain backward compatibility
# - New activities include photo arrays
```

---

## 9. Implementation Notes

### Photo URL Storage
- Photos are stored as **static file paths** in the JSONField
- Example: `/static/core/photos/places/pokhara/hot-air-balloon-1.jpg`
- Photos should be uploaded to the appropriate folder in `backend/core/static/core/photos/`

### Pricing Convention
- **USD prices** are used for international tourists
- **NPR prices** are calculated at approximately 131.5 NPR per 1 USD
- Prices reflect estimated costs for group tours with English-speaking guides
- Actual prices may vary by season and tour operator

### Activity Gallery Implementation
When displaying activities:
1. Show the **first photo** (`photo_urls[0]`) as the main activity card image
2. **On click**, display a gallery modal with all `photo_urls`
3. Allow users to **navigate through photos** using arrows or swipe gestures
4. Show the **activity price** prominently below the title

---

## 10. Testing & Validation

### API Test Commands

```bash
# Test activities endpoint
curl http://127.0.0.1:8001/api/trips/activities/

# Test specific destination activities
curl http://127.0.0.1:8001/api/trips/activities/?destination=2  # Pokhara

# Test trekking routes with pricing
curl http://127.0.0.1:8001/api/trips/trekking/routes/
```

### Database Verification

```bash
# In Django shell
python manage.py shell

from trips.models import Activity
# Check hot air balloon activity
ballon = Activity.objects.get(name__contains='Hot Air Balloon')
print(ballon.cost_estimate)  # Should show 280.00
print(len(ballon.photo_urls))  # Should show 5
```

---

## 11. Next Steps

### To Use These Updates in Frontend:

1. **Update Activity Display Components**
   - Modify activity card components to show `photo_urls` array
   - Implement photo gallery on click

2. **Add Pricing Display**
   - Display `cost_estimate` for activities
   - For trekking routes, display `price_usd` or `price_npr` based on user preference

3. **Create Activity Gallery Modal**
   - Show full-size photos from `photo_urls`
   - Add navigation between photos

4. **Add Photo Placeholders**
   - If a photo URL returns 404, show a fallback placeholder
   - Consider using error handlers: `onerror="this.onerror=null;this.src='/static/core/photos/default.svg';"`

---

## 12. Summary of Changes

✅ **Database**: Added `photo_urls` JSONField to Activity model
✅ **Activities**: Updated all 20 activities with exact pricing ($0-$450)
✅ **Photos**: Added 2-5 photos per activity (50 total photo references)
✅ **Trekking Routes**: Added pricing in both USD and NPR to all 8 routes
✅ **API**: Updated serializers to include photo URLs in responses
✅ **Migration**: Created and applied migration 0004
✅ **Hot Air Balloon**: 5 dedicated photos for premium activity

---

**Last Updated**: May 2, 2026
**Status**: Ready for Frontend Integration
