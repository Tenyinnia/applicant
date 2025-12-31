from pydantic import BaseModel, Field
from typing import List

class ParsedProfile(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    summary: str | None
    skills: List[str] = Field(default_factory=list)
    experience_years: float | None
    education: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)