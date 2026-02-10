"""
AI client wrapper compatible with OpenAI/DeepSeek API standards.
Modified from original Claude client.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger

from src.config import settings


@dataclass
class AIRequest:
    messages: list[dict[str, str]]
    max_tokens: int = 2048  # DeepSeek 支持较长文本，稍微调大点
    timeout: float = 120
    model: str | None = None


class AIClient:
    """Lightweight OpenAI-compatible (DeepSeek) API client with retries."""

    def __init__(self):
        self.base_url = settings.claude_base_url.rstrip("/")
        self.api_key = settings.claude_api_key
        self.model = settings.claude_model

    async def send(self, req: AIRequest) -> str:
        # 1. 构造 OpenAI 格式的 payload
        payload = {
            "model": req.model or self.model,
            "max_tokens": req.max_tokens,
            "messages": req.messages,
            "temperature": 0.7,
            "stream": False
        }

        backoffs = [1, 2, 4]
        last_err: Exception | None = None

        # 2. 构造 OpenAI 格式的 Endpoint
        url = f"{self.base_url}/chat/completions"
        if "/v1" not in self.base_url and "/chat/completions" not in self.base_url:
             url = f"{self.base_url}/chat/completions"

        for attempt, backoff in enumerate(backoffs, start=1):
            try:
                async with httpx.AsyncClient(timeout=req.timeout) as client:
                    resp = await client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}",
                        },
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    return data["choices"][0]["message"]["content"].strip()
                    
            except Exception as e:
                last_err = e
                if "Insufficient Balance" in str(e):
                    break
                    
                if attempt < len(backoffs):
                    sleep_for = backoff + random.uniform(0, 0.3)
                    logger.warning(f"AI API error (attempt {attempt}): {e}. retrying...")
                    await asyncio.sleep(sleep_for)
                else:
                    break

        raise last_err or RuntimeError("AI API error")


# --- 下面的 JSON 辅助函数保持原样即可 ---

def _extract_json_block(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0]
    if "```" in text:
        return text.split("```")[1].split("```")[0]
    return text


def parse_json_with_repair(text: str, *, fix_newlines: bool = False) -> dict[str, Any]:
    """Parse JSON text; repair common issues if needed."""
    raw = _extract_json_block(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败，尝试修复: {e}")
        repaired = raw.replace("“", '"').replace("”", '"')
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
        if fix_newlines:
            def _fix_newlines(m: re.Match) -> str:
                return m.group(0).replace("\n", " ").replace("\r", "")
            repaired = re.sub(r'"[^"]*"', _fix_newlines, repaired)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e2:
            logger.warning(f"JSON 修复失败，尝试二次修复: {e2}")
            start = repaired.find("{")
            end = repaired.rfind("}")
            if start != -1 and end != -1 and end > start:
                repaired = repaired[start:end + 1]
            repaired = repaired.replace("\n", " ").replace("\r", " ").replace("\t", " ")
            repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
            return json.loads(repaired)
