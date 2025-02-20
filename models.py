from pydantic import BaseModel, Field
from typing import List, Dict

class CriteriaResponse(BaseModel):
    criteria: List[str] = Field(..., description="List of extracted criteria from job description")

class ErrorResponse(BaseModel):
    Error: str = Field(..., description="Error message when processing fails")

class ScoreResponse(BaseModel):
    message: str = Field(..., description="Success message after processing")

class CriteriaHeaders(BaseModel):
    criteria_headers: Dict[str, str] = Field(..., description="Mapping of criteria to their headers")

class CandidateScores(BaseModel):
    Candidate_Name: str = Field(..., description="Name of the candidate")
    scores: Dict[str, int] = Field(..., description="Scores for each criteria") 