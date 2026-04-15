import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.jobspy import JobSpyClient, fetch_jobs

def main():

  # 1. Initialize your configuration
  config = JobSpyClient(
    search_term="Software Engineer",
    location="Jakarta",
    results_wanted=10,
    hours_old=72,
    remote_only=False
  )

  print(f"🚀 Starting scrape for '{config.search_term}' in {config.location}...")

  try:
    # 2. Fetch the data
    results = fetch_jobs(config)

     # 3. Define output path (saving to project_root/data/)
     output_file = project_root / "data" / "raw_data.json"
     results.to_json(output_file)

     print(f"✅ Successfully collected {len(results.jobs)} jobs.")
     print(f"📁 Data saved to: {output_file.absolute()}")

  except Exception as e:
    print(f"❌ An error occurred during collection: {e}")
    raise e

if __name__ == "__main__":
  main()
