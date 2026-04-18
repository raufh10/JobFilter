import sys
from pathlib import Path

# --- Path Fixing ---
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
  sys.path.insert(0, str(project_root))

import typer
from rich.console import Console
from rich.panel import Panel

# Local Imports
from apps.cli.resume import Resume
from apps.cli.roles import Roles, Role, JobSpyClient
from apps.cli.fetch import run_fetch

app = typer.Typer(help="Job Filter CLI: Manage skills and fetch scored jobs.")
console = Console()

# --- Resume (Skill) Management ---

@app.command(name="skill-add")
def skill_add(
  category: str = typer.Argument(..., help="languages, tools, frameworks, or cloud_platforms"),
  skill: str = typer.Argument(..., help="The skill name to add")
):
  """Manually add a skill to your local resume.json."""
  resume = Resume.load()
  
  attr_map = {
    "languages": resume.languages,
    "tools": resume.tools,
    "frameworks": resume.frameworks,
    "cloud_platforms": resume.cloud_platforms
  }

  if category not in attr_map:
    console.print(f"[red]Error:[/red] Category must be one of {list(attr_map.keys())}")
    return

  if skill not in attr_map[category]:
    attr_map[category].append(skill)
    resume.save()
    console.print(f"[green]Added [bold]{skill}[/bold] to {category}.[/green]")
  else:
    console.print(f"[yellow]{skill} already exists in {category}.[/yellow]")

@app.command(name="skill-show")
def skill_show():
  """Display all currently saved skills."""
  resume = Resume.load()
  console.print(Panel(resume.model_dump_json(indent=2), title="Current Resume Skills", border_style="blue"))

# --- Role Management ---

@app.command(name="role-add")
def role_add():
  """Interactively setup a job search role."""
  name = typer.prompt("Role Name (e.g., Data Analyst)")
  search_term = typer.prompt("Search Term", default=name)
  results = typer.prompt("Results wanted", default=20, type=int)
  
  # Default path based on name
  default_path = f"data/patterns/{name.lower().replace(' ', '_')}.jsonl"
  spacy_path = typer.prompt("spaCy Patterns Path", default=default_path)

  try:
    new_role = Role(
      name=name,
      client=JobSpyClient(search_term=search_term, results_wanted=results),
      spacy_path=spacy_path
    )
    store = Roles.load()
    store.add_role(new_role)
    store.save()
    console.print(f"[green]Role [bold]{name}[/bold] saved successfully.[/green]")
  except Exception as e:
    console.print(f"[red]Validation Error:[/red] {e}")

@app.command(name="role-list")
def role_list():
  """List all configured search roles."""
  store = Roles.load()
  if not store.roles:
    console.print("[yellow]No roles configured yet.[/yellow]")
    return
  for r in store.roles:
    console.print(f"• [cyan]{r.name}[/cyan] -> [dim]{r.spacy_path}[/dim]")

# --- Main Execution ---

@app.command(name="fetch")
def fetch(
  role: str = typer.Argument(..., help="The name of the role to use"),
  score: float = typer.Option(50.0, "--min-score", "-s", help="Minimum match score")
):
  """Fetch and score jobs using a specific role."""
  try:
    run_fetch(role, min_score=score)
  except Exception as e:
    console.print(f"[bold red]Fetch Error:[/bold red] {e}")

if __name__ == "__main__":
  app()
