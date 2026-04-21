import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.jobspy import fetch_jobs, JobResponse
from src.llm import LLMClient, generate_structured_response
from src.engine.scores import JobMatchScore, SCORING_SYSTEM_PROMPT
from src.engine.roles import Role, Roles
from src.engine.resume import Resume
from src.db.crud import get_cached_scores, upsert_job_cache

console = Console()
db_lock = threading.Lock()

class JobScorer:
  def __init__(self, role: Role, resume: Resume, llm_client: LLMClient, min_score: float = 0.0, max_workers: int = 5):
    self.role = role
    self.resume = resume
    self.llm_client = llm_client
    self.min_score = min_score
    self.max_workers = max_workers

  def _score_single_job(self, job):
    """Worker function to score a single job and update cache."""
    try:
      user_input = f"RESUME:\n{self.resume.content}\n\nJOB DESCRIPTION:\n{job.description}"
      scored_data: JobMatchScore = generate_structured_response(self.llm_client, user_input)

      if scored_data:
        # Use lock to prevent multiple threads from writing to SQLite at the exact same time
        with db_lock:
          upsert_job_cache(
            job_url=job.job_url,
            title=job.title,
            score=scored_data.score,
            explanation=scored_data.explanation,
            matches=scored_data.matched_skills
          )

        if scored_data.score >= self.min_score:
          return {
            "title": job.title,
            "score": scored_data.score,
            "matches": scored_data.matched_skills,
            "explanation": scored_data.explanation,
            "url": job.job_url
          }
    except Exception as e:
      console.print(f"[dim red]Failed to score job '{job.title}': {e}[/dim red]")
    return None

  def run(self):
    """Main execution flow: Fetch -> Cache Check -> Threaded LLM Score -> Display."""
    # 1. Fetch Jobs
    response: JobResponse = fetch_jobs(self.role.client)

    if not response.jobs:
      console.print("[yellow]No jobs found matching the criteria.[/yellow]")
      return

    # 2. Check Cache
    all_urls = [job.job_url for job in response.jobs]
    cache_map = get_cached_scores(all_urls)

    scored_results = []
    jobs_to_score = []

    for job in response.jobs:
      if job.job_url in cache_map:
        cached_data = cache_map[job.job_url]
        if cached_data["score"] >= self.min_score:
          scored_results.append(cached_data)
      else:
        jobs_to_score.append(job)

    # 3. Threaded Scoring for new jobs
    if jobs_to_score:
      with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
      ) as progress:
        task = progress.add_task(
          f"[cyan]Scoring {len(jobs_to_score)} jobs with {self.max_workers} threads...", 
          total=len(jobs_to_score)
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
          # Submit all jobs to the thread pool
          futures = {executor.submit(self._score_single_job, job): job for job in jobs_to_score}
          
          for future in as_completed(futures):
            result = future.result()
            if result:
              scored_results.append(result)
            progress.advance(task)

    if not scored_results:
      console.print(f"[yellow]No jobs met the minimum score of {self.min_score}%.[/yellow]")
      return

    # 4. Sort and Display
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    self._display_table(scored_results)

  def _display_table(self, results: list):
    """Renders results in a formatted Rich table."""
    table = Table(
      title=f"Scored Jobs for {self.role.name} (Min: {self.min_score}% - Matched: {len(results)})", 
      header_style="bold magenta",
      show_lines=True
    )

    table.add_column("Score", justify="right", style="green")
    table.add_column("Job Details", style="cyan")
    table.add_column("Match Logic", style="white")

    for item in results:
      match_str = ", ".join(item['matches'][:5])
      table.add_row(
        f"[bold]{item['score']}%[/bold]",
        f"{item['title']}\n[dim]{item['url']}[/dim]",
        f"[italic]'{item['explanation']}'[/italic]\n[dim]Skills: {match_str}[/dim]"
      )

    console.print(table)

def run_fetch(role_identifier: str, llm_client: LLMClient, min_score: float = 50.0):
  """CLI entry point to execute the fetch command using role name or shortcut index."""
  roles_store = Roles.load()
  resume = Resume.load()

  try:
    identifier = int(role_identifier)
  except ValueError:
    identifier = role_identifier

  role = roles_store.get_role(identifier)
  if not role:
    console.print(f"[red]Error: Role identifier '{role_identifier}' not found.[/red]")
    roles_store.list_roles() 
    return

  if not resume.content:
    console.print("[red]Error: Resume content is empty. Add your resume first.[/red]")
    return

  scorer = JobScorer(role, resume, llm_client, min_score=min_score)
  scorer.run()
