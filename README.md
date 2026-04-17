# Buchi Backend (FastAPI + MongoDB)

## Run locally (Docker)
1. Copy env:
   - `cp .env.example .env`
   - Fill `DOG_API_KEY` to enable external dog search via TheDogAPI (optional; local DB search still works).
2. Start:
   - `docker compose up --build`

API runs on `http://localhost:8000`.

## External search note
`GET /get_pets` keeps the original PDF response shape, but the external provider is TheDogAPI because the Petfinder endpoint was reported inactive by the assessment team. External enrichment is currently dog-only.

## Production server
The container entrypoint uses Gunicorn with Uvicorn workers.
