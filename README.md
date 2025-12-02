# Slack Agent Chatbot

A Slack Bolt bot that responds to `@agent` or `@gpt` prompts by forwarding the message to your custom agent API or the OpenAI Chat Completions endpoint.

## Features
- Mention-driven routing: `@agent` forwards to your agent, `@gpt` to OpenAI, anything else uses the configured default.
- Works in DMs, channels, and threads (bot replies in thread when available).
- Automatically gathers recent thread history and passes it as context to keep answers aligned with the ongoing conversation.
- Performs a warm-up call to the default responder at startup to keep downstream services responsive.
- Announces when it wakes from idle periods (configurable timer) so users know fresh context is loading.
- Optional socket mode support for environments where inbound HTTP isn’t possible.
- Structured logging and ready-to-use health check (HTTP mode).

## Prerequisites
- Python 3.10+
- Slack app with Bot token, Signing secret, and (for socket mode) App-level token.
- Agent API endpoint (POST) that accepts `{ query: string }`.
- OpenAI API key (if you plan to use `@gpt`).

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the environment variables described above. The Python service consumes the same configuration values.

### Running the Service
```bash
python -m python_app.main
```

- **HTTP mode** (default): runs a Flask server on the configured `PORT`/`HOST`, serves the Slack Events endpoint at `SLACK_EVENTS_PATH`, and adds a `/health` probe.
- **Socket mode**: set `SLACK_SOCKET_MODE=true` and provide `SLACK_APP_TOKEN` to run without exposing an HTTP endpoint.

## Usage
- Mention `@agent` followed by your request to call the custom agent service.
- Mention `@gpt` to request an OpenAI-generated answer.
- Mention the bot without either keyword to use the default responder (`DEFAULT_RESPONDER`).
- The first mention after bot startup may be slightly faster because the default responder is pre-warmed.
- If the bot has been idle longer than `IDLE_SLEEP_MINUTES`, it posts a quick “I’m back!” message with the idle duration before the real answer.

Replies are posted back to the originating thread or conversation, and the last few thread messages are sent to the responder as context automatically.

## Testing
1. Install dependencies and activate your virtual environment.
2. Load environment variables (`export $(grep -v '^#' python_app/.env | xargs)` or use a dotenv loader).
3. Run `python -m pytest` to execute the Python test suite (no tests ship by default, but the command ensures dependencies are wired correctly).
4. Start the bot locally with `python -m python_app.main`.
5. In Slack, mention the bot in a channel/thread:
   - Verify access control (admin vs. blocked users).
   - Send multiple thread messages and confirm replies include recent context.
   - Wait longer than `IDLE_SLEEP_MINUTES` and ensure the “I’m back!” notice appears before the real reply.

## Deployment
1. Provision a Python 3.10+ environment with all required env vars (`.env` or secrets manager).
2. Install requirements (`pip install -r requirements.txt`).
3. Decide on transport:
   - **HTTP**: expose the Flask server on your chosen host/port behind HTTPS (e.g., Gunicorn + reverse proxy). Ensure Slack can reach `HOST:PORT/SLACK_EVENTS_PATH`.
   - **Socket mode**: set `SLACK_SOCKET_MODE=true` and run `python -m python_app.main`; Slack handles the connection via `SLACK_APP_TOKEN`.
4. Configure a process manager (systemd, supervisord, PM2, Docker, etc.) to keep the bot running and restart on failure.
5. Monitor logs (`LOG_LEVEL`) and optionally wire health checks via `/health`.

## Project Structure
```
python_app/
├── __init__.py
├── access_control.py
├── agent_client.py
├── app/
│   ├── __init__.py
│   └── clients/
│       ├── __init__.py
│       └── chatgpt_client.py
├── bot.py
├── config.py
├── logger.py
├── main.py
└── utils/
    ├── __init__.py (implicit)
    └── jwt_validator.py
```

## Access Control
Configure role-based access via env vars (Slack user IDs):
- `SLACK_ADMIN_USERS` – comma-separated list of user IDs with full access.
- `SLACK_ALLOWED_USERS` – IDs explicitly allowed.
- `SLACK_BLOCKED_USERS` – IDs explicitly denied.
- `SLACK_DEFAULT_ALLOW` – `true`/`false` to permit others by default (default: true).
- `IDLE_SLEEP_MINUTES` – minutes of inactivity before the bot announces it was sleeping (default: 10).

## OpenAI (Responses API with optional browsing)
- Set `OPENAI_API_URL` (`https://api.openai.com/v1/responses` for Responses API).
- Set `OPENAI_MODEL` to a supported model (e.g., `gpt-4.1` or `gpt-4.1-mini`).
- Toggle web browsing with `OPENAI_BROWSER_ENABLED=true` to allow live information when using the Responses API.

## Troubleshooting
- **Bot not responding**: confirm the Slack app is installed in the workspace and has `app_mentions:read` and channel history scopes; check logs for errors.
- **Signature errors**: verify `SLACK_SIGNING_SECRET`.
- **Agent/OpenAI failures**: check logs and API credentials.
- **Socket mode issues**: ensure `SLACK_APP_TOKEN` is an app-level token with `connections:write`.

Happy building!
