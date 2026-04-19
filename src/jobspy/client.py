from enum import Enum
from pydantic import BaseModel, model_validator
from typing import Optional
from src.common import settings

class StrictnessLevel(str, Enum):
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"

class JobSpyClient(BaseModel):
  site_name: list[str] = ["indeed"]
  search_term: str
  location: str
  results_wanted: int = 20
  hours_old: Optional[int] = 48
  country_indeed: str = "Indonesia"
  remote_only: Optional[bool] = False
  proxy_url: Optional[str] = settings.proxy_url
  strictness: StrictnessLevel = StrictnessLevel.MEDIUM

  @model_validator(mode="after")
  def check_linkedin_proxy(self) -> "JobSpyClient":
    """
    Ensures that if LinkedIn is being scraped, a proxy URL is configured.
    """
    if "linkedin" in [s.lower() for s in self.site_name]:
      if not self.proxy_url:
        raise ValueError(
          "A proxy_url must be configured in settings to scrape LinkedIn."
        )
    return self
