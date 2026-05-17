import os
import io
import json
import re

import anthropic
import pandas as pd


def _client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def parse_bom_file(file_bytes: bytes, filename: str) -> list[dict]:
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))

    bom_text = df.to_string(index=False)

    prompt = f"""Parse this Bill of Materials and extract structured data for every component row.

BOM:
{bom_text}

For each row return:
- mpn: exact manufacturer part number as written
- manufacturer: component manufacturer name
- quantity: integer quantity required
- description: short component description
- reference_designators: reference designators if present, else empty string

Return ONLY a valid JSON array, no prose. Example:
[{{"mpn": "STM32F103C8T6", "manufacturer": "STMicroelectronics", "quantity": 10, "description": "ARM Cortex-M3 MCU", "reference_designators": "U1-U10"}}]"""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []
