"""LLM Client supporting Supabase Edge Functions and local Ollama fallback."""
from __future__ import annotations

import os
import requests
from typing import Optional

SUPABASE_EDGE_URL = os.getenv("SUPABASE_URL")
SUPABASE_EDGE_KEY = os.getenv("SUPABASE_KEY")
EDGE_FUNCTION_NAME = os.getenv("SUPABASE_EDGE_FUNCTION", "get_gemma_response")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")


class LLMClient:
    def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
        # Try edge function first if configured
        if SUPABASE_EDGE_URL and SUPABASE_EDGE_KEY:
            edge_resp = self._invoke_edge(prompt, temperature, max_tokens)
            if edge_resp:
                return edge_resp
        # Fallback to Ollama local
        return self._invoke_ollama(prompt, temperature, max_tokens)

    def _invoke_edge(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        try:
            fn_url = f"{SUPABASE_EDGE_URL}/functions/v1/{EDGE_FUNCTION_NAME}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPABASE_EDGE_KEY}",
            }
            resp = requests.post(
                fn_url,
                json={
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Support multiple possible keys
                return data.get("output") or data.get("response") or data.get("text") or str(data)
        except Exception:
            pass
        return None

    def _invoke_ollama(self, prompt: str, temperature: float, max_tokens: int) -> str:
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "options": {"temperature": temperature},
                    # Ollama may not use max_tokens directly but keep for possible future
                },
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response") or data.get("output") or data.get("text") or str(data)
        except Exception as e:
            return f"[LLM error: {e}]"
