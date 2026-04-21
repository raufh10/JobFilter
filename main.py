import typer
from rich.console import Console
from rich.panel import Panel

from src.common import settings
from src.llm import LLMClient
from src.jobspy import JobSpyClient
from src.engine import Resume, Roles, Role, run_fetch
from src.engine.scores import JobMatchScore, SCORING_SYSTEM_PROMPT

app = typer.Typer(help="Job Filter CLI: Manage resume and fetch scored jobs via LLM.")
console = Console()

# --- Global LLM Client Init ---
def get_llm_client():
  return LLMClient(
    api_key=settings.openai_api_key,
    model="gpt-5.4-nano",
    name="job_scoring_engine",
    system_prompt=SCORING_SYSTEM_PROMPT,
    format_schema=JobMatchScore,
    prompt_key="job_scoring_v1"
  )

# --- Resume Management ---

@app.command(name="resume-set")
def resume_set(
  text: str = typer.Argument(..., help="The full text content of your resume/CV")
):
  """Overwrite your saved resume text content."""
  resume = Resume(content=text)
  resume.save()
  console.print("[green]✅ Resume text saved successfully.[/green]")

@app.command(name="resume-show")
def resume_show():
  """Display your current resume content."""
  resume = Resume.load()
  if not resume.content:
    console.print("[yellow]Resume is empty.[/yellow]")
  else:
    console.print(Panel(resume.content, title="Current Resume Text", border_style="blue"))

# --- Role Management ---

@app.command(name="role-add")
def role_add():
  """Interactively setup a job search role with full JobSpy customization."""
  name = typer.prompt("Role Name (e.g., Data Analyst)")

  # Scraper Settings
  search_input = typer.prompt("Search Terms (comma separated)", default=name)
  search_terms = [t.strip() for t in search_input.split(",")]

  location = typer.prompt("Location", default="Indonesia")

  sites_input = typer.prompt("Sites (comma separated)", default="indeed")
  site_names = [s.strip().lower() for s in sites_input.split(",")]

  if "linkedin" in site_names:
    console.print(
      "\n[bold yellow]⚠️  LinkedIn Detected:[/bold yellow] "
      "Please ensure you have a valid [cyan]proxy_url[/cyan] configured in your "
      "environment or settings before running [bold green]fetch[/bold green].\n"
    )

  results = typer.prompt("Results wanted", default=20, type=int)
  hours = typer.prompt("Hours old (max age of post)", default=48, type=int)
  remote = typer.confirm("Remote only?", default=False)
  
  strictness = typer.prompt(
    "Scoring Strictness (low, medium, high)", 
    default="medium"
  ).lower()

  try:
    client_config = JobSpyClient(
      site_name=site_names,
      search_term=search_terms, 
      location=location, 
      results_wanted=results,
      hours_old=hours,
      remote_only=remote,
      country_indeed="Indonesia",
      strictness=strictness
    )

    new_role = Role(
      name=name,
      client=client_config
    )

    store = Roles.load()
    store.add_role(new_role)
    store.save()

    console.print(f"\n[bold green]✅ Role '{name}' saved successfully![/bold green]")
    console.print(
      f"   [dim]Sites: {', '.join(site_names)} | "
      f"Strictness: {strictness} | "
      f"Age: {hours}h | "
      f"Remote: {remote}[/dim]"
    )

  except ValueError as e:
    console.print(f"[bold red]Configuration Error:[/bold red] {e}")
  except Exception as e:
    console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

@app.command(name="role-list")
def role_list():
  """List all configured search roles with shortcut indices."""
  store = Roles.load()
  if not store.roles:
    console.print("[yellow]No roles configured yet.[/yellow]")
    return

  for i, r in enumerate(store.roles, 1):
    c = r.client
    remote_status = "🌐 Remote" if c.remote_only else "📍 On-site/Hybrid"
    # Added [index] for the shortcut
    console.print(f"[bold green][{i}][/bold green] [bold cyan]{r.name}[/bold cyan]")
    console.print(f"    [dim]Query: {c.search_term} in {c.location} | {remote_status} | {c.hours_old}h old[/dim]")

# --- Main Execution ---

@app.command(name="fetch")
def fetch(
  role: str = typer.Argument(..., help="The name or shortcut index of the role to use"),
  score: float = typer.Option(50.0, "--min-score", "-s", help="Minimum match score (0-100)")
):
  """Fetch and score jobs using a specific role (name or #) and LLM analysis."""
  llm_client = get_llm_client()
  try:
    run_fetch(role, llm_client=llm_client, min_score=score)
  except Exception as e:
    console.print(f"[bold red]Fetch Error:[/bold red] {e}")

if __name__ == "__main__":
  app()
