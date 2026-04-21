import json
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

