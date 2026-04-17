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
from scripts.utils import get_file

# --- 1. Schemas ---

class SkillExtraction(BaseModel):
  model_config = ConfigDict(extra='forbid')

  languages: list[str] = Field(description="Programming languages like Python, R, SQL, Julia.")
  tools: list[str] = Field(description="Software/platforms like Tableau, PowerBI, Docker, Git, Airflow.")
  frameworks: list[str] = Field(description="Libraries or frameworks like PyTorch, TensorFlow, Scikit-learn, Spark.")
  cloud_platforms: list[str] = Field(description="Cloud services like AWS, GCP, Azure and specific services like S3, BigQuery.")

class SkillExtractionValidator(BaseModel):
  model_config = ConfigDict(extra='forbid')
  is_valid: bool = Field(..., description="True if lists are correctly formatted and categorized.")
  corrections: List[str] = Field(default_factory=list, description="Specific issues to fix.")

# --- 2. Prompts ---

"""
techniques: list[str] = Field(description="Methodologies like A/B Testing, Regression, Deep Learning, ETL.")
- techniques: Methodologies and analytical approaches (A/B Testing, Regression, ETL, Deep Learning, Feature Engineering)
"""

GEN_SYSTEM_PROMPT = """
You are a Senior Technical Recruiter.
Consolidate technical skills from text and categorize them strictly.

CATEGORIES:
- languages: Programming/query languages only (Python, R, SQL, Scala, Julia, Bash)
- tools: Named software, platforms, or products (Tableau, PowerBI, Docker, Git, Airflow, Jira, Looker)
- frameworks: Libraries and ML/data frameworks (PyTorch, TensorFlow, Scikit-learn, Spark, Pandas, dbt)
- cloud_platforms: Cloud providers AND their specific services (AWS, GCP, Azure, S3, BigQuery, Redshift, Vertex AI)

RULES:
1. Extract only explicitly mentioned skills — never infer or hallucinate.
2. Normalize names: use canonical forms (e.g. 'PyTorch' not 'pytorch', 'scikit-learn' not 'sklearn').
3. Do NOT put the same skill in multiple categories.
4. Do NOT include soft skills, job titles, or domain knowledge (e.g. 'communication', 'finance', 'leadership').
5. Do NOT include vague phrases (e.g. 'data-driven', 'best practices', 'strong analytical skills').
6. If a category has no skills in the text, return an empty list — never omit the key.
""".strip()

VAL_SYSTEM_PROMPT = """
You are a strict NLP QA Auditor validating list of skills.

CHECK FOR:
1. Miscategorization: Is each skill in the correct category?
   - SQL → languages, NOT tools
   - Docker → tools, NOT frameworks
   - Scikit-learn → frameworks, NOT tools
   - AWS → cloud_platforms, NOT tools

2. Hallucination: Are all skills explicitly present in the original text?
   Flag any skill not found verbatim or by clear implication.

3. Noise: Flag any non-technical entries such as:
   - Soft skills (e.g. 'communication', 'teamwork')
   - Vague phrases (e.g. 'data-driven solutions', 'best practices')
   - Job responsibilities (e.g. 'build dashboards', 'manage pipelines')

4. Duplicates: Flag skills appearing in more than one category list.

5. Normalization: Flag non-canonical names (e.g. 'sklearn' should be 'scikit-learn', 'tf' should be 'TensorFlow').

Respond with is_valid=True only if ALL checks pass with zero issues.
If invalid, list each issue as a specific, actionable correction string.
""".strip()

# --- 3. Core Logic ---

logger = logging.getLogger(__name__)

def refinement_loop(gen_llm: LLMClient, val_llm: LLMClient, raw_skills_text: str):
  """Circular refinement: Generate -> Validate -> Correct."""
  max_retries = 3
  attempt = 0
  
  # Step 1: Initial Generation
  logger.info("🎨 Generating initial patterns...")
  current_output = generate_structured_response(gen_llm, raw_skills_text)

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

def main(
  input_path_override: dict = {
    "path": None,
    "filename": "raw_skills.json"
  },
  output_path_override: dict = {
    "path": None,
    "filename": "skills.json"
  }
):

  setup_logging()
  input_file = get_file(project_root, input_path_override)
  output_file = get_file(project_root, output_path_override)

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

  raw_skills = json.dumps(raw_data.get("data", []))  
  final_patterns = refinement_loop(gen_llm, val_llm, raw_skills)

  final_data = final_patterns.model_dump()
  output_file.parent.mkdir(parents=True, exist_ok=True)
  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)

  logger.info(f"🚀 Successfully saved validated skills to {output_file}")

if __name__ == "__main__":
  main()
