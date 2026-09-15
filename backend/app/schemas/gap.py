"""Pydantic contracts for canonical-skill gap analysis."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GapSkillReference(BaseModel):
    skill_id: str = Field(pattern=r"^SKILL_[0-9]{4}$")
    taxonomy_version: str = Field(min_length=1, max_length=32)


class CandidateSkillReference(GapSkillReference):
    proficiency_level: str | None = Field(default=None, min_length=1, max_length=50)
    years_experience: int | None = Field(default=None, ge=0)


class CandidateProfileRequest(BaseModel):
    subject_id: int = Field(ge=1)
    subject_type: str = Field(default="applicant", min_length=1, max_length=50)
    taxonomy_version: str = Field(min_length=1, max_length=32)
    skills: list[CandidateSkillReference] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=255)
    education: str | None = Field(default=None, max_length=255)
    experience_years: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_skill_versions(self) -> "CandidateProfileRequest":
        if any(skill.taxonomy_version != self.taxonomy_version for skill in self.skills):
            raise ValueError("Candidate skill taxonomy versions must match the profile")
        return self


class RequiredSkillRequest(GapSkillReference):
    role_importance: float = Field(default=1.0, ge=0, le=1)


class GapTargetRequest(BaseModel):
    job_id: int | None = Field(default=None, ge=1)
    required_skills: list[RequiredSkillRequest] = Field(default_factory=list)


class GapContextRequest(BaseModel):
    district_id: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=255)


class GapAnalysisRequest(BaseModel):
    candidate: CandidateProfileRequest
    target: GapTargetRequest
    context: GapContextRequest = Field(default_factory=GapContextRequest)

    @model_validator(mode="after")
    def validate_target_duplicates(self) -> "GapAnalysisRequest":
        skill_ids = [skill.skill_id for skill in self.target.required_skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Target required skills must not contain duplicates")
        return self


class MatchedSkillResponse(BaseModel):
    skill_id: str
    taxonomy_version: str
    coverage: float
    explanation: str


class MissingSkillResponse(BaseModel):
    skill_id: str
    taxonomy_version: str
    priority: float | None
    normalized_demand: float | None
    trend_multiplier: float
    gap_severity: float
    role_importance: float
    explanation: str


class GapAnalysisData(BaseModel):
    matched_skills: list[MatchedSkillResponse]
    missing_skills: list[MissingSkillResponse]


class GapAnalysisMeta(BaseModel):
    scoring_version: str
    taxonomy_version: str
    demand_source_version: str


class GapAnalysisResponse(BaseModel):
    data: GapAnalysisData
    meta: GapAnalysisMeta
    model_version: str | None
    source_version: str
    generated_at: datetime
    warnings: list[str]