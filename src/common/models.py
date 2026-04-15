from pydantic import BaseModel
from typing import Optional
from datetime import date

class JobFilterConfig(BaseModel):
  site_name: list[str] = ["indeed"]
  search_term: str
  location: str
  results_wanted: int = 20
  hours_old: Optional[int] = 48
  country_indeed: str = "Indonesia"
  remote_only: Optional[bool] = False

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

