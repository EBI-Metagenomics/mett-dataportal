import os
from typing import Any

from openai import OpenAI

from dataportal.schema.nl_schemas import METT_GENE_QUERY_SCHEMA
from dataportal.schema.gene_schemas import GeneQuery

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a strict JSON API assistant for a bioinformatics data portal.
Your job is to convert user requests into valid JSON objects for querying gene data.

When referencing a species, always return the acronym in case full scientific name is given
(e.g. BU for "Bacteroides uniformis" or "B. uniformis", and PV for "Phocaeicola vulgatus" or "P. vulgatus").

⚠️ Output ONLY a valid JSON object. Do not include any explanation, prefix, or suffix.
Do NOT say anything like "Sure!" or "Here is your output".

Supported JSON fields: species, essentiality, amr, function, cog_category.

Example:
User: Show essential genes in PV not involved in AMR
Output:
{
  "species": "PV",
  "essentiality": "essential",
  "amr": true
}
"""

def interpret_natural_language_query(user_query: str) -> dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            tools=[{
                "type": "function",
                "function": METT_GENE_QUERY_SCHEMA
            }],
            tool_choice="auto",
            temperature=0
        )

        # Debug: Print raw response for tracing
        print("GPT raw response:\n", response)

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return {"error": "No tool call returned by GPT. Check prompt or query clarity."}

        arguments = tool_calls[0].function.arguments
        print("Parsed arguments from GPT:\n", arguments)

        # Optionally validate using GeneQuery for type safety
        parsed_query = GeneQuery.model_validate_json(arguments)

        return parsed_query.model_dump(exclude_none=True)

    except Exception as e:
        return {"error": str(e)}
