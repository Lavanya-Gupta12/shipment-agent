import json
import os
import re

import ollama

MODEL = os.environ.get("AGENT_MODEL", "qwen2.5-coder:7b")


def ask_llm(system_prompt: str, user_prompt: str) -> dict:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.1},
    )
    raw = response["message"]["content"].strip()
    raw = re.sub(r"^```(json)?", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip()).strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse LLM response as JSON:\n{raw}") from e
