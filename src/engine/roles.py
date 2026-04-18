import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.jobspy import JobSpyClient

class Role(BaseModel):
  """Defines a specific job role and its search configuration."""
  model_config = ConfigDict(extra='forbid')

  name: str = Field(..., description="Unique name for the role, e.g., 'Data Analyst'")
  client: JobSpyClient

class Roles(BaseModel):
  """Container for managing multiple roles."""
  model_config = ConfigDict(extra='forbid')

  roles: List[Role] = Field(default_factory=list)

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
        # Handle if data is a raw list or the wrapped object
        roles_list = data.get("roles", []) if isinstance(data, dict) else data
        return cls(roles=roles_list)
    except (json.JSONDecodeError, ValueError):
      return cls()

  def get_role(self, name: str) -> Optional[Role]:
    """Retrieves a role by its name."""
    for role in self.roles:
      if role.name.lower() == name.lower():
        return role
    return None

  def add_role(self, role: Role, overwrite: bool = True):
    """Adds a new role or replaces an existing one by name."""
    if overwrite:
      self.roles = [r for r in self.roles if r.name.lower() != role.name.lower()]
    self.roles.append(role)
