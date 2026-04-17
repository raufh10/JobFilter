import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

# --- Path Fixing ---
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.jobspy.fetch import fetch_jobs, JobResponse
from src.nlp_utils.matcher import SpacyMatcher
from src.nlp_utils.patterns import EntityPatterns

# Import CLI specific models
from apps.cli.roles import Role, Roles
from apps.cli.resume import Resume

console = Console()

class JobScorer:
  def __init__(self, role: Role, resume: Resume, min_score: float = 0.0):
    self.role = role
    self.resume = resume
    self.min_score = min_score
    self.matcher = self._setup_matcher()
    
    # Flatten resume skills into a unique lowercase set
    self.resume_skills = set(
      s.lower() for s in (
        self.resume.languages + 
        self.resume.tools + 
        self.resume.frameworks + 
        self.resume.cloud_platforms
      )
    )

  def _setup_matcher(self) -> SpacyMatcher:
    """Initializes SpacyMatcher and loads the role's patterns."""
    matcher = SpacyMatcher()
    
    try:
      patterns = EntityPatterns.from_json(self.role.spacy_path)
      matcher.add_rules(patterns)
    except Exception as e:
      console.print(f"[yellow]Warning: Could not load patterns: {e}[/yellow]")
      
    return matcher

  def run(self):
    """Main execution flow: Fetch -> Extract -> Score -> Filter -> Display."""
    response: JobResponse = fetch_jobs(self.role.client)
    
    if not response.jobs:
      console.print("[yellow]No jobs found matching the criteria.[/yellow]")
      return

    scored_results = []
    for job in response.jobs:
      extracted = self.matcher.process_text(job.description or "")
      found_skills = {e.text.lower() for e in extracted}
      
      matches = found_skills.intersection(self.resume_skills)
      
      score = 0.0
      if found_skills:
        score = (len(matches) / len(found_skills)) * 100

      # Apply the score threshold filter
      if score >= self.min_score:
        scored_results.append({
          "title": job.title,
          "company": job.company_name or "N/A",
          "score": round(score, 1),
          "matches": list(matches),
          "url": job.job_url
        })

    if not scored_results:
      console.print(f"[yellow]No jobs met the minimum score of {self.min_score}%.[/yellow]")
      return

    scored_results.sort(key=lambda x: x['score'], reverse=True)
    self._display_table(scored_results)

  def _display_table(self, results: list):
    """Renders results in a formatted Rich table."""
    table = Table(
      title=f"Matched Jobs for {self.role.name} (Min Score: {self.min_score}%)", 
      header_style="bold magenta"
    )

    table.add_column("Score", justify="right", style="green")
    table.add_column("Job Title", style="cyan")
    table.add_column("Company", style="white")
    table.add_column("Top Matches", style="dim")

    for item in results[:15]:
      match_str = ", ".join(item['matches'][:5])
      table.add_row(
        f"{item['score']}%",
        item['title'],
        item['company'],
        match_str if match_str else "[dim]no matches[/dim]"
      )

    console.print(table)

def run_fetch(role_name: str, min_score: float = 50.0):
  """CLI entry point to execute the fetch command."""
  roles_store = Roles.load()
  role = roles_store.get_role(role_name)
  resume = Resume.load()

  if not role:
    console.print(f"[red]Error: Role '{role_name}' not found.[/red]")
    return

  scorer = JobScorer(role, resume, min_score=min_score)
  scorer.run()
