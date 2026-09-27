"""
providers.py
------------
The three LLM provider adapters and the failover orchestrator.

Design contract -- every provider function has the same signature and the same
error behaviour:

    async def call_<provider>(system_prompt: str, user_prompt: str) -> str

It returns the assistant's reply text on success, and raises on any failure. It
never returns None and never swallows an exception. All failure handling lives in
the orchestrator, which keeps the adapters small and uniform.

Every adapter enforces PROVIDER_TIMEOUT_SECONDS so a hanging upstream cannot
stall the chain.
"""

import logging
import time

import httpx

from app.assistant.config import (
    CEREBRAS_BASE_URL,
    CEREBRAS_MODEL,
    GEMINI_MODEL,
    GROQ_MODEL,
    MAX_OUTPUT_TOKENS,
    PROVIDER_FAILOVER_ORDER,
    PROVIDER_TIMEOUT_SECONDS,
    settings,
)

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Raised by an adapter when its provider fails. Carries the provider name."""

    def __init__(self, provider: str, cause: Exception | str) -> None:
        self.provider = provider
        self.cause = cause
        super().__init__(f"{provider} failed: {cause}")


# ---------------------------------------------------------------------------
# Provider 1: Groq (primary)
# ---------------------------------------------------------------------------


async def call_groq(system_prompt: str, user_prompt: str) -> str:
    """
    Call Groq via the official groq SDK.

    Primary in the chain because it is the fastest of the three -- roughly 1-2s per
    answer against Gemini's 3-5s -- and a user waits for whichever provider answers
    first. Position is set by config.PROVIDER_FAILOVER_ORDER, not by this file.

    The groq SDK ships an AsyncGroq client, so unlike Gemini there is no thread
    offload needed -- the call is natively awaitable.
    """
    import asyncio

    from groq import AsyncGroq

    if not settings.groq_api_key:
        raise ProviderError("groq", "GROQ_API_KEY is not configured")

    async def _call() -> str:
        client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.2,
        )
        text = completion.choices[0].message.content
        if not text or not text.strip():
            raise ProviderError("groq", "empty response from model")
        return text.strip()

    try:
        return await asyncio.wait_for(_call(), timeout=PROVIDER_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        raise ProviderError("groq", "timed out") from exc
    except ProviderError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ProviderError("groq", exc) from exc


# ---------------------------------------------------------------------------
# Provider 2: Google Gemini (fallback 1)
# ---------------------------------------------------------------------------


async def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """
    Call Google Gemini via the official google-generativeai SDK.

    Fallback rather than primary: it is the slowest of the three, so its 3-5s is
    only worth paying when Groq is unavailable. Position is set by
    config.PROVIDER_FAILOVER_ORDER, not by this file.

    The SDK is synchronous, so the blocking call is pushed onto a worker thread
    with asyncio.to_thread. Without this the event loop would block for the full
    duration of the request and every concurrent /chat call would queue behind it.
    """
    import asyncio

    from google import genai
    from google.genai import types

    if not settings.gemini_api_key:
        raise ProviderError("gemini", "GEMINI_API_KEY is not configured")

    def _blocking_call() -> str:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                # Grounding rules require deterministic, documentation-faithful
                # output. Low temperature keeps the model from improvising.
                temperature=0.2,
            ),
        )
        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise ProviderError("gemini", "empty response from model")
        return text.strip()

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_blocking_call),
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise ProviderError("gemini", "timed out") from exc
    except ProviderError:
        raise
    except Exception as exc:  # noqa: BLE001 - any SDK/network failure triggers failover
        raise ProviderError("gemini", exc) from exc


# ---------------------------------------------------------------------------
# Provider 3: Cerebras (fallback 2)
# ---------------------------------------------------------------------------


async def call_cerebras(system_prompt: str, user_prompt: str) -> str:
    """
    Call Cerebras over its OpenAI-compatible REST API using httpx.

    Cerebras exposes the standard /chat/completions shape, so we talk to it with a
    plain bearer-token POST rather than pulling in the OpenAI SDK -- fewer
    dependencies, and httpx gives us a native async client and explicit timeouts.
    """
    if not settings.cerebras_api_key:
        raise ProviderError("cerebras", "CEREBRAS_API_KEY is not configured")

    payload = {
        "model": CEREBRAS_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.cerebras_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=PROVIDER_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{CEREBRAS_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise ProviderError(
            "cerebras", f"HTTP {exc.response.status_code}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ProviderError("cerebras", "timed out") from exc
    except Exception as exc:  # noqa: BLE001
        raise ProviderError("cerebras", exc) from exc

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("cerebras", "malformed response body") from exc

    if not text or not text.strip():
        raise ProviderError("cerebras", "empty response from model")
    return text.strip()


# ---------------------------------------------------------------------------
# Failover orchestrator
# ---------------------------------------------------------------------------

# Ordered failover chain: primary first, then fallbacks.
#
# The order is NOT written here. It comes from config.PROVIDER_FAILOVER_ORDER, which
# is also what /health reports -- keeping one list means the order that is documented
# and the order that is attempted cannot drift apart. This mapping only says which
# adapter implements which provider name.
#
# Current order: groq -> gemini -> cerebras (fastest first, see config.py).
_ADAPTERS = {
    "groq": call_groq,
    "gemini": call_gemini,
    "cerebras": call_cerebras,
}

PROVIDER_CHAIN = tuple(
    (name, _ADAPTERS[name]) for name in PROVIDER_FAILOVER_ORDER
)


async def generate_reply(
    system_prompt: str,
    user_prompt: str,
) -> tuple[str | None, str | None]:
    """
    Walk the failover chain and return (reply, provider_used).

    Semantics:
      - Providers without a configured API key are skipped up front (no wasted
        network round-trip). Skipping is logged at INFO, failing is logged at
        WARNING -- they are genuinely different conditions.
      - The first provider to return text wins; the chain stops immediately.
      - Any exception from an adapter is caught, logged with its cause and
        latency, and the next provider is tried.
      - If the entire chain is exhausted, returns (None, None). The caller is
        responsible for turning that into the user-facing fallback message.

    Latency is measured per attempt so operators can see, for example, that
    Gemini is slow-but-working versus Groq failing instantly on a 429.
    """
    last_error: str | None = None

    for name, adapter in PROVIDER_CHAIN:
        key_configured = {
            "gemini": settings.gemini_api_key,
            "groq": settings.groq_api_key,
            "cerebras": settings.cerebras_api_key,
        }[name]

        if not key_configured:
            logger.info("Provider %s skipped (no API key configured)", name)
            continue

        started = time.perf_counter()
        logger.info("Provider %s attempt started", name)
        try:
            reply = await adapter(system_prompt, user_prompt)
        except ProviderError as exc:
            elapsed = time.perf_counter() - started
            last_error = str(exc.cause)
            logger.warning(
                "Provider %s failed after %.2fs: %s -- trying next provider",
                name,
                elapsed,
                exc.cause,
            )
            continue
        except Exception as exc:  # noqa: BLE001 - defensive: adapter contract violated
            elapsed = time.perf_counter() - started
            last_error = str(exc)
            logger.warning(
                "Provider %s raised an unexpected %s after %.2fs: %s -- trying next provider",
                name,
                type(exc).__name__,
                elapsed,
                exc,
            )
            continue

        elapsed = time.perf_counter() - started
        logger.info("Provider %s succeeded in %.2fs", name, elapsed)
        return reply, name

    logger.error(
        "All providers in the failover chain failed. Last error: %s", last_error
    )
    return None, None
