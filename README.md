## AI Code Reviewer

An intelligent FastAPI service that performs automated code reviews on GitHub pull requests using OpenAI. When a pull request is opened, synchronized, or reopened, the service analyzes the diff, generates targeted suggestions, and publishes review comments with GitHub Suggestions so they can be applied with one click. Basic review analytics are tracked to a local JSON file for a simple dashboard.

## Features

- **AI-powered analysis**: Focused review of changed lines using OpenAI, tuned to return actionable suggestions.
- **GitHub App integration**: Receives webhooks, authenticates per-installation, and posts review comments.
- **Actionable suggestions**: Uses GitHub Suggestions blocks that developers can apply directly.
- **Health and readiness**: `/health` and `/health/ready` endpoints.
- **Simple analytics**: Aggregates review stats in `backend/analytics_data.json` and exposes `/api/analytics/dashboard`.

## Prerequisites

- **Python**: 3.10+ recommended
- **GitHub App**: with Pull requests (Read & write) and Contents (Read) permissions
- **OpenAI API key**

## Quick start (Windows)

1. Clone the repository.
2. Run: `./scripts/setup.bat`
3. Create `backend/.env` (see Configuration below).
4. Place your GitHub App private key `.pem` file where the service can read it (see Configuration).
5. Start the API: `./scripts/run-backend.bat`
6. Start ngrok in another terminal: `ngrok http 8000`
7. Open `http://localhost:8000/docs` for interactive API docs.

## Quick start (macOS/Linux)

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   - `python -m venv backend/venv`
   - `source backend/venv/bin/activate`
   - `pip install -r backend/requirements.txt`
3. Create `backend/.env` (see Configuration).
4. Place your GitHub App private key `.pem` file where the service can read it (see Configuration).
5. Run the API:
   - From the `backend` directory: `uvicorn app.main:app --reload --port 8000`
6. Start ngrok in another terminal: `ngrok http 8000`
7. Open `http://localhost:8000/docs`.

## Configuration

Create a `backend/.env` file with the following values:

```env
GITHUB_APP_ID=<your_github_app_id>
GITHUB_WEBHOOK_SECRET=<your_webhook_secret>
OPENAI_API_KEY=<your_openai_api_key>
# Optional: path to your GitHub App private key file (relative or absolute)
GITHUB_PRIVATE_KEY_PATH=mycodereviewbot.2025-07-01.private-key.pem
```

Private key file placement options:

- Put the `.pem` file in the `backend/` directory and keep the default `GITHUB_PRIVATE_KEY_PATH`, or
- Set `GITHUB_PRIVATE_KEY_PATH` to the absolute path of your `.pem` file.

Readiness checks look for the private key file and required environment variables at `/health/ready`.

## GitHub App setup

1. Create a new GitHub App (on your account or organization).
2. Set Webhook URL to your server: `https://<your-host>/api/webhooks/github`.
   - For local development, use a tunneling tool (e.g., ngrok) and point the Webhook URL to `https://<ngrok-id>.ngrok.io/api/webhooks/github`.
3. Configure permissions:
   - Pull requests: Read & write
   - Contents: Read
   - Metadata: Read-only
4. Subscribe to events:
   - `pull_request`
5. Generate and download the private key (`.pem`) and configure `GITHUB_PRIVATE_KEY_PATH`.
6. Install the App on the target repositories.

## How it works

- The webhook endpoint `POST /api/webhooks/github` receives GitHub events.
- For `pull_request` events with actions `opened`, `synchronize`, or `reopened`, the service:
  - Obtains an installation token via the GitHub App.
  - Lists changed files in the PR.
  - For supported file types (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`), it analyzes the diff using OpenAI (`app/core/ai_analyzer.py`).
  - Builds GitHub review comments with suggestion blocks and submits them in batches.
  - Records review metrics to `backend/analytics_data.json` (exposed via `/api/analytics/dashboard`).

Signature verification for webhooks is implemented but currently commented out in `app/api/webhooks.py`. You can enable it by uncommenting the verification lines and ensuring `GITHUB_WEBHOOK_SECRET` is set.

## API endpoints

- `GET /` — basic landing info with links.
- `GET /docs` — interactive Swagger UI.
- `GET /health/` — health status.
- `GET /health/ready` — readiness check for env vars and private key file.
- `POST /api/webhooks/github` — GitHub webhook receiver.
- `POST /api/webhooks/github/test` — debug endpoint to echo headers/body.
- `GET /api/analytics/dashboard` — simple review stats.

### Example: test webhook locally

```bash
curl -X POST "http://localhost:8000/api/webhooks/github/test" \
  -H "Content-Type: application/json" \
  -d '{"hello": "world"}'
```

## Development notes

- Dependencies are listed in `backend/requirements.txt`.
- The development scripts (`scripts/setup.bat`, `scripts/run-backend.bat`) assume Windows and run the API on port 8000.
- Analytics are persisted to `backend/analytics_data.json` when the server runs from the `backend/` directory (as in the provided scripts).

## License

This project is released under the MIT License. See `LICENSE` for details.


