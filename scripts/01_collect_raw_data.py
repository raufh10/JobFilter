import sys
import logging
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.jobspy import JobSpyClient, fetch_jobs
from src.common import setup_logging

logger = logging.getLogger(__name__)

def main():
  # 1. Initialize logging system
  setup_logging()

  # 2. Initialize configuration
  config = JobSpyClient(
    search_term="Data Analyst",
    location="Indonesia",
    results_wanted=1000,
    hours_old=8760,
    remote_only=False
  )

  logger.info(f"🚀 Starting scrape for '{config.search_term}' in {config.location}...")

  try:
    # 3. Fetch the data
    results = fetch_jobs(config)
    logger.info(f"📥 Received {len(results.jobs)} raw results from JobSpy.")

    # 4. Filter results based on search term in title/description
    results.filter_by_search_term(config.search_term)
    logger.info(f"🔍 After filtering, {len(results.jobs)} jobs remain.")

    # 5. Define output path
    output_file = project_root / "data" / "raw_data.json"
    
    # 6. Save to JSON including the token counts for LLM readiness
    results.to_json(output_file, include_tokens=True)

    logger.info(f"✅ Successfully processed and saved data.")
    logger.info(f"📁 Path: {output_file.absolute()}")

  except Exception as e:
    logger.error(f"❌ An error occurred during collection: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
  main()
