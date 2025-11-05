from __future__ import annotations

from typing import Optional

import requests

from .config import config
from .logger import log_error, log_info


def call_agent(query: str) -> str:
    try:
        response = requests.post(
            config.agent_api.url,
            json={"query": query},
            timeout=config.agent_api.timeout / 1000,
        )
        response.raise_for_status()
        try:
            data: Optional[dict] = response.json() if response.content else None
        except ValueError as error:
            log_error("Agent API returned invalid JSON", error)
            return "Agent returned an unreadable response."
        log_info("Agent response received", data or {})
        if isinstance(data, dict) and data.get("response"):
            return str(data["response"])
        return "Agent did not return any message."
    except requests.HTTPError as http_error:
        log_error("Agent API returned a non-success status", http_error)
        return "Agent returned an error while processing the request."
    except requests.RequestException as error:
        log_error("Agent API error", error)
        return "Error connecting to agent."
