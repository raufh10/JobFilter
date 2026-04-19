import json
import pandas as pd

from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import date

from jobspy import scrape_jobs
from src.jobspy.client import JobSpyClient
from src.tiktoken import BatchTokenCount, TokenCount, TokenCounter

class JobPost(BaseModel):
  id: str | None = None
  title: str
  company_name: str | None = None
  job_url: str
  location: Optional[str] = None
  description: str | None = None
  date_posted: date | None = None
  is_remote: bool | None = None

  # Indeed Specifics
  company_industry: str | None = None
  company_addresses: str | None = None
  company_num_employees: str | None = None
  company_revenue: str | None = None

class JobResponse(BaseModel):
  jobs: list[JobPost] = []

  @classmethod
  def from_dataframe(cls, df: pd.DataFrame):
    clean_df = df.where(pd.notnull(df), None)
    records = clean_df.to_dict(orient="records")
    return cls(jobs=[JobPost(**row) for row in records])

  def merge(self, other: "JobResponse"):
    """
    Merges another JobResponse into this one, removing duplicates based on job_url.
    """
    existing_urls = {job.job_url for job in self.jobs}
    for job in other.jobs:
      if job.job_url not in existing_urls:
        self.jobs.append(job)
        existing_urls.add(job.job_url)
    return self

  def filter_by_search_term(self, search_terms: List[str], strictness: str = "medium"):
    """
    Filters jobs based on strictness level. 
    Matches if ANY of the terms in search_terms are found.
    """
    strictness = strictness.lower()
    if strictness == "low":
      return self

    terms = [t.lower() for t in search_terms]
    filtered_jobs = []

    for job in self.jobs:
      title = (job.title or "").lower()
      desc = (job.description or "").lower()
      
      title_match = any(t in title for t in terms)
      desc_match = any(t in desc for t in terms)

      if strictness == "high":
        if title_match:
          filtered_jobs.append(job)
      elif strictness == "medium":
        if title_match or desc_match:
          filtered_jobs.append(job)

    self.jobs = filtered_jobs
    return self

  def to_dataframe(self) -> pd.DataFrame:
    """
    Export current state to DataFrame only when requested.
    """
    return pd.DataFrame([job.model_dump() for job in self.jobs])

  def get_token_counts(self, model_name: str = "gpt-5.4-nano") -> BatchTokenCount:
    """
    Calculates token counts for all job descriptions currently in the model.
    """
    counter = TokenCounter(model_name=model_name)
    descriptions = [job.description if job.description else "" for job in self.jobs]
    return counter.count_batch(descriptions)

  def to_json(self, file_path: str | Path, include_tokens: bool = False):
    """
    Saves the job data to JSON. 
    If include_tokens is True, it merges token metadata into the output.
    """

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    export_data = self.model_dump()
    
    if include_tokens:
      token_meta = self.get_token_counts()
      export_data["token_metadata"] = token_meta.model_dump()

    with open(path, 'w', encoding='utf-8') as f:
      json.dump(export_data, f, indent=2, default=str)

def fetch_jobs(config: JobSpyClient) -> JobResponse:
  """
  Iterates through all search terms in config, scrapes, merges, and filters.
  """
  final_response = JobResponse(jobs=[])

  # 1. Loop through each search term
  for term in config.search_term:
    scrape_kwargs = {
      "site_name": config.site_name,
      "search_term": term,
      "location": config.location,
      "results_wanted": config.results_wanted,
      "hours_old": config.hours_old,
      "country_indeed": config.country_indeed,
      "remote_only": config.remote_only,
    }

    if "linkedin" in [s.lower() for s in config.site_name]:
      scrape_kwargs["proxies"] = [config.proxy_url]

    # 2. Scrape and merge
    try:
      raw_jobs_df = scrape_jobs(**scrape_kwargs)
      current_batch = JobResponse.from_dataframe(raw_jobs_df)
      final_response.merge(current_batch)
    except Exception as e:
      print(f"Error scraping term '{term}': {e}")
      continue

  # 3. Final Filter using the full list of terms and strictness
  return final_response.filter_by_search_term(
    search_terms=config.search_term, 
    strictness=config.strictness
  )
