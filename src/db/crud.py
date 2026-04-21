import json
from typing import List, Dict, Optional
from src.db.client import get_connection

def upsert_role(role):
  data = role.model_dump()
  c = data["client"]
  
  query = """
    INSERT INTO roles (
      name, site_name, search_term, location, results_wanted, 
      hours_old, country_indeed, remote_only, strictness
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
      site_name=excluded.site_name,
      search_term=excluded.search_term,
      location=excluded.location,
      results_wanted=excluded.results_wanted,
      hours_old=excluded.hours_old,
      country_indeed=excluded.country_indeed,
      remote_only=excluded.remote_only,
      strictness=excluded.strictness
  """

  params = (
    data["name"],
    json.dumps(c["site_name"]),
    json.dumps(c["search_term"]),
    c["location"],
    c["results_wanted"],
    c.get("hours_old"),
    c["country_indeed"],
    int(c["remote_only"]),
    c["strictness"]
  )
  
  with get_connection() as conn:
    conn.execute(query, params)

def get_all_roles():
  with get_connection() as conn:
    rows = conn.execute("SELECT * FROM roles").fetchall()
  return [dict(row) for row in rows]

def get_cached_scores(job_urls: List[str]) -> Dict[str, dict]:
  """Retrieves cached results for multiple job URLs at once."""
  if not job_urls:
    return {}

  placeholders = ", ".join(["?"] * len(job_urls))
  query = f"""
    SELECT job_url, title, score, explanation, matched_skills 
    FROM jobs 
    WHERE job_url IN ({placeholders})
  """

  cached_results = {}
  
  with get_connection() as conn:
    rows = conn.execute(query, job_urls).fetchall()
    
    for row in rows:
      url = row["job_url"]
      cached_results[url] = {
        "title": row["title"],
        "score": row["score"],
        "explanation": row["explanation"],
        "matches": json.loads(row["matched_skills"]),
        "url": url
      }
      
  return cached_results

def upsert_job_cache(job_url: str, title: str, score: int, explanation: str, matches: list):
  """Saves or updates a job's score and metadata."""
  query = """
    INSERT INTO jobs (job_url, title, score, explanation, matched_skills)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(job_url) DO UPDATE SET
      score=excluded.score,
      explanation=excluded.explanation,
      matched_skills=excluded.matched_skills
  """
  with get_connection() as conn:
    conn.execute(query, (
      job_url, 
      title, 
      score, 
      explanation, 
      json.dumps(matches)
    ))

def get_top_scored_jobs(min_score: float, limit: int = 50) -> List[dict]:
  """
  Retrieves the highest scoring jobs from the cache.
  Used by the 'jobs' CLI command for direct cache viewing.
  """
  query = """
    SELECT job_url, title, score, explanation, matched_skills 
    FROM jobs 
    WHERE score >= ? 
    ORDER BY score DESC 
    LIMIT ?
  """
  
  with get_connection() as conn:
    rows = conn.execute(query, (min_score, limit)).fetchall()
    
    return [
      {
        "title": row["title"],
        "score": row["score"],
        "explanation": row["explanation"],
        "matches": json.loads(row["matched_skills"]),
        "url": row["job_url"]
      }
      for row in rows
    ]
