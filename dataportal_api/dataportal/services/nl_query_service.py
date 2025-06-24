import json
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
You are a strict JSON API assistant for a bioinformatics data portal.
Your job is to convert user requests into valid JSON objects for querying gene data.

When referencing a species, always return the acronym in case full scientific name is given
(e.g. BU for "Bacteroides uniformis" or ""B. uniformis, and "PV" for "Phocaeicola vulgatus" or "P. vulgatus).

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

def interpret_natural_language_query(user_query: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        print("GPT raw content:\n", repr(content))
        print("GPT returned:", content)  # Debug

        return json.loads(content)  # 👈 safe and correct
    except Exception as e:
        return {"error": str(e)}
