"""
medjar.llm — provider adapters for the production reasoning path.

Standard library only (`urllib`), so the prototype keeps its zero-dependency
property. An adapter is any callable

    adapter(system_prompt, user_prompt) -> str

returning the model's raw text. `LLMEngine` (see agents.py) parses that text as
the reasoning contract.

Supported out of the box:

  * `OpenAIAdapter`     — any OpenAI-compatible /chat/completions endpoint
                          (OpenAI, Azure OpenAI, vLLM, Ollama, LM Studio,
                          Together, Groq, OpenRouter, …) via `base_url`
  * `AnthropicAdapter`  — /v1/messages
  * `ScriptedAdapter`   — offline, deterministic; used to exercise the whole
                          LLM code path without network access

API keys are read from the environment and are never logged.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

__all__ = [
    "LLMError", "LLMConfigError", "OpenAIAdapter", "AnthropicAdapter", "ScriptedAdapter",
    "build_adapter", "extract_json",
]


class LLMError(RuntimeError):
    """Raised when a provider call fails or its output cannot be parsed."""


class LLMConfigError(LLMError):
    """Misconfiguration: missing credentials, bad endpoint, rejected auth.

    Held distinct from transient and parse failures because it must never be
    swallowed. A single agent losing a turn is survivable; a system that is
    wholly unable to reach its model must fail loudly rather than quietly
    emitting empty differentials.
    """


# --------------------------------------------------------------------------
# JSON recovery
# --------------------------------------------------------------------------
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> Dict:
    """Recover a JSON object from model output.

    Models wrap JSON in prose or code fences, and occasionally emit trailing
    commas. We try, in order: the raw string, any fenced block, then the widest
    brace-balanced span, applying a trailing-comma repair to each.
    """
    candidates: List[str] = [text.strip()]

    for m in _FENCE.finditer(text):
        candidates.append(m.group(1).strip())

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])

    for cand in candidates:
        if not cand:
            continue
        for attempt in (cand, re.sub(r",\s*([}\]])", r"\1", cand)):
            try:
                out = json.loads(attempt)
            except (ValueError, TypeError):
                continue
            if isinstance(out, dict):
                return out
    raise LLMError(f"no JSON object found in model output: {text[:200]!r}")


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def _post_json(url: str, payload: Dict, headers: Dict[str, str],
               timeout: float, retries: int, backoff: float) -> Dict:
    body = json.dumps(payload).encode("utf-8")
    last: Optional[Exception] = None

    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:                      # noqa: PERF203
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:400]
            except Exception:                                    # pragma: no cover
                pass
            if e.code in (401, 403):
                raise LLMConfigError(
                    f"authentication rejected (HTTP {e.code}) by {url}: {detail}")
            last = LLMError(f"HTTP {e.code} from {url}: {detail}")
            # 4xx other than rate limiting will not succeed on retry
            if e.code not in (408, 409, 425, 429) and e.code < 500:
                raise last
        except urllib.error.URLError as e:
            last = LLMError(f"network error contacting {url}: {e.reason}")
        except (ValueError, TypeError) as e:
            last = LLMError(f"malformed JSON response from {url}: {e}")
            raise last

        if attempt < retries:
            time.sleep(backoff * (2 ** attempt))

    raise last if last else LLMError("request failed")


# --------------------------------------------------------------------------
# Adapters
# --------------------------------------------------------------------------
@dataclass
class OpenAIAdapter:
    """Any OpenAI-compatible chat-completions endpoint."""

    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1600
    json_mode: bool = True
    timeout: float = 90.0
    retries: int = 2
    backoff: float = 1.5
    calls: int = field(default=0, init=False)

    def _key(self) -> str:
        key = self.api_key or os.environ.get(self.api_key_env, "")
        if not key:
            raise LLMConfigError(
                f"no API key: set ${self.api_key_env} or pass api_key=…")
        return key

    def __call__(self, system: str, user: str) -> str:
        payload: Dict = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = _post_json(f"{self.base_url.rstrip('/')}/chat/completions",
                          payload, {"Authorization": f"Bearer {self._key()}"},
                          self.timeout, self.retries, self.backoff)
        self.calls += 1
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e


@dataclass
class AnthropicAdapter:
    """Anthropic /v1/messages."""

    model: str = "claude-sonnet-4-5"
    base_url: str = "https://api.anthropic.com/v1"
    api_key_env: str = "ANTHROPIC_API_KEY"
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1600
    version: str = "2023-06-01"
    timeout: float = 90.0
    retries: int = 2
    backoff: float = 1.5
    calls: int = field(default=0, init=False)

    def _key(self) -> str:
        key = self.api_key or os.environ.get(self.api_key_env, "")
        if not key:
            raise LLMConfigError(
                f"no API key: set ${self.api_key_env} or pass api_key=…")
        return key

    def __call__(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": user}],
        }
        data = _post_json(f"{self.base_url.rstrip('/')}/messages", payload,
                          {"x-api-key": self._key(),
                           "anthropic-version": self.version},
                          self.timeout, self.retries, self.backoff)
        self.calls += 1
        try:
            parts = data["content"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, TypeError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e


@dataclass
class ScriptedAdapter:
    """Deterministic offline adapter.

    Returns a canned response for the first persona keyword found in the system
    prompt. This exists so the entire LLM path — prompt construction, transport
    boundary, contract parsing, citation validation, debate, consensus and
    reporting — can be executed and verified in environments with no outbound
    network access.
    """

    responses: Dict[str, str] = field(default_factory=dict)
    default: str = '{"differential": [], "red_flags": [], "confidence": 0.3}'
    calls: int = field(default=0, init=False)
    log: List[str] = field(default_factory=list, init=False)

    def __call__(self, system: str, user: str) -> str:
        self.calls += 1
        self.log.append(system[:60])
        low = system.lower()
        for key, resp in self.responses.items():
            if key.lower() in low:
                return resp
        return self.default


# --------------------------------------------------------------------------
def build_adapter(provider: str = "openai", model: Optional[str] = None,
                  base_url: Optional[str] = None,
                  api_key: Optional[str] = None,
                  temperature: float = 0.2) -> Callable[[str, str], str]:
    """Construct an adapter by provider name.

    `provider` is one of: openai, anthropic, or any OpenAI-compatible service
    reached by supplying `base_url` (e.g. http://localhost:11434/v1 for Ollama).
    """
    p = provider.strip().lower()
    if p in ("anthropic", "claude"):
        kw: Dict = {"temperature": temperature}
        if model:
            kw["model"] = model
        if base_url:
            kw["base_url"] = base_url
        if api_key:
            kw["api_key"] = api_key
        return AnthropicAdapter(**kw)

    if p in ("openai", "azure", "vllm", "ollama", "together", "groq",
             "openrouter", "compatible", "local"):
        kw = {"temperature": temperature}
        if model:
            kw["model"] = model
        if base_url:
            kw["base_url"] = base_url
        if api_key:
            kw["api_key"] = api_key
        if p == "ollama":
            kw.setdefault("base_url", "http://localhost:11434/v1")
            kw["api_key"] = api_key or "ollama"     # local servers ignore this
            kw["json_mode"] = False
        return OpenAIAdapter(**kw)

    raise LLMError(f"unknown provider {provider!r}")
