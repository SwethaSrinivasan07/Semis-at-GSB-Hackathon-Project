import os
import json
import re

import anthropic


def _client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_substitutes(part: dict, risk_flags: dict) -> list[dict]:
    issues = [f"{dim} ({level})" for dim, level in risk_flags.items() if level in ("RED", "YELLOW")]

    prompt = f"""A semiconductor procurement engineer needs substitute parts for a flagged component.

Original part:
- MPN: {part.get("mpn", "Unknown")}
- Manufacturer: {part.get("manufacturer", "Unknown")}
- Description: {part.get("description", "Unknown")}
- Risk issues: {", ".join(issues)}

Suggest 3-4 substitute parts that address these risks. For each provide:
- mpn: exact part number
- manufacturer: manufacturer name
- compatibility_grade: one of ["Drop-in", "Minor rework", "Redesign required"]
- key_differences: 1-2 sentences on relevant spec differences
- why_better: how this substitute resolves the supply chain risk
- estimated_availability: rough stock/lead time expectation

Return ONLY a valid JSON array, no prose:
[{{"mpn": "...", "manufacturer": "...", "compatibility_grade": "Drop-in", "key_differences": "...", "why_better": "...", "estimated_availability": "..."}}]"""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []
