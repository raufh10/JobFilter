import json
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from src.jobspy import JobSpyClient
from src.db.crud import upsert_role, get_all_roles

class Role(BaseModel):
  """Defines a specific job role and its search configuration."""
  model_config = ConfigDict(extra='forbid')
  name: str
  client: JobSpyClient

class Roles(BaseModel):
  """Container for managing multiple roles with SQLite backend."""
  model_config = ConfigDict(extra='forbid')
  roles: List[Role] = Field(default_factory=list)

  @classmethod
  def _map_row_to_role(cls, row: dict) -> Role:
    """Helper to transform a raw DB row into a validated Role object."""
    return Role(
      name=row["name"],
      client=JobSpyClient(
        site_name=json.loads(row["site_name"]),
        search_term=json.loads(row["search_term"]),
        location=row["location"],
        results_wanted=row["results_wanted"],
        hours_old=row.get("hours_old"),
        country_indeed=row["country_indeed"],
        remote_only=bool(row["remote_only"]),
        strictness=row["strictness"]
      )
    )

  @classmethod
  def load(cls) -> "Roles":
    """Loads all roles from SQLite and parses them into Role objects."""
    raw_rows = get_all_roles()
    return cls(roles=[cls._map_row_to_role(dict(row)) for row in raw_rows])

  def save(self):
    """Blindly passes roles to the DB upsert logic."""
    for role in self.roles:
      upsert_role(role)

  def get_role(self, identifier: Union[str, int]) -> Optional[Role]:
    """Retrieves a role by name or shortcut index (1-based)."""
    # Refresh roles to ensure we have current DB state
    current_roles = self.load().roles
    
    if isinstance(identifier, int):
      index = identifier - 1
      if 0 <= index < len(current_roles):
        return current_roles[index]
      return None

    for role in current_roles:
      if role.name.lower() == str(identifier).lower():
        return role
    return None

  def add_role(self, role: Role, overwrite: bool = True):
    """Directly saves a role to SQLite and refreshes local state."""
    upsert_role(role)
    self.roles = self.load().roles
