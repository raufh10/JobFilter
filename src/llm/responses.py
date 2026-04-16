import re
from src.llm.client import LLMClient

def clean_text(text: str) -> str:
  """
  Cleans raw text using regex:
  1. Removes HTML tags.
  2. Replaces multiple newlines/spaces with a single space.
  3. Strips leading/trailing whitespace.
  """

  if not text:
    return ""
  text = re.sub(r'<[^>]*>', ' ', text)
  text = re.sub(r'\s+', ' ', text)
  return text.strip()

def generate_structured_response(llm: LLMClient, user_input: str):
  """
  Cleans input and generates a structured response using responses.parse API.
  """

  cleaned_input = clean_text(user_input)
  
  if not cleaned_input:
    return None

  json_schema = llm.format_schema.model_json_schema()

  response = llm.client.responses.create(
    model=llm.model,
    input=[
      {"role": "system", "content": llm.system_prompt},
      {"role": "user", "content": cleaned_input},
    ],
    text={
      "format": {
        "type": "json_schema",
        "name": "llm.name",
        "schema": json_schema,
        "strict": True
      }
    },
    prompt_cache_key=llm.prompt_key,
    prompt_cache_retention="in-memory",
    service_tier="flex"
  )

  return llm.format_schema.model_validate_json(response.output_text)
