from __future__ import annotations

from typing import Any, Dict, List

import requests

from ...config import config
from ...logger import log_error, log_info


def call_chatgpt(query: str) -> str:
    if not config.openai.api_key:
        log_error("ChatGPT API error", ValueError("OPENAI_API_KEY is not configured"))
        return "ChatGPT integration is not configured."

    payload: Dict[str, Any] = {
        "model": config.openai.model,
        "messages": [{"role": "user", "content": query}],
        "max_tokens": config.openai.max_tokens,
        "temperature": config.openai.temperature,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.openai.api_key}",
    }

    try:
        response = requests.post(
            config.openai.api_url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        try:
            data: Dict[str, Any] = response.json()
        except ValueError as error:
            log_error("OpenAI API returned invalid JSON", error)
            return "OpenAI API returned an unexpected response."
        log_info("ChatGPT response received", {"usage": data.get("usage")})
        choices: List[Dict[str, Any]] = data.get("choices") or []
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if content:
                return str(content)
        return "No response from ChatGPT."
    except requests.HTTPError as http_error:
        log_error("OpenAI API returned a non-success status", http_error)
        return "OpenAI API returned an error."
    except requests.RequestException as error:
        log_error("ChatGPT API error", error)
        return "Error connecting to ChatGPT. Please try again later."
