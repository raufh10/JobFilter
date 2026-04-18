from typing import List
from pydantic import BaseModel, Field, ConfigDict

class JobMatchScore(BaseModel):
  model_config = ConfigDict(extra='forbid')

  score: float = Field(
    ..., 
    description="Match score from 0 to 100 based on the rubric."
  )
  matched_skills: List[str] = Field(
    default_factory=list, 
    description="List of technical skills found in the job that exist in the resume."
  )
  explanation: str = Field(
    ..., 
    description="A one-sentence justification for the score."
  )

SCORING_SYSTEM_PROMPT = """
You are a Technical Recruiter scoring a job description against a candidate's resume text.
Use the following strict Rubric to determine the score:

- 90-100: Perfect match; candidate has all core technologies and required experience levels.
- 70-89: Strong match; candidate has most core technologies but may lack secondary tools.
- 50-69: Fair match; candidate has foundational skills but lacks specific industry frameworks.
- 10-49: Poor match; significant skill gaps in primary required stack.
- 0: No relevance.

Rules:
1. Focus only on skills present in BOTH the job and the resume.
2. The explanation MUST be exactly one sentence.
3. Output MUST be valid JSON matching the schema.
"""
