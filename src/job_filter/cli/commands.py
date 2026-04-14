import re
import json
import typer
from pathlib import Path
from client.fetch import fetch_jobs
from client.models import validate_client_config

app = typer.Typer()

@app.command()
def fetch():
  """Fetch jobs and print to terminal."""
  try:
    config = validate_client_config()
    jobs = fetch_jobs()

    print(f"\nFound {len(jobs)} jobs\n")
    for _, job in jobs.iterrows():

      raw_desc = job.get('description', 'N/A')
      clean_desc = re.sub(r'\\-|\\+|\\\*|\\#', lambda m: m.group()[1:], raw_desc)
      clean_desc = re.sub(r'\n{3,}', '\n\n', clean_desc).strip()

      print(f"Title:    {job.get('title', 'N/A')}")
      print(f"Company:  {job.get('company', 'N/A')}")
      print(f"Location: {job.get('location', 'N/A')}")
      print(f"Description:\n{clean_desc}")
      print(f"URL:      {job.get('job_url', 'N/A')}")
      print("-" * 50)
  except FileNotFoundError:
    print("No client.json found. Run `job_filter config create` first.")


@app.command()
def create():
  """Create a new client.json interactively."""
  config_path = Path("client.json")
  if config_path.exists():
    overwrite = typer.confirm("client.json already exists. Overwrite?")
    if not overwrite:
      raise typer.Abort()

  site_name = typer.prompt("Site names (comma separated, e.g. indeed,linkedin)").split(",")
  search_term = typer.prompt("Search term")
  location = typer.prompt("Location")
  results_wanted = typer.prompt("Results wanted", default=20)
  hours_old = typer.prompt("Hours old (leave blank to skip)", default="")
  country_indeed = typer.prompt("Country for Indeed (leave blank to skip)", default="")
  remote_only = typer.confirm("Remote only?", default=False)

  config = {
    "site_name": [s.strip() for s in site_name],
    "search_term": search_term,
    "location": location,
    "results_wanted": int(results_wanted),
    "hours_old": int(hours_old) if hours_old else None,
    "country_indeed": country_indeed if country_indeed else None,
    "remote_only": remote_only,
  }

  with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

  print("\nclient.json created successfully!")


@app.command()
def adjust():
  """Adjust existing client.json interactively."""
  config_path = Path("client.json")
  if not config_path.exists():
    print("No client.json found. Run `job_filter config create` first.")
    raise typer.Abort()

  with open(config_path) as f:
    current = json.load(f)

  print("\nCurrent config (press Enter to keep existing value):\n")

  site_name = typer.prompt("Site names (comma separated)", default=",".join(current["site_name"])).split(",")
  search_term = typer.prompt("Search term", default=current["search_term"])
  location = typer.prompt("Location", default=current["location"])
  results_wanted = typer.prompt("Results wanted", default=str(current["results_wanted"]))
  hours_old = typer.prompt("Hours old", default=str(current.get("hours_old") or ""))
  country_indeed = typer.prompt("Country for Indeed", default=str(current.get("country_indeed") or ""))
  remote_only = typer.confirm("Remote only?", default=current.get("remote_only", False))

  config = {
    "site_name": [s.strip() for s in site_name],
    "search_term": search_term,
    "location": location,
    "results_wanted": int(results_wanted),
    "hours_old": int(hours_old) if hours_old else None,
    "country_indeed": country_indeed if country_indeed else None,
    "remote_only": remote_only,
  }

  with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

  print("\nclient.json updated successfully!")
