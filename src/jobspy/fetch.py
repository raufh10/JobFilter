from jobspy import scrape_jobs
from job_filter.packages.common.src.models import JobFilterConfig, JobResponse
#from common import JobFilterConfig, JobResponse

def fetch_jobs(config: JobFilterConfig) -> JobResponse:
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
