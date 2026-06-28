from __future__ import annotations

import json
import re
import time
import urllib.request


def _api_url(endpoint: str) -> str:
    value = (endpoint or "").strip()
    if value.startswith(("http://", "https://")):
        if "/" in value.removeprefix("https://").removeprefix("http://"):
            return value
        return value.rstrip("/") + "/v1/chat/completions"
    if "/" in value:
        return "https://" + value
    return "https://" + value.rstrip("/") + "/v1/chat/completions"


def install_api_url_patch() -> None:
    from eoh.llm import api_general

    def get_response(self, prompt_content: str, max_retries: int = 5):
        payload = json.dumps({
            "model": self.model_LLM,
            "messages": [{"role": "user", "content": prompt_content}],
        }).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "opencode/1.0",
        }
        url = _api_url(self.api_endpoint)
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    parsed = json.loads(resp.read().decode("utf-8", "replace"))
                choices = parsed.get("choices")
                if not choices:
                    error_msg = parsed.get("error", {}).get("message", str(parsed))
                    raise ValueError(f"API returned no choices: {error_msg}")
                return choices[0]["message"]["content"]
            except Exception as exc:
                api_general.logger.debug("API error (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        api_general.logger.warning(
            "API call failed after %d attempts (endpoint=%s, model=%s).",
            max_retries,
            self.api_endpoint,
            self.model_LLM,
        )
        return None

    api_general.InterfaceAPI.get_response = get_response
