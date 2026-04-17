import sys
import typer
from typing import Optional
from rich.console import Console

# --- Path Fixing ---
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.common import settings
from apps.cli.resume import Resume
from apps.cli.roles import Roles, Role, JobSpyClient
from apps.cli.fetch import run_fetch

app = typer.Typer(help="Job Filter CLI: Manage roles, resume, and fetch scored jobs.")
console = Console()

# --- Resume Commands ---

@app.command(name="resume-parse")
def resume_parse(text: str = typer.Argument(..., help="Raw text to extract skills from")):
  """Parse raw text into your resume.json using LLM."""
  console.print("[bold blue]Parsing resume text via LLM...[/bold blue]")
  new_resume = Resume.from_text(text, settings.openai_api_key)
  
  if new_resume:
    new_resume.save()
    console.print("[bold green]✅ Resume updated successfully in data/cli/resume.json[/bold green]")
  else:
    console.print("[bold red]❌ Failed to parse resume.[/bold red]")

@app.command(name="resume-show")
def resume_show():
  """Display current skills in resume.json."""
  resume = Resume.load()
  console.print_json(resume.model_dump_json())

# --- Role Commands ---

@app.command(name="role-add")
def role_add():
  """Interactively add a new job search role."""
  name = typer.prompt("Role Name (e.g., Data Analyst)")
  search_term = typer.prompt("JobSpy Search Term", default=name)
  location = typer.prompt("Location", default="Indonesia")
  results_wanted = typer.prompt("Results Wanted", default=50, type=int)
  spacy_path = typer.prompt("Path to spaCy patterns (.jsonl)", default=f"data/patterns/{name.lower().replace(' ', '_')}.jsonl")

  try:
    new_role = Role(
      name=name,
      client=JobSpyClient(
        search_term=search_term,
        location=location,
        results_wanted=results_wanted
      ),
      spacy_path=spacy_path
    )
    
    roles_store = Roles.load()
    roles_store.add_role(new_role)
    roles_store.save()
    console.print(f"[bold green]✅ Role '{name}' added successfully.[/bold green]")
  except Exception as e:
    console.print(f"[bold red]❌ Error: {e}[/bold red]")

@app.command(name="role-list")
def role_list():
  """List all configured roles."""
  roles_store = Roles.load()
  if not roles_store.roles:
    console.print("[yellow]No roles found. Use 'role-add' to create one.[/yellow]")
    return
  
  for role in roles_store.roles:
    console.print(f"- [bold cyan]{role.name}[/bold cyan]: {role.client.search_term} ({role.client.location})")

# --- Fetch Command ---

@app.command(name="fetch")
def fetch(
  role: str = typer.Argument(..., help="The name of the role to fetch jobs for"),
  min_score: float = typer.Option(50.0, "--score", "-s", help="Minimum match score threshold")
):
  """Fetch and score jobs for a specific role."""
  try:
    run_fetch(role, min_score=min_score)
  except Exception as e:
    console.print(f"[bold red]❌ Pipeline Error: {e}[/bold red]")

if __name__ == "__main__":
  app()
