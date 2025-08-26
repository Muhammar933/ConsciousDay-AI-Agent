# agent/reflection_agent.py
"""
Agent wrapper for ConsciousDay: generate reflection & strategy using LangChain + OpenRouter/OpenAI.

Provides:
    generate_reflection(journal, intention, dream, priorities) -> dict
Return dict keys:
    - reflection
    - dream_summary
    - mindset
    - strategy

Notes:
    - Expects OPENAI_API_KEY to be set in env (or use OpenRouter by also setting OPENAI_BASE_URL).
    - If no API key present, the function returns an error dict instead of raising.
"""

import os
import json
import re
from typing import Dict, Any

from dotenv import load_dotenv

# LangChain imports
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except Exception as e:
    raise ImportError(
        "langchain is required. Install with `pip install langchain` and ensure langchain.chat_models is available."
    ) from e

# load .env if present
load_dotenv()

# Read environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # used for OpenRouter or OpenAI
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional: e.g., https://openrouter.ai/api/v1
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # optional fallback (not implemented here)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # default model name; change as needed
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

PROMPT_TEMPLATE = """You are a daily reflection and planning assistant.
Your goals:
1) Reflect on the user's morning journal and dream input.
2) Interpret the user's emotional and mental state.
3) Understand their intention and top 3 priorities.
4) Generate a practical, energy-aligned, time-aware strategy for the day.

INPUT:
Morning Journal: {journal}
Intention: {intention}
Dream: {dream}
Top 3 Priorities: {priorities}

OUTPUT (in JSON):
Return a JSON object exactly with these keys:
- reflection (short paragraph)
- dream_summary (short paragraph)
- mindset (short paragraph)
- strategy (short paragraph, include time-aligned suggestions if possible)

Example:
{{"reflection":"...","dream_summary":"...","mindset":"...","strategy":"..."}}
"""

_PROMPT = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["journal", "intention", "dream", "priorities"])


def _build_llm() -> ChatOpenAI:
    """
    Build and return a LangChain ChatOpenAI instance configured to use:
      - OPENAI_API_KEY (+ optional OPENAI_BASE_URL) for OpenRouter / OpenAI compatible access.

    Note: This function prioritizes the OpenAI/OpenRouter-style integration via ChatOpenAI.
    If you want native Together.ai HTTP usage, implement a custom client.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set. Set OPENAI_API_KEY (or configure Together AI separately).")

    llm_kwargs = {
        "model": LLM_MODEL,
        "temperature": TEMPERATURE,
        # ChatOpenAI in LangChain accepts openai_api_key and openai_api_base kwargs
        "openai_api_key": OPENAI_API_KEY,
    }
    if OPENAI_BASE_URL:
        llm_kwargs["openai_api_base"] = OPENAI_BASE_URL

    # Create ChatOpenAI instance
    return ChatOpenAI(**llm_kwargs)


def _extract_json_from_text(text: str) -> str | None:
    """
    Try to extract JSON substring from model output.
    - Remove code fences.
    - Find first {...} balanced substring (naive).
    Returns JSON string or None.
    """
    if not text:
        return None

    # Remove common code fences (```json ... ``` or ``` ... ```)
    fenced_removed = re.sub(r"```(?:json)?\s*", "", text).strip()
    fenced_removed = re.sub(r"\s*```$", "", fenced_removed).strip()

    # If entire cleaned text is JSON-ish, return it
    if fenced_removed.startswith("{") and fenced_removed.endswith("}"):
        return fenced_removed

    # Try to find first {...} block — simple approach
    start = fenced_removed.find("{")
    end = fenced_removed.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = fenced_removed[start:end + 1].strip()
        return candidate

    return None


def generate_reflection(journal: str, intention: str, dream: str, priorities: str) -> Dict[str, Any]:
    """
    Main function to call LLM and get structured reflection output.

    Returns a dict with either:
      - keys: reflection, dream_summary, mindset, strategy
    OR
      - keys: error, raw (when parsing or LLM call failed)
    """
    # Basic input normalization
    journal = journal or ""
    intention = intention or ""
    dream = dream or ""
    priorities = priorities or ""

    # Validate presence of API credentials
    if not (OPENAI_API_KEY or TOGETHER_API_KEY):
        return {
            "error": "No API key configured. Set OPENAI_API_KEY (for OpenRouter/OpenAI) or TOGETHER_API_KEY.",
            "raw": None
        }

    # Prefer OpenAI/OpenRouter via LangChain ChatOpenAI
    try:
        llm = _build_llm()
        chain = LLMChain(llm=llm, prompt=_PROMPT)

        # Run the chain (LangChain will return text)
        raw_output = chain.run({
            "journal": journal,
            "intention": intention,
            "dream": dream,
            "priorities": priorities
        })
    except Exception as exc:
        return {"error": "LLM call failed", "raw": str(exc)}

    # Clean & extract JSON from raw_output
    raw_text = (raw_output or "").strip()
    json_text = _extract_json_from_text(raw_text)

    if not json_text:
        # If no JSON found, return the raw output for debugging
        return {"error": "Could not find JSON in model output", "raw": raw_text}

    # Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return {"error": "JSON decode error", "raw": json_text}

    # Normalize and ensure keys exist
    result = {
        "reflection": data.get("reflection", "").strip() if isinstance(data.get("reflection", ""), str) else "",
        "dream_summary": data.get("dream_summary", "").strip() if isinstance(data.get("dream_summary", ""), str) else "",
        "mindset": data.get("mindset", "").strip() if isinstance(data.get("mindset", ""), str) else "",
        "strategy": data.get("strategy", "").strip() if isinstance(data.get("strategy", ""), str) else "",
    }

    return result


# Quick local test helper (won't run unless you execute this file directly)
if __name__ == "__main__":
    # This block tries to call the model only if API key exists; otherwise it prints sample output.
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not set — running local dry-run example.")
        sample = {
            "reflection": "You woke up with mixed feelings; notice the balance between excitement and worry.",
            "dream_summary": "Running dream suggests a desire to move forward but encountering friction.",
            "mindset": "Stay curious and patient. Use short focus sessions.",
            "strategy": "Start with the 30-minute focused work on priority #1, take short walk midday, batch small tasks after lunch."
        }
        print(json.dumps(sample, indent=2, ensure_ascii=False))
    else:
        print("Calling LLM (this requires network and valid API keys)...")
        example = generate_reflection(
            journal="I woke up uneasy but excited about starting a new task.",
            intention="Focus and complete core feature",
            dream="I was walking in a maze and couldn't find the door.",
            priorities="1. Finish coding, 2. Exercise, 3. Call mom"
        )
        print(json.dumps(example, indent=2, ensure_ascii=False))
