import json
from pathlib import Path

from pydantic import BaseModel
from typing import Optional
from datetime import date

from jobspy import scrape_jobs

from src.jobspy.client import JobSpyClient

class JobPost(BaseModel):
  id: str | None = None
  title: str
  company_name: str | None
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

  def to_json(self, file_path: str | Path):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_data = self.model_dump_json(indent=2)
    path.write_text(json_data, encoding="utf-8")

def fetch_jobs(config: JobSpyClient) -> JobResponse:
  """
  Scrapes Indeed jobs and returns a JobResponse object.
  """
  jobs = scrape_jobs(
    site_name=config.site_name,
    search_term=config.search_term,
    location=config.location,
    results_wanted=config.results_wanted,
    hours_old=config.hours_old,
    country_indeed=config.country_indeed,
    remote_only=config.remote_only,
  )

  return jobs
