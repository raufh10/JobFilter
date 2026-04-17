import sys
import json
import logging

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.llm import LLMClient, generate_structured_response
from src.common import setup_logging, settings
from src.tiktoken import TokenCounter
from scripts.utils import get_file

# 1. Skill Extraction Schema
class SkillExtraction(BaseModel):
  model_config = ConfigDict(extra='forbid')

  languages: list[str] = Field(description="Programming languages like Python, R, SQL, Julia.")
  tools: list[str] = Field(description="Software/platforms like Tableau, PowerBI, Docker, Git, Airflow.")
  frameworks: list[str] = Field(description="Libraries or frameworks like PyTorch, TensorFlow, Scikit-learn, Spark.")
  techniques: list[str] = Field(description="Methodologies like A/B Testing, Regression, Deep Learning, ETL.")
  cloud_platforms: list[str] = Field(description="Cloud services like AWS, GCP, Azure and specific services like S3, BigQuery.")

# 2. Model & Prompt

MODEL = "gpt-5.4-nano"
NAME = "raw_skills"
PROMPT_KEY = "raw_skills-v1"

SYSTEM_PROMPT = """
You are an expert Technical Recruiter.
Your task is to parse job descriptions and extract technical requirements into a structured format.

Guidelines:
- Normalize terms: e.g., 'Scikit Learn' and 'sklearn' should both be 'Scikit-learn'.
- Only include technical items found in the text. If a category has no items, return an empty list.
""".strip()

logger = logging.getLogger(__name__)

def process_single_job(job: dict, llm: LLMClient) -> dict | None:
  """Helper function to process one job (used by ThreadPoolExecutor)."""
  description = job.get("description")
  job_id = job.get("id")
  title = job.get("title")

  if not description:
    return None

  try:
    logger.info(f"  - Processing: {title}")
    skills_data = generate_structured_response(llm, description)
    
    return {
      "job_id": job_id,
      "title": title,
      "skills": skills_data.model_dump()
    }
  except Exception as e:
    logger.error(f"  ⚠️ Failed job {job_id}: {e}")
    return None

def main():
  setup_logging()
  
  input_file = project_root / "data" / "raw_data.json"
  output_file = project_root / "data" / "raw_skills.json"

  if not input_file.exists():
    logger.error(f"❌ Input file not found: {input_file}")
    return

  with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)
    jobs = data.get("jobs", [])

  llm = LLMClient(
    api_key=settings.openai_api_key, 
    model=MODEL,
    name=NAME,
    system_prompt=SYSTEM_PROMPT,
    format_schema=SkillExtraction,
    prompt_key=PROMPT_KEY
  )

  logger.info(f"🧠 Extracting data for {len(jobs)} jobs using 8 threads...")

  extracted_results = []
  with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(process_single_job, job, llm) for job in jobs]
    for future in futures:
      result = future.result()
      if result:
        extracted_results.append(result)

  # 3. Tiktoken Integration for JSON payload calculation
  logger.info("📊 Calculating final JSON token count...")  
  final_json_str = json.dumps(extracted_results, indent=2)
  
  counter = TokenCounter(model_name=MODEL)
  token_info = counter.count_tokens(final_json_str)
  
  final_output = {
    "metadata": {
      "job_count": len(extracted_results),
      "json_token_count": token_info.token_count,
      "model_used_for_count": MODEL
    },
    "data": extracted_results
  }

  # 4. Save Results
  output_file.parent.mkdir(parents=True, exist_ok=True)
  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2)

  logger.info(f"✅ Extraction complete. Tokens in JSON: {token_info.token_count}")
  logger.info(f"📁 Results saved to {output_file}")

if __name__ == "__main__":
  main()
