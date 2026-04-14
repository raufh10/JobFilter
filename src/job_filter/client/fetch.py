from jobspy import scrape_jobs
from client.models import validate_client_config
import pandas as pd

def fetch_jobs(config_path: str = "client.json") -> pd.DataFrame:
  config = validate_client_config(config_path)

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
