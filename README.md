# Slack Agent Chatbot

A Slack Bolt bot that responds to `@agent` or `@gpt` prompts by forwarding the message to your custom agent API or the OpenAI Chat Completions endpoint.

## Features
- Mention-driven routing: `@agent` forwards to your agent, `@gpt` to OpenAI, anything else uses the configured default.
- Works in DMs, channels, and threads (bot replies in thread when available).
- Automatically gathers recent thread history and passes it as context to the responder so replies stay in-sync with the conversation.
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

Replies are posted back to the originating thread or conversation.

## Project Structure
```
python_app/
├── agent_client.py
├── app/
│   └── clients/
│       └── chatgpt_client.py
├── bot.py
├── config.py
├── logger.py
├── main.py
└── utils/
    └── jwt_validator.py
```

## Access Control
- Configure role-based access via env vars (Slack user IDs):
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
