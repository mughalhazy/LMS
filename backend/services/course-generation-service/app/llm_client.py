from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class LLMClient:
    """
    Stdlib-only LLM client (OpenAI-compatible chat completions endpoint).
    No external dependencies — uses urllib.request + json only.

    Usage:
        client = LLMClient(api_key="sk-...", model="gpt-4o-mini")
        text   = client.complete(prompt="...")
        data   = client.complete_json(prompt="...", system_prompt="...")
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_s: int = 30,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def complete(self, *, prompt: str, system_prompt: str = "") -> str | None:
        """Send a chat completion request. Returns response text or None on any failure."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps(
            {"model": self._model, "messages": messages, "temperature": 0.3}
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                data: dict[str, Any] = json.loads(resp.read())
            return str(data["choices"][0]["message"]["content"])
        except Exception:
            # Best-effort — never raise; caller falls back to heuristic pipeline
            return None

    def complete_json(self, *, prompt: str, system_prompt: str = "") -> Any:
        """Complete and JSON-parse the response. Returns None on any failure or parse error."""
        raw = self.complete(prompt=prompt, system_prompt=system_prompt)
        if raw is None:
            return None
        # Strip markdown code fences if the model wraps its JSON
        stripped = raw.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            end = -1 if lines[-1].strip() == "```" else len(lines)
            stripped = "\n".join(lines[1:end])
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            return None
