# Qrib

## Phone OTP Auth

The API authenticates users by phone number and OTP, then issues SimpleJWT
tokens.

Endpoints:

- `POST /auth/request-otp/` with `{"phone_number": "+212600000000"}`
- `POST /auth/verify-otp/` with `{"phone_number": "+212600000000", "code": "123456"}`
- `GET /auth/me/` with `Authorization: Bearer <access_token>`
- `POST /auth/token/refresh/` with `{"refresh": "<refresh_token>"}`

`/auth/verify-otp/` returns `access`, `refresh`, and a `user` object containing
`phone_number`, `full_name`, and `profile_completed`. The client can use
`profile_completed` to decide whether to start a later profile completion flow.

OTP codes are stored as hashes with an expiry. In local development,
`QRIB_RETURN_OTP_IN_RESPONSE=true` returns the generated OTP in the response
until SMS or WhatsApp delivery is implemented.

## Worker Profile

After OTP login, the frontend can save worker onboarding progress as a draft and
complete it only when required fields are valid.

Endpoints:

- `GET /profiles/me/`
- `PATCH /profiles/worker-draft/`
- `POST /profiles/worker-complete/`

Required fields for completion:

- `full_name`
- `location_permission_granted`
- `location_lat`
- `location_lng`
- `location_city`
- `skills_description`

Draft update example:

```json
{
  "full_name": "Hamza Ait",
  "location_permission_granted": true,
  "location_lat": "33.573100",
  "location_lng": "-7.589800",
  "location_city": "Casablanca",
  "skills_description": "I repair water leaks and install bathroom fixtures.",
  "evidence_notes": "Photos can be added later."
}
```

`POST /profiles/worker-complete/` validates the draft, copies `full_name` to the
user, sets `profile_completed=true`, and returns `redirect_to`.

## Backend AI Agent

The backend agent uses OpenAI to decide the next conversational step, then
Django safely applies only validated side effects.

Endpoints:

- `GET /agent/state/`
- `POST /agent/start/`
- `POST /agent/message/`

After OTP login, call `POST /agent/start/` to let the agent ask the first
question without sending fake user text.

Example:

```json
{
  "message": "I am a worker. My name is Hamza Ait.",
  "input_type": "text"
}
```

Location permission is handled by Expo. When the agent asks for location, the
response can include:

```json
{
  "frontend_actions": [
    {
      "type": "request_location_permission",
      "reason": "Location is required for worker area."
    }
  ]
}
```

After Expo gets location, send it back as an event:

```json
{
  "message": "location allowed",
  "events": [
    {
      "type": "location_granted",
      "payload": {
        "lat": "33.573100",
        "lng": "-7.589800",
        "city": "Casablanca"
      }
    }
  ]
}
```

The model can propose `ready_to_complete=true`, but the backend still validates
all required fields before saving and returning `redirect_to`.

## Environment

Copy the example file and change the secret values:

```bash
cp .env.example .env
```

The Django settings read secrets and runtime values from environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `OPENAI_API_KEY`
- `QRIB_AGENT_MODEL`
- `QRIB_OTP_CODE_LENGTH`
- `QRIB_OTP_TTL_MINUTES`
- `QRIB_RETURN_OTP_IN_RESPONSE`
- `QRIB_REQUEST_OTP_RATE`
- `QRIB_VERIFY_OTP_RATE`

## Docker

```bash
docker compose up --build
docker compose exec web python manage.py migrate
```

Docker runs PostgreSQL in the `db` service and stores data in the
`postgres_data` named volume.

Useful commands:

```bash
docker compose ps
docker compose logs db
docker compose exec web python manage.py check
docker compose exec web python manage.py test auth profiles ai_agent
```

Local `.env` files contain secrets and must not be committed. `.env.example`
is safe to commit because it contains placeholders only.

## Local Database Note

The project uses PostgreSQL through Docker. Old local SQLite files such as
`qrib/db.sqlite3` are no longer used by Django.

If you need to reset local Docker database data during development:

```bash
docker compose down -v
docker compose up --build
docker compose exec web python manage.py migrate
```
