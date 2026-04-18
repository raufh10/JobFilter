import re
import httpx
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

def get_openai_compatible_schema(model) -> dict:
  """
  Recursively ensures all objects have every property key in 'required'
  and strips 'default' keys — both required for OpenAI strict json_schema.
  """
  def fix(obj: dict) -> dict:
    if isinstance(obj, dict):
      obj.pop("default", None)
      if "properties" in obj:
        obj["required"] = list(obj["properties"].keys())
      for value in obj.values():
        fix(value)
    elif isinstance(obj, list):
      for item in obj:
        fix(item)
    return obj

  return fix(model.model_json_schema())

def generate_structured_response(llm: LLMClient, user_input: str):
  """
  Cleans input and generates a structured response using responses.parse API.
  """
  cleaned_input = clean_text(user_input)

  if not cleaned_input:
    return None

  json_schema = get_openai_compatible_schema(llm.format_schema)

  try:
    response = llm.client.post(
      llm.base_url,
      json={
        "model": llm.model,
        "input": [
          {"role": "system", "content": llm.system_prompt},
          {"role": "user", "content": cleaned_input},
        ],
        "text": {
          "format": {
            "type": "json_schema",
            "name": llm.name,
            "schema": json_schema,
            "strict": True
          }
        },
        "prompt_cache_key": llm.prompt_key,
        "prompt_cache_retention": "in_memory",
        "service_tier": "flex"
      }
    )
    response.raise_for_status()
    
  except httpx.HTTPStatusError as e:
    error_details = e.response.json() if "application/json" in e.response.headers.get("Content-Type", "") else e.response.text
    print(f"\n[!] OpenAI API Error {e.response.status_code}:")
    print(f"Details: {error_details}")
    raise
    
  output_text = response.json().get("output_text")
  return llm.format_schema.model_validate_json(output_text)
