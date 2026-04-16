import sys
import json
import re
import logging

from pathlib import Path
from typing import List, Union, Literal, Type
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.llm import LLMClient, generate_structured_response
from src.common import setup_logging, settings

# --- 1. Schemas ---

class SkillExtraction(BaseModel):
  model_config = ConfigDict(extra='forbid')

  languages: list[str] = Field(description="Programming languages like Python, R, SQL, Julia.")
  tools: list[str] = Field(description="Software/platforms like Tableau, PowerBI, Docker, Git, Airflow.")
  frameworks: list[str] = Field(description="Libraries or frameworks like PyTorch, TensorFlow, Scikit-learn, Spark.")
  techniques: list[str] = Field(description="Methodologies like A/B Testing, Regression, Deep Learning, ETL.")
  cloud_platforms: list[str] = Field(description="Cloud services like AWS, GCP, Azure and specific services like S3, BigQuery.")

class SkillExtractionValidator(BaseModel):
  model_config = ConfigDict(extra='forbid')
  is_valid: bool = Field(..., description="True if lists are correctly formatted and categorized.")
  corrections: List[str] = Field(default_factory=list, description="Specific issues to fix.")

# --- 2. Prompts ---

GEN_SYSTEM_PROMPT = """
You are a Senior NLP Engineer. Convert raw skills into spaCy EntityRuler patterns.
- Use Strings for simple exact matches (e.g., 'Python').
- Use Token Patterns (List of Dicts) for multi-word or hyphenated skills (e.g., 'Scikit-learn').
- Use 'LOWER' for case-insensitivity and 'OP': '?' for optional punctuation.
""".strip()

VAL_SYSTEM_PROMPT = """
You are an NLP QA Auditor. Check spaCy patterns for:
1. Logic: Multi-word skills MUST be token lists, not single strings.
2. Schema: Only use allowed spaCy keys (LOWER, LEMMA, OP, etc.).
3. Accuracy: Ensure the label matches the skill category.
If invalid, list specific technical corrections.
""".strip()

# --- 3. Core Logic ---

logger = logging.getLogger(__name__)

def refinement_loop(gen_llm: LLMClient, val_llm: LLMClient, raw_skills_text: str):
  """Circular refinement: Generate -> Validate -> Correct."""
  max_retries = 2
  attempt = 0
  
  # Step 1: Initial Generation
  logger.info("🎨 Generating initial patterns...")
  current_output = generate_structured_response(gen_llm, raw_skills_text)
  print(current_output.model_dump_json())
  from sys import exit
  exit()

  while attempt < max_retries:
    # Step 2: Validation
    val_input = f"Skills: {raw_skills_text}\nGenerated: {current_output.model_dump_json()}"
    validation = generate_structured_response(val_llm, val_input)

    if validation.is_valid:
      logger.info(f"✅ Validation passed on attempt {attempt + 1}")
      return current_output

    # Step 3: Feedback
    attempt += 1
    logger.warning(f"🔄 Refinement attempt {attempt}: {validation.corrections}")
    feedback_input = (
      f"Original Skills: {raw_skills_text}\n"
      f"Previous Patterns: {current_output.model_dump_json()}\n"
      f"CORRECTIONS NEEDED: {json.dumps(validation.corrections)}"
    )
    current_output = generate_structured_response(gen_llm, feedback_input)

  logger.error("🛑 Max retries reached. Returning best effort.")
  return current_output

def main():
  setup_logging()
  input_file = project_root / "data" / "raw_skills.json"
  output_file = project_root / "data" / "skills.jsonl"

  if not input_file.exists():
    logger.error("No input data found.")
    return

  with open(input_file, "r") as f:
    raw_data = json.load(f)

  # Prepare Clients
  gen_llm = LLMClient(
    api_key=settings.openai_api_key,
    model="gpt-5.4-mini",
    name="pattern_gen",
    system_prompt=GEN_SYSTEM_PROMPT,
    format_schema=SkillExtraction,
    prompt_key="p_gen"
  )

  val_llm = LLMClient(
    api_key=settings.openai_api_key,
    model="gpt-5.4",
    name="pattern_val",
    system_prompt=VAL_SYSTEM_PROMPT,
    format_schema=SkillExtractionValidator,
    prompt_key="p_val"
  )

  raw_skills = json.dumps(raw_data.get("data", [])[:2])  
  final_patterns = refinement_loop(gen_llm, val_llm, raw_skills)

  with open(output_file, "w") as f:
    for p in final_patterns.patterns:
      f.write(json.dumps(p.model_dump(exclude_none=True)) + "\n")

  logger.info(f"🚀 Successfully saved patterns to {output_file}")

if __name__ == "__main__":
  main()
