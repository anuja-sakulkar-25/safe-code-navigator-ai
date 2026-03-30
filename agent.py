import os
import re
from typing import List
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from schemas import (
    AnalyzeRequest, AnalyzeResponse, SecurityCheck,
    CodeExplanation, RiskFlag, RiskLevel, QuestionType
)
from scanner import scan_for_sensitive_data, classify_question

load_dotenv()


# ════════════════════════════════════════════════════════════
# ADK TOOL — Structural code analyzer
# Called by the ADK agent as a tool before Gemini reasoning
# ════════════════════════════════════════════════════════════

def analyze_code_structure(code: str) -> dict:
    """
    Performs lightweight structural analysis on sanitized code.
    Detects language, complexity signals, and risk patterns.
    This output is added to the Gemini prompt as structured context.

    Args:
        code: The sanitized code snippet to analyze

    Returns:
        dict with detected_language, complexity_signals, risk_patterns
    """
    if not code or len(code.strip()) < 5:
        return {
            "detected_language": "unknown",
            "complexity_signals": [],
            "risk_patterns": []
        }

    # ── Language detection ─────────────────────────────────────────
    language = "unknown"
    if "def " in code and ("import " in code or "self" in code or ":\n" in code):
        language = "Python"
    elif "function " in code and ("const " in code or "let " in code or "var " in code):
        language = "JavaScript/TypeScript"
    elif "public " in code and ("class " in code or "void " in code or "static " in code):
        language = "Java"
    elif "func " in code and "{" in code and "}" in code:
        language = "Go"
    elif "fun " in code and ("val " in code or "var " in code):
        language = "Kotlin"
    elif "SELECT" in code.upper() and "FROM" in code.upper():
        language = "SQL"
    elif "#include" in code or "std::" in code:
        language = "C++"
    elif "def " in code:
        language = "Python"

    # ── Complexity signals ─────────────────────────────────────────
    complexity = []
    lines = len(code.strip().split('\n'))
    if lines > 100:
        complexity.append(f"Long function ({lines} lines) — higher chance of hidden behavior")
    elif lines > 40:
        complexity.append(f"Medium length ({lines} lines)")

    if code.count("if ") + code.count("elif ") > 4:
        complexity.append("Many conditional branches — read all paths carefully")
    if "async" in code or "await" in code:
        complexity.append("Async code — execution order may not be top-to-bottom")
    if "try" in code and ("except" in code or "catch" in code):
        complexity.append("Contains exception handling — check what is caught vs swallowed")

    # ── Risk patterns ──────────────────────────────────────────────
    risks = []
    if "global " in code:
        risks.append("Uses global variables — changes affect state across the module")
    if "except:" in code or "except Exception:" in code:
        risks.append("Broad exception catch — errors may be silently swallowed")
    if ".update(" in code or " += " in code:
        risks.append("In-place mutation detected — callers may not expect modified input")
    if "os.system(" in code or "subprocess" in code:
        risks.append("Executes shell commands — potential security and portability concern")
    if "sleep(" in code:
        risks.append("Contains sleep() — introduces timing dependency")
    if "pass" in code:
        risks.append("Contains 'pass' — may be a silent no-op in error handler")

    return {
        "detected_language": language,
        "complexity_signals": complexity,
        "risk_patterns": risks
    }


# ════════════════════════════════════════════════════════════
# ADK AGENT DEFINITION
# ════════════════════════════════════════════════════════════

def create_safecode_navigator_agent() -> Agent:
    """
    Creates the SafeCode Navigator AI ADK Agent with Gemini 1.5 Flash.
    The agent has one tool: analyze_code_structure.
    It calls the tool first, then reasons over the result to
    produce a structured plain-English explanation.
    """
    return Agent(
        name="safecode_navigator_agent",
        model="gemini-2.5-flash",
        description=(
            "SafeCode Navigator AI: helps new developers understand legacy "
            "codebases safely. Classifies questions, analyzes code structure, "
            "and produces structured plain-English explanations."
        ),
        instruction="""
You are SafeCode Navigator AI, a senior software engineer helping a new
developer understand unfamiliar code before they modify it.

ALWAYS start by calling the analyze_code_structure tool on any code provided.
Use its output (language, complexity signals, risk patterns) to inform
your explanation.

Then produce a structured response with ALL of these sections, clearly labeled:

PURPOSE
What business problem does this code solve? What is its role?

BEHAVIOR
Walk through what the code does step-by-step. Be specific enough that
someone who has never seen it understands the execution flow.

INTENT RECONSTRUCTION
Why was it written this way? What constraints was the original author
working under? What shortcuts or tradeoffs did they make?

INPUTS AND OUTPUTS
What does this accept as input (types, what each means)?
What does it return? Under what conditions?

DEPENDENCIES
What external systems, modules, or functions does it call?
What other code calls THIS? (use context if given)

EDGE CASES
What unusual inputs does it handle silently?
What would cause it to fail or return unexpectedly?

RISK SURFACE
What is dangerous to change? Be specific — name the exact risk.
Don't say "has side effects." Say exactly what changes would break what.

SUGGESTED DOCUMENTATION
Write a complete docstring or comment block the developer can paste
directly into the code.

QUESTIONS FOR MANAGER
List 2-4 specific questions this developer should ask their tech lead
BEFORE modifying this code. Questions that cannot be answered from code alone.

Be specific throughout. Generic explanations are useless to someone
who needs to safely modify unfamiliar code.
""",
        tools=[analyze_code_structure],
    )


# ════════════════════════════════════════════════════════════
# MAIN PIPELINE — Called by FastAPI
# ════════════════════════════════════════════════════════════

async def run_safecode_navigator_agent(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Full SafeCode Navigator AI pipeline:
    1. Classify question → get warning checklist
    2. Scan for sensitive data → block if found
    3. Run ADK agent with Gemini → get explanation
    4. Parse and return structured response
    """

    # Step 1: classify question type and risk level
    classification = classify_question(request.question)
    q_type   = classification["question_type"]
    risk     = classification["risk_level"]
    warnings = classification["warning_checklist"]

    # Step 2: security scan — BEFORE Gemini sees anything
    if request.code:
        security = scan_for_sensitive_data(request.code)
        if not security.passed:
            return AnalyzeResponse(
                security_check=security,
                question_type=QuestionType(q_type),
                risk_level=RiskLevel(risk),
                warning_checklist=warnings,
                error="Blocked: sensitive data detected. See flags above."
            )
    else:
        security = SecurityCheck(passed=True)

    # Step 3: build the message for the agent
    parts = [f"Question: {request.question}"]
    if request.context:
        parts.append(f"Context: {request.context}")
    if request.code:
        parts.append(f"Code:\n```\n{request.code}\n```")

    user_message = "\n\n".join(parts)

    # Step 4: run the ADK agent
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        # Set the key so ADK can find it
        os.environ["GOOGLE_API_KEY"] = api_key

        session_service = InMemorySessionService()
        agent = create_safecode_navigator_agent()

        runner = Runner(
            agent=agent,
            app_name="safecode_navigator",
            session_service=session_service,
        )

        # Create a fresh session for this request
        session = await session_service.create_session(
            app_name="safecode_navigator",
            user_id="dev_user",
        )

        # Collect the final response text from the agent
        final_text = ""
        from google.genai import types as genai_types

        async for event in runner.run_async(
            user_id="dev_user",
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)]
            ),
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text

        explanation = parse_explanation(final_text, request.question)

        return AnalyzeResponse(
            security_check=security,
            question_type=QuestionType(q_type),
            risk_level=RiskLevel(risk),
            explanation=explanation,
            warning_checklist=warnings,
            coverage_confidence=0.85,
        )

    except Exception as e:
        return AnalyzeResponse(
            security_check=security,
            question_type=QuestionType(q_type),
            risk_level=RiskLevel(risk),
            warning_checklist=warnings,
            error=f"Agent error: {str(e)}"
        )


# ════════════════════════════════════════════════════════════
# RESPONSE PARSER
# ════════════════════════════════════════════════════════════

def parse_explanation(text: str, question: str) -> CodeExplanation:
    """
    Parses Gemini's free-text response into the structured CodeExplanation schema.
    Extracts each labeled section using regex, builds typed output.
    Falls back to full text in behavior field if sections are not found.
    """

    def extract(label: str, next_labels: List[str]) -> str:
        pattern = (
            rf"(?i){re.escape(label)}[\s\n]+"
            rf"(.*?)"
            rf"(?={'|'.join(re.escape(n) for n in next_labels)}|$)"
        )
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else ""

    order = [
        "PURPOSE", "BEHAVIOR", "INTENT RECONSTRUCTION",
        "INPUTS AND OUTPUTS", "DEPENDENCIES", "EDGE CASES",
        "RISK SURFACE", "SUGGESTED DOCUMENTATION", "QUESTIONS FOR MANAGER"
    ]

    purpose    = extract("PURPOSE",               order[1:])
    behavior   = extract("BEHAVIOR",              order[2:])
    intent     = extract("INTENT RECONSTRUCTION", order[3:])
    io         = extract("INPUTS AND OUTPUTS",    order[4:])
    deps_raw   = extract("DEPENDENCIES",          order[5:])
    edges_raw  = extract("EDGE CASES",            order[6:])
    risks_raw  = extract("RISK SURFACE",          order[7:])
    docs       = extract("SUGGESTED DOCUMENTATION", order[8:])
    qs_raw     = extract("QUESTIONS FOR MANAGER", [])

    def to_list(raw: str) -> List[str]:
        lines = [l.strip().lstrip("•-*0123456789. ") for l in raw.split("\n")]
        return [l for l in lines if len(l) > 8]

    # Build typed risk flags with auto severity detection
    risk_flags = []
    for line in to_list(risks_raw):
        sev = (
            "critical" if any(w in line.lower() for w in
                               ["critical", "crash", "race", "corrupt", "data loss"])
            else "high" if any(w in line.lower() for w in
                               ["break", "fail", "error", "null", "silent"])
            else "medium"
        )
        risk_flags.append(RiskFlag(
            description=line[:120],
            severity=RiskLevel(sev),
            reason=line
        ))

    # Fallback: if section parsing produced nothing, use full response as behavior
    if not purpose and not behavior:
        behavior = text

    return CodeExplanation(
        purpose=purpose or f"Analysis of: {question}",
        behavior=behavior or "See full analysis.",
        intent_reconstruction=intent or "Unable to infer from available code.",
        inputs_outputs=io or "See analysis above.",
        dependencies=to_list(deps_raw),
        edge_cases=to_list(edges_raw),
        risk_surface=risk_flags,
        suggested_documentation=docs or "# Refer to explanation above for documentation.",
        questions_for_manager=to_list(qs_raw),
    )