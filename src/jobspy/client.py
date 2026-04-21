from enum import Enum
from pydantic import BaseModel
from typing import Optional, List

class StrictnessLevel(str, Enum):
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"

class JobSpyClient(BaseModel):
  site_name: List[str] = ["indeed"]
  search_term: List[str]
  location: str
  results_wanted: int = 20
  hours_old: Optional[int] = 48
  country_indeed: str = "Indonesia"
  remote_only: Optional[bool] = False
  strictness: StrictnessLevel = StrictnessLevel.MEDIUM
