from __future__ import annotations

import re
from typing import Callable

from slack_bolt import App
from slack_sdk.errors import SlackApiError

from .agent_client import call_agent
from .app.clients.chatgpt_client import call_chatgpt
from .config import config
from .logger import log_error, log_info


Responder = Callable[[str], str]


def _normalize_text(text: str | None) -> str:
    return (text or "").strip()


def _strip_bot_mention(text: str, bot_user_id: str | None) -> str:
    if not bot_user_id:
        return text.strip()
    mention_pattern = re.compile(rf"<@{re.escape(bot_user_id)}>?", re.IGNORECASE)
    return mention_pattern.sub("", text).strip()


def _extract_directive(text: str) -> str | None:
    if re.search(r"@agent\b", text, flags=re.IGNORECASE):
        return "agent"
    if re.search(r"@gpt\b", text, flags=re.IGNORECASE):
        return "openai"
    return None


def _select_responder(directive: str | None) -> Responder:
    if directive == "agent":
        return call_agent
    if directive == "openai":
        return call_chatgpt
    return {"agent": call_agent, "openai": call_chatgpt}.get(
        config.bot.default_responder, call_agent
    )


def register_listeners(app: App) -> None:
    @app.event("app_mention")
    def _(body, say, context, event, logger=None):
        _handle_message(event, say, context)

    @app.message(re.compile(".*"))
    def _(message, say, context, logger=None):
        if message.get("subtype") == "bot_message" or message.get("bot_id"):
            return
        _handle_message(message, say, context)


def _handle_message(message: dict, say, context: dict) -> None:
    try:
        text = _strip_bot_mention(
            _normalize_text(message.get("text")), context.get("bot_user_id")
        )
        if not text:
            return

        directive = _extract_directive(text)
        responder = _select_responder(directive)
        cleaned_text = re.sub(r"@agent\b|@gpt\b", "", text, flags=re.IGNORECASE).strip()
        prompt = cleaned_text or text
        reply = responder(prompt)
        response_text = reply or "No reply from agent."

        say(
            text=response_text,
            thread_ts=message.get("thread_ts") or message.get("ts"),
        )

        log_info(
            "Message processed",
            {
                "channel": message.get("channel"),
                "user": message.get("user"),
                "directive": directive or config.bot.default_responder,
            },
        )
    except SlackApiError as api_error:
        log_error("Failed to post response to Slack", api_error)
    except Exception as error:  # pylint: disable=broad-except
        log_error("Failed to process message", error)
        try:
            say("Sorry, something went wrong while handling your request.")
        except SlackApiError as api_error:
            log_error("Unable to send error message to Slack", api_error)

