from pydantic import BaseModel
from typing import Optional

class JobSpyClient(BaseModel):
  site_name: list[str] = ["indeed"]
  search_term: str
  location: str
  results_wanted: int = 20
  hours_old: Optional[int] = 48
  country_indeed: str = "Indonesia"
  remote_only: Optional[bool] = False
