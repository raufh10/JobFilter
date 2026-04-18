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
  search_term = typer.prompt("Search Term", default=name)
  location = typer.prompt("Location", default="Indonesia")
  
  sites_input = typer.prompt("Sites (comma separated)", default="indeed")
  site_names = [s.strip() for s in sites_input.split(",")]
  
  results = typer.prompt("Results wanted", default=20, type=int)
  hours = typer.prompt("Hours old (max age of post)", default=48, type=int)
  remote = typer.confirm("Remote only?", default=False)

  try:
    new_role = Role(
      name=name,
      client=JobSpyClient(
        site_name=site_names,
        search_term=search_term, 
        location=location, 
        results_wanted=results,
        hours_old=hours,
        remote_only=remote,
        country_indeed="Indonesia"
      )
    )
    
    store = Roles.load()
    store.add_role(new_role)
    store.save()
    
    console.print(f"\n[bold green]✅ Role '{name}' saved with custom config:[/bold green]")
    console.print(f"   [dim]Sites: {', '.join(site_names)} | Age: {hours}h | Remote: {remote}[/dim]")
    
  except Exception as e:
    console.print(f"[red]Validation Error:[/red] {e}")

@app.command(name="role-list")
def role_list():
  """List all configured search roles and their specific filters."""
  store = Roles.load()
  if not store.roles:
    console.print("[yellow]No roles configured yet.[/yellow]")
    return
    
  for r in store.roles:
    c = r.client
    remote_status = "🌐 Remote" if c.remote_only else "📍 On-site/Hybrid"
    console.print(f"• [bold cyan]{r.name}[/bold cyan]")
    console.print(f"  [dim]Query: {c.search_term} in {c.location} | {remote_status} | {c.hours_old}h old[/dim]")

# --- Main Execution ---

@app.command(name="fetch")
def fetch(
  role: str = typer.Argument(..., help="The name of the role to use"),
  score: float = typer.Option(50.0, "--min-score", "-s", help="Minimum match score (0-100)")
):
  """Fetch and score jobs using a specific role and LLM analysis."""
  llm_client = get_llm_client()
  try:
    run_fetch(role, llm_client=llm_client, min_score=score)
  except Exception as e:
    console.print(f"[bold red]Fetch Error:[/bold red] {e}")

if __name__ == "__main__":
  app()
