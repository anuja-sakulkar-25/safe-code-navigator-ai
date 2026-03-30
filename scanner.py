#scan_for_sensitive_data() — runs every pattern against the submitted code using Python's re (regex) module. 
# If any match, the whole request is blocked immediately, before ADK or Gemini are ever called.
# get_warning_checklist() — returns a contextual list of what to replace, based on question type, 
# shown to the developer BEFORE they paste code.

import re
from typing import List, Tuple
from schemas import SecurityFlag, SecurityCheck

SENSITIVE_PATTERNS: List[Tuple[str, str, str, str]] = [
    (
        "aws_access_key",
        r"AKIA[0-9A-Z]{16}",
        "AWS Access Key ID — grants access to AWS services",
        "AWS_ACCESS_KEY_ID_PLACEHOLDER"
    ),
    (
        "stripe_live_key",
        r"sk_live_[A-Za-z0-9]{24,}",
        "Stripe live secret key — grants full payment API access",
        "STRIPE_SECRET_KEY_PLACEHOLDER"
    ),
    (
        "stripe_test_key",
        r"sk_test_[A-Za-z0-9]{24,}",
        "Stripe test secret key detected",
        "STRIPE_TEST_KEY_PLACEHOLDER"
    ),
    (
        "gcp_private_key",
        r'"private_key":\s*"-----BEGIN',
        "GCP service account private key",
        "GCP_PRIVATE_KEY_PLACEHOLDER"
    ),
    (
        "database_url",
        r"(postgres|mysql|mongodb|redis):\/\/[^\s\"'<>]+",
        "Database connection string with credentials",
        "DATABASE_URL_PLACEHOLDER"
    ),
    (
        "jwt_token",
        r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "JWT token — may contain auth credentials",
        "JWT_TOKEN_PLACEHOLDER"
    ),
    (
        "private_ip",
        r"\b(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b",
        "Internal IP address — reveals internal network topology",
        "INTERNAL_HOST_PLACEHOLDER"
    ),
    (
        "generic_api_key",
        r"(?i)(api[_\-]?key|apikey|api[_\-]?secret)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]",
        "API key assignment detected",
        "API_KEY_PLACEHOLDER"
    ),
    (
        "bearer_token",
        r"(?i)bearer\s+[A-Za-z0-9\-._~+\/]{20,}",
        "Bearer token in authorization header",
        "BEARER_TOKEN_PLACEHOLDER"
    ),
    (
        "password_assignment",
        r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{6,}['\"]",
        "Hardcoded password detected",
        "PASSWORD_PLACEHOLDER"
    ),
]


def scan_for_sensitive_data(code: str) -> SecurityCheck:
    """
    Scans code for sensitive patterns.
    Returns SecurityCheck with passed=True if clean, passed=False if blocked.
    Input is NEVER sent to Gemini if this returns passed=False.
    """
    if not code or not code.strip():
        return SecurityCheck(passed=True, flags=[])

    found: List[SecurityFlag] = []

    for pattern_name, pattern_regex, description, replacement in SENSITIVE_PATTERNS:
        if re.search(pattern_regex, code):
            found.append(SecurityFlag(
                type=pattern_name,
                description=description,
                replacement_suggestion=f"Replace with: {replacement}"
            ))

    if found:
        return SecurityCheck(
            passed=False,
            flags=found,
            message=(
                "Your code was NOT sent to the AI. "
                "Replace the values shown below, then resubmit."
            )
        )

    return SecurityCheck(passed=True, flags=[])


def get_warning_checklist(question_type: str) -> List[str]:
    """Returns what to sanitize before pasting, based on question type."""
    base = [
        "Replace customer names or emails with CUSTOMER_PLACEHOLDER",
        "Replace internal IP addresses with INTERNAL_HOST",
    ]
    specific = {
        "api_integration": [
            "Replace API keys and tokens with API_KEY_PLACEHOLDER",
            "Replace endpoint URLs with API_ENDPOINT_PLACEHOLDER",
            "Replace Authorization headers with AUTH_HEADER_PLACEHOLDER",
        ],
        "database_query": [
            "Replace connection strings with DATABASE_URL_PLACEHOLDER",
            "Replace table/column names containing real customer data",
            "Replace passwords with DB_PASSWORD_PLACEHOLDER",
        ],
        "config_environment": [
            "Share key names only — replace ALL values with PLACEHOLDER",
            "Replace secret manager references with SECRET_NAME_PLACEHOLDER",
            "Replace any hardcoded passwords with PASSWORD_PLACEHOLDER",
        ],
        "error_debugging": [
            "Remove stack trace lines containing internal server paths",
            "Replace error messages that contain customer data",
        ],
        "file_dependencies": [
            "Remove absolute file paths if they reveal sensitive structure",
        ],
        "function_logic": [],
        "workflow_flow": [],
    }
    return specific.get(question_type, []) + base


def classify_question(question: str) -> dict:
    """Classifies the developer's question into type and risk level."""
    q = question.lower()

    if any(k in q for k in ["api", "endpoint", "token", "auth", "oauth",
                              "webhook", "http", "request", "integration"]):
        q_type, risk = "api_integration", "high"

    elif any(k in q for k in ["database", "query", "sql", "db", "table",
                                "schema", "postgres", "mysql", "mongo", "orm"]):
        q_type, risk = "database_query", "high"

    elif any(k in q for k in ["config", "env", "environment", "secret",
                                ".env", "credential", "password", "key"]):
        q_type, risk = "config_environment", "critical"

    elif any(k in q for k in ["import", "dependency", "module", "file",
                                "package", "require"]):
        q_type, risk = "file_dependencies", "medium"

    elif any(k in q for k in ["error", "exception", "bug", "crash",
                                "fail", "traceback", "debug"]):
        q_type, risk = "error_debugging", "medium"

    elif any(k in q for k in ["workflow", "flow", "process", "pipeline"]):
        q_type, risk = "workflow_flow", "low"

    else:
        q_type, risk = "function_logic", "low"

    return {
        "question_type": q_type,
        "risk_level": risk,
        "warning_checklist": get_warning_checklist(q_type),
    }