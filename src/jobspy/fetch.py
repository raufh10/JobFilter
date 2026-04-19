import json
import pandas as pd

from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Any
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
    """
    Creates a JobResponse directly from the jobspy DataFrame
    """
    clean_df = df.where(pd.notnull(df), None)
    records = clean_df.to_dict(orient="records")
    
    return cls(jobs=[JobPost(**row) for row in records])

  def filter_by_search_term(self, search_term: str, strictness: str = "medium"):
    """
    Filters jobs based on strictness level:
    - high: Title must match search term.
    - medium: Title OR Description must match.
    - low: No filtering applied.
    """
    term = search_term.lower()
    strictness = strictness.lower()

    if strictness == "low":
      return self

    filtered_jobs = []
    for job in self.jobs:
      title_match = job.title and term in job.title.lower()
      desc_match = job.description and term in job.description.lower()

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
  Scrapes jobs and applies filtering based on config strictness.
  """
  # Define base arguments
  scrape_kwargs = {
    "site_name": config.site_name,
    "search_term": config.search_term,
    "location": config.location,
    "results_wanted": config.results_wanted,
    "hours_old": config.hours_old,
    "country_indeed": config.country_indeed,
    "remote_only": config.remote_only,
  }

  # Proxy logic for LinkedIn
  if "linkedin" in [s.lower() for s in config.site_name]:
    scrape_kwargs["proxies"] = [config.proxy_url]

  raw_jobs_df = scrape_jobs(**scrape_kwargs)
  
  response = JobResponse.from_dataframe(raw_jobs_df)
  return response.filter_by_search_term(
    search_term=config.search_term, 
    strictness=config.strictness
  )
