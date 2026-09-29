"""
agents.py
---------
Defines all four autonomous CrewAI agents for the
Personalized Learning Path Generator system.

Agents
------
1. Profiler & Diagnostic Agent  - Evaluates skills, pinpoints knowledge gaps
2. Curriculum Designer Agent    - Structures macro-roadmap into modules/milestones
3. Resource Curation Agent      - Attaches high-quality resources to every module
4. Assessment & Adaptation Agent - Generates quizzes and adapts upcoming modules

LLM Provider
------------
Uses Groq (via LiteLLM) by default. Set GROQ_API_KEY and optionally
GROQ_MODEL in your .env file. Falls back gracefully to OpenAI if
OPENAI_API_KEY is set instead.
"""

import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()  # Load .env before building agents

# Groq does not support LiteLLM's cache_breakpoint field — disable caching globally
os.environ["LITELLM_DISABLE_PROMPT_CACHING"] = "true"

# CrewAI 1.15 injects cache_breakpoint into every message for Anthropic prompt caching.
# Groq rejects this unknown field → monkey-patch mark_cache_breakpoint to be a no-op
# so the field is never added to messages when Groq is the active provider.
import crewai.llms.cache as _crewai_cache
import crewai.agents.crew_agent_executor as _crew_exec
import crewai.experimental.agent_executor as _exp_exec

def _noop_mark_cache_breakpoint(message: dict) -> dict:
    """No-op replacement: return message unchanged (no cache_breakpoint added)."""
    return message

_crewai_cache.mark_cache_breakpoint = _noop_mark_cache_breakpoint
_crew_exec.mark_cache_breakpoint = _noop_mark_cache_breakpoint
_exp_exec.mark_cache_breakpoint = _noop_mark_cache_breakpoint



# ---------------------------------------------------------------------------
# Shared LLM factory (temperature tuned per agent role)
# ---------------------------------------------------------------------------

def _llm(temperature: float = 0.3) -> LLM:
    """
    Return a CrewAI LLM instance backed by Groq (via litellm).

    Priority:
      1. GROQ_API_KEY  → uses groq/<GROQ_MODEL> via litellm
      2. OPENAI_API_KEY → falls back to openai/<OPENAI_MODEL>

    Set in .env:
        GROQ_API_KEY=gsk_...
        GROQ_MODEL=llama-3.1-8b-instant   # optional, default shown
    """
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        return LLM(
            model=f"groq/{model_name}",
            temperature=temperature,
            api_key=groq_key,
            caching=False,          # Groq rejects cache_breakpoint header
        )
    elif openai_key:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        return LLM(
            model=model_name,
            temperature=temperature,
            api_key=openai_key,
        )
    else:
        raise EnvironmentError(
            "No LLM API key found. Set GROQ_API_KEY (recommended) or "
            "OPENAI_API_KEY in your .env file."
        )


# ---------------------------------------------------------------------------
# 1. Profiler & Diagnostic Agent
# ---------------------------------------------------------------------------

def create_profiler_agent() -> Agent:
    """
    Evaluates the learner's existing knowledge and surfaces precise gaps
    that stand between their current state and their target career goal.
    """
    return Agent(
        role="Profiler & Diagnostic Specialist",
        goal=(
            "Conduct a thorough, empathetic assessment of the learner's current "
            "skill set, prior experience, and declared career ambition. "
            "Identify specific knowledge gaps — not vague weaknesses — and "
            "rank them by criticality so the Curriculum Designer can immediately "
            "prioritize the roadmap."
        ),
        backstory=(
            "You are a seasoned educational psychologist and technical recruiter "
            "with 15 years of experience in FAANG-level hiring panels and bootcamp "
            "curriculum design. You know exactly which skills separate a junior "
            "from a senior engineer, a data analyst from an ML engineer, or a "
            "beginner from an advanced practitioner in any tech domain. "
            "You ask only the most diagnostic questions — no fluff — and your "
            "gap reports are famous for their surgical precision. You never "
            "overwhelm the learner; you translate raw gaps into motivating "
            "opportunities."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_llm(temperature=0.2),
    )


# ---------------------------------------------------------------------------
# 2. Curriculum Designer Agent
# ---------------------------------------------------------------------------

def create_curriculum_designer_agent() -> Agent:
    """
    Converts the gap report into a sequenced, milestone-driven macro-roadmap.
    """
    return Agent(
        role="Curriculum Architect",
        goal=(
            "Transform the diagnosed skill gaps into a crystal-clear, sequential "
            "learning roadmap composed of logical modules, weekly milestones, and "
            "realistic time estimates. Each module must build on the last and "
            "directly address a gap identified by the Profiler. The roadmap must "
            "feel achievable yet ambitious — optimized for momentum and retention."
        ),
        backstory=(
            "You are a former head of curriculum at a top-tier online education "
            "platform (think Coursera or Udacity), with a doctorate in instructional "
            "design. You have architected learning journeys for over 200,000 learners "
            "across disciplines including software engineering, data science, cloud "
            "architecture, and product management. "
            "You believe deeply in spaced repetition, progressive overload, and "
            "project-based milestones. You structure roadmaps so that learners "
            "feel genuine momentum every single week. Your roadmaps are renowned "
            "for transforming overwhelmed beginners into job-ready professionals "
            "in the shortest defensible timeframe."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_llm(temperature=0.4),
    )


# ---------------------------------------------------------------------------
# 3. Resource Curation Agent
# ---------------------------------------------------------------------------

def create_resource_curator_agent() -> Agent:
    """
    Attaches specific, vetted, high-quality learning resources to every
    module produced by the Curriculum Designer.
    """
    return Agent(
        role="Resource Curation Specialist",
        goal=(
            "For every module in the roadmap, identify and attach the single "
            "best free resource, the single best paid resource, one practical "
            "coding exercise or project, and one piece of official documentation. "
            "All resources must be real, up-to-date, directly relevant, and "
            "explicitly matched to the module learning objective. "
            "Include estimated read/watch time and difficulty rating for each."
        ),
        backstory=(
            "You are a hyperpolymath librarian-turned-developer advocate who has "
            "spent a decade curating technical content for engineering teams at "
            "Google, Meta, and several YC startups. You have an encyclopedic "
            "knowledge of developer education platforms: freeCodeCamp, MDN, "
            "official Python/JS/React docs, MIT OpenCourseWare, Coursera, "
            "Udemy, Frontend Masters, roadmap.sh, LeetCode, HackerRank, "
            "Kaggle, fast.ai, and dozens more. "
            "You ruthlessly filter out outdated, low-quality, or misleading "
            "content. Your curated lists are the ones engineers actually bookmark."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_llm(temperature=0.3),
    )


# ---------------------------------------------------------------------------
# 4. Assessment & Adaptation Agent
# ---------------------------------------------------------------------------

def create_assessment_adapter_agent() -> Agent:
    """
    Generates targeted quizzes after each module and dynamically adapts the
    subsequent roadmap based on learner performance signals.
    """
    return Agent(
        role="Assessment & Adaptive Learning Specialist",
        goal=(
            "After each completed module, generate a concise but comprehensive "
            "5-10 question quiz (mix of MCQ, short-answer, and code-completion) "
            "that accurately measures mastery of that module objectives. "
            "Analyze the results, compute a mastery score, and emit a structured "
            "adaptation report: which topics need reinforcement, whether the pace "
            "should slow or accelerate, and what specific adjustments to make to "
            "the next module — including adding, removing, or reordering content."
        ),
        backstory=(
            "You are an adaptive learning engineer who pioneered data-driven "
            "personalization at one of the world's largest EdTech platforms. "
            "Your algorithms have helped millions of learners reach their goals "
            "40% faster than static curricula. You combine psychometric theory "
            "(IRT, Bloom's taxonomy) with real-time performance analytics to "
            "build feedback loops that actually move the needle. "
            "You know that a 70% quiz score means something very different from "
            "a 40% score, and you respond with the precise intervention — not a "
            "generic 'review this module'. Your quizzes are fair, well-calibrated, "
            "and immune to simple memorization tricks."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_llm(temperature=0.3),
    )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def build_all_agents() -> dict:
    """Return all four agents keyed by short name."""
    return {
        "profiler": create_profiler_agent(),
        "curriculum_designer": create_curriculum_designer_agent(),
        "resource_curator": create_resource_curator_agent(),
        "assessment_adapter": create_assessment_adapter_agent(),
    }
