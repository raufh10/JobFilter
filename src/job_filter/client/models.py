from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

class JobFilterConfig(BaseModel):
  site_name: list[str]
  search_term: str
  location: str
  results_wanted: int = 20
  hours_old: Optional[int] = None
  country_indeed: Optional[str] = None
  remote_only: Optional[bool] = False

def read_client_config(path: str = "client.json") -> dict:
  config_path = Path(path)
  if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {path}")
  with open(config_path) as f:
    return json.load(f)

def validate_client_config(path: str = "client.json") -> JobFilterConfig:
  data = read_client_config(path)
  return JobFilterConfig(**data)
