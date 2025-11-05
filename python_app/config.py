from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

from dotenv import load_dotenv

# Load environment variables from a .env file if present.
load_dotenv()


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: Optional[str], default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(value: Optional[str], default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ServerConfig:
    port: int
    host: str
    events_path: str


@dataclass(frozen=True)
class BotConfig:
    default_responder: Literal["agent", "openai"]


@dataclass(frozen=True)
class SlackConfig:
    bot_token: str
    signing_secret: str
    app_token: Optional[str]
    socket_mode: bool


@dataclass(frozen=True)
class AgentApiConfig:
    url: str
    timeout: int


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: Optional[str]
    api_url: str
    model: str
    max_tokens: int
    temperature: float


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    environment: str


@dataclass(frozen=True)
class SecurityConfig:
    jwt_secret: Optional[str]
    jwt_expiration: str


@dataclass(frozen=True)
class Config:
    server: ServerConfig
    bot: BotConfig
    slack: SlackConfig
    agent_api: AgentApiConfig
    openai: OpenAIConfig
    logging: LoggingConfig
    security: SecurityConfig

    @classmethod
    def from_env(cls) -> "Config":
        default_responder = (os.getenv("DEFAULT_RESPONDER") or "agent").lower()
        if default_responder not in {"agent", "openai"}:
            # Defer throwing an error until validate() is called.
            pass

        return cls(
            server=ServerConfig(
                port=_parse_int(os.getenv("PORT"), 3978),
                host=os.getenv("HOST", "0.0.0.0"),
                events_path=os.getenv("SLACK_EVENTS_PATH", "/slack/events"),
            ),
            bot=BotConfig(default_responder=default_responder),  # type: ignore[arg-type]
            slack=SlackConfig(
                bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
                signing_secret=os.getenv("SLACK_SIGNING_SECRET", ""),
                app_token=os.getenv("SLACK_APP_TOKEN"),
                socket_mode=_parse_bool(os.getenv("SLACK_SOCKET_MODE"), False),
            ),
            agent_api=AgentApiConfig(
                url=os.getenv("AGENT_API_URL", "http://localhost:3001/api/agent"),
                timeout=_parse_int(os.getenv("AGENT_API_TIMEOUT"), 30_000),
            ),
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                api_url=os.getenv(
                    "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
                ),
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                max_tokens=_parse_int(os.getenv("OPENAI_MAX_TOKENS"), 1_000),
                temperature=_parse_float(os.getenv("OPENAI_TEMPERATURE"), 0.7),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "info"),
                environment=os.getenv("NODE_ENV", "development"),
            ),
            security=SecurityConfig(
                jwt_secret=os.getenv("JWT_SECRET"),
                jwt_expiration=os.getenv("JWT_EXPIRATION", "24h"),
            ),
        )

    def validate(self) -> None:
        missing_env = [
            name
            for name in ("SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET")
            if not os.getenv(name)
        ]
        if missing_env:
            raise ValueError(
                "Missing required environment variables: " + ", ".join(missing_env)
            )

        if self.slack.socket_mode and not self.slack.app_token:
            raise ValueError(
                "SLACK_APP_TOKEN is required when SLACK_SOCKET_MODE is true"
            )

        if self.bot.default_responder not in {"agent", "openai"}:
            raise ValueError(
                "Invalid DEFAULT_RESPONDER value: "
                f"{self.bot.default_responder}. Expected 'agent' or 'openai'."
            )


# Instantiate a config object once so the rest of the application can import it.
config = Config.from_env()

