"""
tasks.py
--------
Defines the four sequential CrewAI Tasks that drive the
Personalized Learning Path Generator pipeline.

Pipeline order
--------------
1. profiling_task        --> gap_report
2. curriculum_task       --> roadmap
3. resource_task         --> enriched_roadmap
4. assessment_task       --> quiz + adaptation_report
"""

from crewai import Task
from agents import (
    create_profiler_agent,
    create_curriculum_designer_agent,
    create_resource_curator_agent,
    create_assessment_adapter_agent,
)


# ---------------------------------------------------------------------------
# Task 1 – Skill Profiling & Gap Analysis
# ---------------------------------------------------------------------------

def create_profiling_task(
    user_profile: dict,
    profiler_agent=None,
) -> Task:
    """
    Input  : user_profile dict with keys:
               - name          (str)
               - current_skills (list[str])
               - experience_years (int)
               - target_role   (str)
               - weekly_hours  (int)  -- hours available to study per week
    Output : A structured gap report (markdown) with:
               - Confirmed skills
               - Critical gaps (ranked)
               - Nice-to-have gaps
               - Recommended entry point for the curriculum
    """
    if profiler_agent is None:
        profiler_agent = create_profiler_agent()

    name = user_profile.get("name", "the learner")
    skills = ", ".join(user_profile.get("current_skills", []))
    exp = user_profile.get("experience_years", 0)
    target = user_profile.get("target_role", "Software Engineer")
    hours = user_profile.get("weekly_hours", 10)

    description = f"""
You are evaluating a learner named {name}.

**Learner Profile**
- Current skills: {skills}
- Years of experience: {exp}
- Target role / career goal: {target}
- Available study time: {hours} hours per week

**Your Task**
1. Confirm which declared skills are genuinely solid vs. superficial based on the target role requirements.
2. Identify every critical knowledge gap that would prevent {name} from being hired for the role "{target}".
3. Rank critical gaps from highest to lowest priority (P1 = must fix first).
4. List any nice-to-have gaps that would differentiate the candidate.
5. Recommend the single best entry point for their curriculum (which gap to attack first).

**Output Format** – Return a valid Markdown document with these exact sections:
## Confirmed Strengths
## Critical Gaps (Ranked P1 → Pn)
## Nice-to-Have Gaps
## Recommended Entry Point
## Summary Paragraph
"""

    return Task(
        description=description,
        expected_output=(
            "A detailed Markdown gap report with confirmed strengths, ranked "
            "critical gaps, nice-to-have gaps, recommended entry point, and a "
            "summary paragraph."
        ),
        agent=profiler_agent,
    )


# ---------------------------------------------------------------------------
# Task 2 – Curriculum Design
# ---------------------------------------------------------------------------

def create_curriculum_task(curriculum_agent=None) -> Task:
    """
    Consumes the gap report produced by Task 1 and generates a
    sequenced, milestone-driven learning roadmap.
    """
    if curriculum_agent is None:
        curriculum_agent = create_curriculum_designer_agent()

    description = """
Using the gap report from the Profiler Agent, design a complete, sequenced
learning roadmap.

**Requirements**
- Break the roadmap into 4-8 modules, ordered from foundational to advanced.
- Each module must include:
    - Module number and title
    - Learning objective (one sentence, outcome-focused)
    - Key topics covered (bullet list)
    - Estimated duration (e.g., "1-2 weeks, 10 hrs/wk")
    - Success milestone: a concrete deliverable or checkpoint the learner completes
- The final module must include a capstone project that is directly relevant to the target role.

**Output Format** – Return a valid Markdown document with this structure:
# Learning Roadmap: <Target Role>

## Module 1: <Title>
### Objective
### Topics
### Estimated Duration
### Success Milestone

...repeat for all modules...

## Capstone Project
"""

    return Task(
        description=description,
        expected_output=(
            "A complete Markdown learning roadmap with 4-8 numbered modules, "
            "each with objective, topics, estimated duration, and success milestone, "
            "plus a capstone project section."
        ),
        agent=curriculum_agent,
    )


# ---------------------------------------------------------------------------
# Task 3 – Resource Curation
# ---------------------------------------------------------------------------

def create_resource_task(resource_agent=None) -> Task:
    """
    Attaches vetted, high-quality resources to every module in the roadmap.
    """
    if resource_agent is None:
        resource_agent = create_resource_curator_agent()

    description = """
Using the learning roadmap from the Curriculum Architect, enrich each module
with carefully selected learning resources.

**For every module, provide EXACTLY:**
1. Best Free Resource   – title, URL, platform, estimated time, difficulty (Beginner/Intermediate/Advanced)
2. Best Paid Resource   – title, URL, platform, price range, estimated time, difficulty
3. Hands-On Exercise    – title, URL or description, estimated time (coding challenge, mini-project, or lab)
4. Official Docs Reference – title, URL, the specific section most relevant to this module

**Rules**
- Only recommend resources that were actually available as of 2024. Do not invent URLs.
- Mark any resource you are less than 90% confident about with "(verify link)".
- Keep descriptions to 1-2 sentences max per resource.

**Output Format** – Return the enriched roadmap in Markdown, adding a
"### Resources" subsection under each existing module section.
"""

    return Task(
        description=description,
        expected_output=(
            "The full Markdown roadmap with a '### Resources' subsection added "
            "under each module, containing the 4 required resource types with "
            "all specified metadata."
        ),
        agent=resource_agent,
    )


# ---------------------------------------------------------------------------
# Task 4 – Assessment & Adaptation
# ---------------------------------------------------------------------------

def create_assessment_task(
    module_number: int = 1,
    quiz_answers: dict | None = None,
    assessment_agent=None,
) -> Task:
    """
    Generates a quiz for a specific module number, and (if quiz_answers
    are provided) produces an adaptation report for the following module.

    Parameters
    ----------
    module_number : int
        Which module to generate a quiz for.
    quiz_answers  : dict | None
        { "q1": "learner answer", "q2": "learner answer", ... }
        If None, only the quiz is generated (no adaptation report).
    """
    if assessment_agent is None:
        assessment_agent = create_assessment_adapter_agent()

    answer_block = ""
    if quiz_answers:
        formatted = "\n".join(
            f"  Q{k}: {v}" for k, v in quiz_answers.items()
        )
        answer_block = f"""
**Learner's Quiz Answers**
{formatted}

After evaluating the answers:
- Compute a mastery score (0-100).
- Identify exactly which topics were strong vs. weak.
- Write an adaptation report recommending:
    a) Topics to reinforce in a follow-up micro-session before Module {module_number + 1}
    b) Whether to expand, compress, or reorder Module {module_number + 1} content
    c) An adjusted pace recommendation (slow / maintain / accelerate)
"""
    else:
        answer_block = (
            "(No answers provided yet — generate only the quiz for Module "
            f"{module_number}.)"
        )

    description = f"""
Using the enriched roadmap, perform the following for **Module {module_number}**:

**Part A – Quiz Generation**
Create a 7-question quiz for Module {module_number} with:
- 3 Multiple-choice questions (4 options each, mark correct answer)
- 2 Short-answer questions (1-3 sentences expected)
- 2 Code-completion or debug questions (provide a code snippet with blanks or bugs)

Each question must directly test a specific learning objective from Module {module_number}.
Include the answer key at the end under "## Answer Key".

{answer_block}

**Output Format** – Return a valid Markdown document:
# Module {module_number} Assessment

## Quiz
### Q1 (MCQ) ...
### Q2 (MCQ) ...
### Q3 (MCQ) ...
### Q4 (Short Answer) ...
### Q5 (Short Answer) ...
### Q6 (Code) ...
### Q7 (Code) ...

## Answer Key

## Adaptation Report  ← (only if answers were provided)
"""

    return Task(
        description=description,
        expected_output=(
            f"A Markdown document with a 7-question quiz for Module {module_number} "
            "(MCQ, short-answer, and code questions), an answer key, and — if "
            "answers were supplied — a structured adaptation report."
        ),
        agent=assessment_agent,
    )
