from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .bot import register_listeners
from .config import config
from .logger import log_error, log_info


def create_slack_app() -> App:
    slack_app = App(
        token=config.slack.bot_token,
        signing_secret=config.slack.signing_secret,
    )
    register_listeners(slack_app)
    return slack_app


def run_socket_mode(slack_app: App) -> None:
    if not config.slack.app_token:
        raise ValueError("SLACK_APP_TOKEN must be set for socket mode.")

    handler = SocketModeHandler(slack_app, config.slack.app_token)
    log_info(
        "Slack bot started in socket mode",
        {"environment": config.logging.environment},
    )
    handler.start()


def run_http_server(slack_app: App) -> None:
    flask_app = Flask(__name__)
    slack_handler = SlackRequestHandler(slack_app)
    events_path = (
        config.server.events_path
        if config.server.events_path.startswith("/")
        else f"/{config.server.events_path}"
    )

    @flask_app.post(events_path)
    def slack_events():
        return slack_handler.handle(request)

    @flask_app.get("/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 200

    host = config.server.host
    port = config.server.port
    log_info(
        "Slack bot server started",
        {
            "port": port,
            "host": host,
            "eventsPath": events_path,
            "environment": config.logging.environment,
        },
    )
    flask_app.run(host=host, port=port)


def main() -> None:
    try:
        config.validate()
    except Exception as error:  # pylint: disable=broad-except
        log_error("Configuration validation failed", error)
        raise

    slack_app = create_slack_app()

    try:
        if config.slack.socket_mode:
            run_socket_mode(slack_app)
        else:
            run_http_server(slack_app)
    except Exception as error:  # pylint: disable=broad-except
        log_error("Failed to start Slack bot", error)
        raise


if __name__ == "__main__":
    main()
