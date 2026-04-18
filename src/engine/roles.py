import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- 1. Models ---

class JobSpyClient(BaseModel):
  """Parameters for the JobSpy scraper client."""
  model_config = ConfigDict(extra='forbid')

  site_name: List[str] = ["indeed"]
  search_term: str
  location: str = "Indonesia"
  results_wanted: int = 20
  hours_old: Optional[int] = 48
  country_indeed: str = "Indonesia"
  remote_only: Optional[bool] = False

class Role(BaseModel):
  """Defines a specific job role, its search config, and spaCy assets."""
  model_config = ConfigDict(extra='forbid')

  name: str = Field(..., description="Unique name for the role, e.g., 'Data Analyst'")
  client: JobSpyClient
  spacy_path: str = Field(
    ..., 
    description="Path to the spaCy patterns JSONL file for this role."
  )

  @field_validator('spacy_path')
  @classmethod
  def check_spacy_path_exists(cls, v: str) -> str:
    """Ensures the spaCy patterns file exists at initialization."""
    path = Path(v)
    if not path.exists():
      raise FileNotFoundError(f"spaCy patterns file not found at: {v}")
    return v

class Roles(BaseModel):
  """Container for managing multiple roles."""
  model_config = ConfigDict(extra='forbid')
  
  roles: List[Role] = Field(default_factory=list)

  # --- 2. File Persistence ---

  def save(self, path: Path = Path("data/cli/roles.json")):
    """Saves the roles configuration to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
      f.write(self.model_dump_json(indent=2))

  @classmethod
  def load(cls, path: Path = Path("data/cli/roles.json")) -> "Roles":
    """Loads the roles configuration. Returns empty container if not found."""
    if not path.exists():
      return cls()
    try:
      with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        roles_list = data.get("roles", []) if isinstance(data, dict) else data
        return cls(roles=roles_list)
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
      # If loading fails due to missing spacy_path in existing roles, 
      # we catch it here to allow the app to start.
      return cls()

  # --- 3. Helper Methods ---

  def get_role(self, name: str) -> Optional[Role]:
    """Retrieves a role by its name."""
    for role in self.roles:
      if role.name.lower() == name.lower():
        return role
    return None

  def add_role(self, role: Role, overwrite: bool = True):
    """
    Adds a new role. The existence of spacy_path is already 
    checked by the Role validator.
    """
    if overwrite:
      self.roles = [r for r in self.roles if r.name.lower() != role.name.lower()]
    self.roles.append(role)

