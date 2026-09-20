"""
iam_auth.py — LLM API helper for the AI Dev Team pipeline.

Using Groq Cloud API.
All agents import `call_bob_chat` from this module — the function name
is kept for backward compatibility so zero import changes are needed.

Usage:
    from orchestration.iam_auth import call_bob_chat
    result = call_bob_chat("Generate acceptance criteria for ...")
"""

from __future__ import annotations

import os
import re
import time
from typing import cast
from groq import Groq
from groq.types.chat import ChatCompletionMessageParam

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Per-call output token ceiling — the model's hard maximum.
# Groq free-tier OTPM rate limits are enforced as retriable 429 errors
# and must NOT be absorbed by pre-truncating every response.
_MAX_OUTPUT_TOKENS = int(os.environ.get("GROQ_MAX_OUTPUT_TOKENS", "32768"))

# Retry settings for 429 rate-limit responses.
_RATE_LIMIT_MAX_RETRIES = int(os.environ.get("GROQ_RATE_LIMIT_RETRIES", "3"))
_RATE_LIMIT_DEFAULT_WAIT = float(os.environ.get("GROQ_RATE_LIMIT_WAIT_S", "15.0"))


class LLMCallError(Exception):
    """Raised when the LLM API call fails.

    Circuit breaker and agent wrappers catch this to route to fallback logic.
    """


def _parse_retry_after(error_message: str) -> float:
    """
    Extract the suggested wait time (in seconds) from a Groq 429 error message.

    Groq rate-limit errors typically look like:
        "Rate limit reached... Please try again in 10.5s"
        "Please try again in 1m30s"

    Returns the parsed seconds, or _RATE_LIMIT_DEFAULT_WAIT if not found.
    """
    match = re.search(
        r"try again in\s+(?:(\d+)m\s*)?(\d+(?:\.\d+)?s)?",
        error_message,
        re.IGNORECASE,
    )
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds_str = match.group(2) or "0s"
        seconds = float(seconds_str.rstrip("s"))
        total = minutes * 60 + seconds
        if total > 0:
            return min(total, 60.0)
    return min(_RATE_LIMIT_DEFAULT_WAIT, 60.0)


def call_bob_chat(
    prompt_or_messages: str | list[ChatCompletionMessageParam],
    system_prompt: str | None = None,
    max_tokens: int = 1500,
    model_override: str | None = None,
    timeout: int = 60,
) -> str:
    """
    Execute a chat completion call via the Groq API.

    Automatically retries on 429 rate-limit responses, waiting the duration
    suggested by Groq before each retry (up to _RATE_LIMIT_MAX_RETRIES times).

    Parameters
    ----------
    prompt_or_messages : A plain string (treated as user message) or a list of
                         OpenAI-style message dicts.
    system_prompt      : Optional system prompt prepended to the messages.
    max_tokens         : Maximum tokens in the completion response. Capped at
                         _MAX_OUTPUT_TOKENS (default 32 768, overridable via
                         GROQ_MAX_OUTPUT_TOKENS env var).
    model_override     : Override the default model for this call.
    timeout            : Request timeout in seconds.

    Returns
    -------
    The assistant's response text (stripped).

    Raises
    ------
    LLMCallError
        On any failure (missing key, network error, API error, empty response,
        or rate limit exhausted after all retries).
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise LLMCallError(
            "GROQ_API_KEY is not set. Add it to your .env file.\n"
            "Get your API key from: https://console.groq.com"
        )

    model = model_override or os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    max_tokens = min(max_tokens, _MAX_OUTPUT_TOKENS)

    # Build messages list once — reused across retries
    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if isinstance(prompt_or_messages, str):
        messages.append(cast(ChatCompletionMessageParam, {"role": "user", "content": prompt_or_messages}))
    else:
        messages.extend(cast(list[ChatCompletionMessageParam], prompt_or_messages))

    last_exc: Exception | None = None

    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 2):  # +2: initial attempt + N retries
        try:
            client = Groq(api_key=api_key, timeout=timeout)
            
            stream_output = os.environ.get("STREAM_AGENT_OUTPUT") == "1"
            agent_name = os.environ.get("CURRENT_AGENT_NAME")
            
            if stream_output and agent_name:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=True,
                )
                import json as _json
                full_content = []
                for chunk in response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_content.append(delta)
                        event = {
                            "event": "agent_stream",
                            "agent": agent_name,
                            "chunk": delta
                        }
                        print(f"@@AGENT_STREAM@@{_json.dumps(event)}", flush=True)
                content = "".join(full_content)
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                )

                try:
                    content = response.choices[0].message.content
                except (IndexError, AttributeError) as exc:
                    raise LLMCallError(
                        f"Groq API response missing content: {str(response)[:200]}"
                    ) from exc

            if not content or not content.strip():
                raise LLMCallError("Groq API returned empty content.")

            return content.strip()

        except LLMCallError:
            raise  # re-raise our own errors immediately

        except Exception as exc:
            err_str = str(exc)
            last_exc = exc

            is_rate_limit = (
                "429" in err_str
                or "rate_limit" in err_str.lower()
                or "rate limit" in err_str.lower()
                or "too many requests" in err_str.lower()
            )

            if is_rate_limit and attempt <= _RATE_LIMIT_MAX_RETRIES:
                wait_s = _parse_retry_after(err_str) + 1.0  # +1s buffer
                print(
                    f"[iam_auth] Rate limit hit (attempt {attempt}/{_RATE_LIMIT_MAX_RETRIES}). "
                    f"Waiting {wait_s:.1f}s before retry..."
                )
                time.sleep(wait_s)
                continue

            raise LLMCallError(f"Groq API call failed: {err_str[:300]}") from exc

    raise LLMCallError(
        f"Groq API rate limit exceeded after {_RATE_LIMIT_MAX_RETRIES} retries. "
        f"Last error: {str(last_exc)[:200]}"
    )
