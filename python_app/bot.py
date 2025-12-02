from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Callable, List

from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from .access_control import can_use_feature
from .agent_client import AgentUnavailableError, call_agent
from .app.clients.chatgpt_client import call_chatgpt
from .config import config
from .logger import log_error, log_info, log_warn


Responder = Callable[[str], str]
_last_activity_at = datetime.now(timezone.utc)


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


def _select_responder(directive: str | None) -> tuple[Responder, str]:
    if directive == "agent":
        return call_agent, "agent"
    if directive == "openai":
        return call_chatgpt, "openai"
    default = config.bot.default_responder
    return (
        {"agent": call_agent, "openai": call_chatgpt}.get(default, call_agent),
        default,
    )


def register_listeners(app: App) -> None:
    _perform_startup_warmup()

    @app.event("app_mention")
    def _(body, say, context, event, client, logger=None):
        _handle_message(event, say, context, client)

    @app.event("app_home_opened")
    def handle_app_home_opened(event, client, logger=None):
        try:
            client.views_publish(
                user_id=event.get("user"),
                view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Hi there!* I'm ready to help.\n• Ask with `@agent` to reach your agent.\n• Ask with `@gpt` (or default) to reach OpenAI.\n• Works in channels, threads, and DMs.",
                            },
                        }
                    ],
                },
            )
        except Exception as error:  # pylint: disable=broad-except
            log_error("Failed to publish App Home", error)

    @app.message(re.compile(".*"))
    def _(message, say, context, client, logger=None):
        if message.get("subtype") == "bot_message" or message.get("bot_id"):
            return
        _handle_message(message, say, context, client)


def _handle_message(message: dict, say, context: dict, client: WebClient) -> None:
    try:
        text = _strip_bot_mention(
            _normalize_text(message.get("text")), context.get("bot_user_id")
        )
        if not text:
            return

        directive = _extract_directive(text)
        responder, responder_name = _select_responder(directive)
        user_id = message.get("user") or ""
        if not can_use_feature(user_id, responder_name):
            log_warn(
                "Access denied for user",
                {"user": user_id, "feature": responder_name},
            )
            say(
                text="You do not have access to use this bot right now.",
                thread_ts=message.get("thread_ts") or message.get("ts"),
            )
            return

        _maybe_notify_wakeup(say, message)

        cleaned_text = re.sub(r"@agent\b|@gpt\b", "", text, flags=re.IGNORECASE).strip()
        prompt = _build_prompt_with_context(
            cleaned_text or text,
            _fetch_thread_context(
                client,
                channel=message.get("channel"),
                thread_ts=message.get("thread_ts") or message.get("ts"),
                latest_ts=message.get("ts"),
            ),
        )
        try:
            reply = responder(prompt)
        except AgentUnavailableError as agent_error:
            if responder_name == "agent":
                log_warn(
                    "Agent unavailable, falling back to ChatGPT",
                    {"error": str(agent_error)},
                )
                reply = call_chatgpt(prompt)
            else:
                raise
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
                "directive": directive or responder_name,
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


def _maybe_notify_wakeup(say, message: dict) -> None:
    global _last_activity_at  # noqa: PLW0603 - shared timestamp for idle tracking

    now = datetime.now(timezone.utc)
    idle_minutes = config.bot.idle_sleep_minutes
    idle_threshold = timedelta(minutes=max(idle_minutes, 1))
    if now - _last_activity_at >= idle_threshold:
        duration_minutes = int((now - _last_activity_at).total_seconds() // 60)
        say(
            text=f"I'm back! I was asleep for {duration_minutes} minute(s).",
            thread_ts=message.get("thread_ts") or message.get("ts"),
        )
    _last_activity_at = now


def _fetch_thread_context(
    client: WebClient,
    channel: str | None,
    thread_ts: str | None,
    latest_ts: str | None,
    limit: int = 5,
) -> List[str]:
    if not channel or not thread_ts:
        return []
    try:
        response = client.conversations_replies(
            channel=channel,
            ts=thread_ts,
            limit=limit,
        )
    except SlackApiError as api_error:
        log_warn(
            "Failed to fetch thread context",
            {"channel": channel, "thread": thread_ts, "error": str(api_error)},
        )
        return []
    messages: List[dict] = response.get("messages", [])
    history = []
    for entry in messages:
        text = entry.get("text")
        ts = entry.get("ts")
        if not text or ts == latest_ts:
            continue
        user = entry.get("user") or "system"
        history.append(f"{user}: {text}")
    return history[-limit:]


def _build_prompt_with_context(prompt: str, context_lines: List[str]) -> str:
    if not context_lines:
        return prompt
    context_text = "\n".join(context_lines)
    return f"Previous conversation:\n{context_text}\n\nLatest request:\n{prompt}"


def _perform_startup_warmup() -> None:
    responder_name = config.bot.default_responder
    warmup_prompt = "Health check"
    try:
        if responder_name == "agent":
            call_agent(warmup_prompt)
        else:
            call_chatgpt(warmup_prompt)
        log_info("Responder warm-up succeeded", {"target": responder_name})
    except Exception as error:  # pylint: disable=broad-except
        log_warn(
            "Responder warm-up failed",
            {"target": responder_name, "error": str(error)},
        )
