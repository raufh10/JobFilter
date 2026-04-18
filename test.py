import re
import httpx
import tiktoken
import pandas as pd
from typing import List
from pydantic import BaseModel, Field
from jobspy import scrape_jobs

from src.common import settings
from src.llm.client import LLMClient
from src.llm.responses import generate_structured_response

system_prompt = """
You are a technical recruiting assistant specializing in the Jakarta tech market. 
Your task is to identify sentence indices that contain CORE information.

CORE INFORMATION includes:
- Technical skills (Python, Go, React, SQL, etc.)
- Years of experience or education requirements.
- Daily responsibilities (Building APIs, managing teams, designing UI).
- Soft skills explicitly required for the role.

EXCLUDE:
- Company history/vision ("We were founded in 2010...").
- Benefits ("Free lunch", "Insurance", "Gym").
- Generic statements ("We are a great place to work").
- Legal boilerplate ("Equal opportunity employer").

Return the indices in the order they appear in the text.
"""

class RelevantIndices(BaseModel):
  indices: List[int] = Field(description="List of sentence indices relevant to job requirements or responsibilities.")

def filter_jobs(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
  term = search_term.lower()
  mask = (
    df['title'].str.lower().str.contains(term, na=False) | 
    df['description'].str.lower().str.contains(term, na=False)
  )
  return df[mask].copy()

def split_sentences(text: str) -> List[str]:
  if not text: return []
  sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if s.strip()]
  return sentences

def process_relevance(llm: LLMClient, description: str) -> str:
  sentences = split_sentences(description)
  if not sentences: return ""
  
  indexed_input = "\n".join([f"[{i}] {s}" for i, s in enumerate(sentences)])
  
  try:
    result = generate_structured_response(llm, indexed_input)
    filtered = [sentences[i] for i in result.indices if i < len(sentences)]
    return " ".join(filtered)
  except Exception as e:
    print(f"Error: {e}")
    return description

def main(roles: list[str]):

  # Initialize LLM Client
  llm = LLMClient(
    api_key=settings.openai_api_key,
    model="gpt-5.4-nano",
    name="RelevanceFilter",
    system_prompt=system_prompt,
    format_schema=RelevantIndices,
    prompt_key="jakarta_job_refiner"
  )

  try:
    encoding = tiktoken.encoding_for_model("gpt-5.4-nano")
  except KeyError:
    encoding = tiktoken.get_encoding("o200k_base")

  all_jobs = []

  for role in roles:
    print(f"--- Scraping Indeed Jakarta for: {role} ---")
    jobs_df = scrape_jobs(
      site_name=["indeed"],
      search_term=role,
      location="Jakarta, Indonesia",
      results_wanted=500,
      hours_old=2160, 
      country_indeed='indonesia',
    )

    filtered_jobs = filter_jobs(jobs_df, role)

    if not filtered_jobs.empty:
      print(f"Refining {len(filtered_jobs)} job descriptions...")
      
      # Process each description: Split -> LLM Filter Indices -> Reassemble
      filtered_jobs['refined_description'] = filtered_jobs['description'].apply(
        lambda x: process_relevance(llm, x)
      )      

      # Calculate tokens for the refined version
      filtered_jobs['description_tokens'] = filtered_jobs['refined_description'].apply(
        lambda x: len(encoding.encode(x)) if x else 0
      )

      all_jobs.append(filtered_jobs)
    else:
      print(f"No results for '{role}'.")

  # 4. Final Reporting
  if all_jobs:
    general_df = pd.concat(all_jobs).drop_duplicates(subset=['job_url'])

    print("\n" + "="*40)
    print("GENERAL SUMMARY (REFINED VIA GPT-5.4-NANO)")
    print("="*40)
    print(f"Total Unique Jobs: {len(general_df)}")
    print(f"Total Refined Tokens: {general_df['description_tokens'].sum()}")
    print(f"Average Refined Tokens: {general_df['description_tokens'].mean():.1f}")

    print("\nTop 5 Most Content-Heavy Roles (Refined):")
    print(general_df[['company', 'title', 'description_tokens']].sort_values(by='description_tokens', ascending=False).head(5).to_string(index=False))
  else:
    print("No jobs found.")

if __name__ == "__main__":
  target_roles = ["software engineer", "data engineer", "devops", "data analyst", "ai engineer"]
  target_roles = ["ai engineer"]
  main(roles=target_roles)
