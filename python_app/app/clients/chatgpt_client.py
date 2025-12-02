from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import requests

from ...config import config
from ...logger import log_error, log_info


def call_chatgpt(query: str) -> str:
    if not config.openai.api_key:
        log_error("ChatGPT API error", ValueError("OPENAI_API_KEY is not configured"))
        return "ChatGPT integration is not configured."

    prefers_responses_api = "responses" in config.openai.api_url.rstrip("/").split("/")[-1]
    try:
        return _call_openai_api(
            url=config.openai.api_url,
            payload=_build_payload(query, prefers_responses_api),
            parser=_parse_response if prefers_responses_api else _parse_chat_completion,
        )
    except requests.HTTPError as http_error:
        response = http_error.response
        body = None
        status = None
        try:
            if response is not None:
                status = response.status_code
                body = response.text
        except Exception:
            body = None
        log_error(
            "OpenAI Responses call failed",
            {
                "status": status,
                "body": body,
            },
        )
        return "Live answer unavailable (Responses API failed)."
    except requests.RequestException as error:
        log_error("ChatGPT API error", error)
        return "Error connecting to ChatGPT. Please try again later."


def _call_openai_api(
    *,
    url: str,
    payload: Dict[str, Any],
    parser: Callable[[Dict[str, Any]], Optional[str]],
) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.openai.api_key}",
    }

    response = requests.post(
        url,
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
    content = parser(data)
    return content or "No response from ChatGPT."


def _build_payload(query: str, use_responses: bool) -> Dict[str, Any]:
    if use_responses:
        payload = {
            "model": config.openai.model,
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": query}],
                }
            ],
            "max_output_tokens": config.openai.max_tokens,
            "temperature": config.openai.temperature,
        }
        if config.openai.browser_enabled:
            tool_type = "web_search_preview_2025_03_11"
            payload["tools"] = [{"type": tool_type}]
            payload["tool_choice"] = "required"
        return payload

    return {
        "model": config.openai.model,
        "messages": [{"role": "user", "content": query}],
        "max_tokens": config.openai.max_tokens,
        "temperature": config.openai.temperature,
    }


def _parse_response(data: Dict[str, Any]) -> Optional[str]:
    output: List[Dict[str, Any]] = data.get("output") or []
    for item in output:
        content_entries: List[Dict[str, Any]] = item.get("content") or []
        for entry in content_entries:
            if entry.get("type") in {"text", "output_text"}:
                text_value: Optional[str] = entry.get("text")
                if text_value:
                    return text_value
    return None


def _parse_chat_completion(data: Dict[str, Any]) -> Optional[str]:
    choices: List[Dict[str, Any]] = data.get("choices") or []
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if content:
            return str(content)
    return None
