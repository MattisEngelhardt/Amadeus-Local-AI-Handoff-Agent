from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama runtime cannot be reached."""


class OllamaModelMissing(RuntimeError):
    """Raised when a required local Ollama model is not available."""


@dataclass(frozen=True)
class OllamaGenerateResult:
    text: str
    model: str
    raw: dict[str, Any]


class OllamaClient:
    """Small stdlib-only client for the local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(req, timeout=timeout or self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            message = f"HTTP {exc.code}: {details or exc.reason}"
            raise OllamaUnavailable(message) from exc
        except error.URLError as exc:
            raise OllamaUnavailable(str(exc)) from exc

        if not raw_body.strip():
            return {}

        try:
            return json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama returned invalid JSON: {raw_body[:300]}") from exc

    def list_models(self) -> list[str]:
        data = self._request("GET", "/api/tags", timeout=10)
        names = set()
        for model in data.get("models", []):
            name = model.get("name", "")
            if not name:
                continue
            names.add(name)
            if name.endswith(":latest"):
                names.add(name.removesuffix(":latest"))
        return sorted(names)

    def is_available(self) -> bool:
        try:
            self.list_models()
            return True
        except OllamaUnavailable:
            return False

    def ensure_model(self, model: str) -> None:
        models = self.list_models()
        if model not in models:
            raise OllamaModelMissing(f"Model '{model}' is not installed. Run: ollama pull {model}")

    def generate(
        self,
        prompt: str,
        model: str,
        system: str | None = None,
        response_format: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if response_format:
            payload["format"] = response_format
        if options:
            payload["options"] = options

        logger.info("Sending prompt to local Ollama model '%s'.", model)
        data = self._request("POST", "/api/generate", payload=payload)
        return str(data.get("response", "")).strip()

    def generate_structured(
        self,
        prompt: str,
        model: str,
        system: str,
        response_model: type[BaseModel],
        options: dict[str, Any] | None = None,
    ) -> BaseModel:
        raw = self.generate(
            prompt=prompt,
            model=model,
            system=system,
            response_format="json",
            options=options,
        )
        return response_model.model_validate_json(raw)
