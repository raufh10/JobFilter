import json
import re
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from src.llm import LLMClient, generate_structured_response

# Default storage path
DEFAULT_RESUME_PATH = Path("data/cli/resume.json")

class Resume(BaseModel):
  model_config = ConfigDict(extra='forbid')

  languages: List[str] = Field(
    default_factory=list, 
    description="Programming languages like Python, R, SQL, Julia."
  )
  tools: List[str] = Field(
    default_factory=list, 
    description="Software/platforms like Tableau, PowerBI, Docker, Git, Airflow."
  )
  frameworks: List[str] = Field(
    default_factory=list, 
    description="Libraries or frameworks like PyTorch, TensorFlow, Scikit-learn, Spark."
  )
  cloud_platforms: List[str] = Field(
    default_factory=list, 
    description="Cloud services like AWS, GCP, Azure and specific services like S3, BigQuery."
  )

  def save(self, path: Path = DEFAULT_RESUME_PATH):
    """
    Creates or replaces the resume.json file.
    Automatically creates parent directories if they don't exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
      f.write(self.model_dump_json(indent=2))

  @classmethod
  def load(cls, path: Path = DEFAULT_RESUME_PATH) -> "Resume":
    """
    Reads the resume.json file and returns a Resume instance.
    Returns an empty Resume if the file does not exist.
    """
    if not path.exists():
      return cls()
    
    try:
      with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return cls.model_validate(data)
    except (json.JSONDecodeError, ValueError):
      # Return empty resume if file is corrupted
      return cls()

  @classmethod
  def from_text(
    cls, 
    text: str, 
    api_key: str, 
    model: str = "gpt-5.4-nano"
  ) -> Optional["Resume"]:
    """
    Initializes an LLM client internally and extracts resume details from raw text.
    Returns a validated Resume instance.
    """
    if not text.strip():
      return None

    llm_client = LLMClient(
      api_key=api_key,
      model=model,
      name="resume_parser",
      system_prompt=(
        "You are an expert Technical Recruiter. "
        "Extract technical skills from the provided text into the structured format. "
        "Normalize names (e.g., 'scikit-learn' instead of 'sklearn')."
      ),
      format_schema=cls,
      prompt_key="cli_resume_parsing"
    )

    try:
      parsed_resume = generate_structured_response(llm_client, text)
      return parsed_resume
    except Exception as e:
      print(f"⚠️ Failed to parse resume from text: {e}")
      return None
