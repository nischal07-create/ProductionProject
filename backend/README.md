# TrailMate Backend

## Run locally

```powershell
cd C:\Users\ASUS\trailmate\backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000 --noreload
```

## UI

Open:

- `http://127.0.0.1:8000/` - TrailMate Dashboard UI
- `http://127.0.0.1:8000/api/health/` - health check

## Auth + APIs

- `POST /api/auth/token/` - get JWT access token
- `GET /api/trips/destinations/` - public destinations list
- `GET /api/trips/activities/` - public activities list
- `GET/POST /api/trips/plans/` - authenticated trip plans
- `GET/PATCH/DELETE /api/trips/plans/<id>/` - authenticated plan detail
- `GET/POST /api/trips/plans/<plan_id>/items/` - authenticated plan activities
- `GET/DELETE /api/trips/plans/<plan_id>/items/<item_id>/` - authenticated single plan item
- `POST /api/trips/guide/kathmandu/` - AI-style Kathmandu guide (best places, famous foods, Google Maps links)
