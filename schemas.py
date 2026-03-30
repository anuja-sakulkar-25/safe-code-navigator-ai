#This file defines the shape of every request and response. 
#Think of it as the contract between the user and the agent.

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class QuestionType(str, Enum):
    function_logic     = "function_logic"
    api_integration    = "api_integration"
    database_query     = "database_query"
    config_environment = "config_environment"
    file_dependencies  = "file_dependencies"
    workflow_flow      = "workflow_flow"
    error_debugging    = "error_debugging"


class RiskLevel(str, Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


class AnalyzeRequest(BaseModel):
    question: str = Field(description="What the developer wants to understand")
    code: Optional[str] = Field(default=None, description="The sanitized code snippet")
    context: Optional[str] = Field(default=None, description="Which module or system this belongs to")


class RiskFlag(BaseModel):
    description: str
    severity: RiskLevel
    reason: str


class CodeExplanation(BaseModel):
    purpose: str
    behavior: str
    intent_reconstruction: str
    inputs_outputs: str
    dependencies: List[str] = Field(default_factory=list)
    edge_cases: List[str]   = Field(default_factory=list)
    risk_surface: List[RiskFlag] = Field(default_factory=list)
    suggested_documentation: str
    questions_for_manager: List[str] = Field(default_factory=list)


class SecurityFlag(BaseModel):
    type: str
    description: str
    replacement_suggestion: str


class SecurityCheck(BaseModel):
    passed: bool
    flags: List[SecurityFlag] = Field(default_factory=list)
    message: Optional[str] = None


class AnalyzeResponse(BaseModel):
    security_check: SecurityCheck
    question_type: Optional[QuestionType] = None
    risk_level: Optional[RiskLevel]       = None
    explanation: Optional[CodeExplanation] = None
    warning_checklist: List[str]           = Field(default_factory=list)
    coverage_confidence: Optional[float]   = None
    error: Optional[str]                   = None