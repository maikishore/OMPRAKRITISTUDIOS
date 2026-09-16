import json
import re
import httpx
import logging
from typing import Dict, Any, List, Optional
from core.config import settings

logger = logging.getLogger("microdrama.llm_client")

class LLMClient:
    """Universal LLM client configured for Cloudflare Workers AI with gemma-4-26b-a4b-it."""

    def __init__(self, account_id: Optional[str] = None, auth_token: Optional[str] = None, model: Optional[str] = None):
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        self.auth_token = auth_token or settings.CLOUDFLARE_AUTH_TOKEN
        self.model = model or settings.LLM_MODEL or "@cf/google/gemma-4-26b-a4b-it"

    def is_configured(self) -> bool:
        return bool(self.account_id and self.auth_token)

    def generate_chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Calls Cloudflare Workers AI Gemma endpoint."""
        if not self.is_configured():
            logger.warning("Cloudflare credentials not configured.")
            raise ValueError("Cloudflare Account ID or Auth Token is not configured. Please set them in Settings or .env.")

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                raise RuntimeError(f"Cloudflare Workers AI returned error: {errors}")

            result = data.get("result", {})
            return result.get("response", "").strip()

    def generate_structured_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Ensures the LLM returns clean, validated JSON object."""
        augmented_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: You MUST respond ONLY with a single valid JSON object. "
            "Do NOT include markdown formatting, backticks (```json), or any conversational commentary."
        )

        raw_response = self.generate_chat(augmented_system, user_prompt)
        return self._extract_json(raw_response)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extracts and parses JSON from potentially noisy LLM outputs."""
        if not text:
            raise ValueError("Empty response received from LLM.")

        # Remove markdown code blocks if present
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        # Try parsing directly
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback regex search for outer-most curly braces
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception as e:
                    raise ValueError(f"Failed to parse extracted JSON substring: {e}. Raw: {clean_text[:200]}")
            raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}")
