"""
crew.py
-------
Assembles all agents and tasks into a cohesive CrewAI Crew
and exposes a run_pipeline() function that drives the full
end-to-end learning path generation workflow.
"""

from crewai import Crew, Process
from agents import (
    create_profiler_agent,
    create_curriculum_designer_agent,
    create_resource_curator_agent,
    create_assessment_adapter_agent,
)
from tasks import (
    create_profiling_task,
    create_curriculum_task,
    create_resource_task,
    create_assessment_task,
)


def run_pipeline(user_profile: dict, generate_quiz_for_module: int = 1) -> dict:
    """
    Execute the full 4-agent pipeline sequentially.

    Parameters
    ----------
    user_profile : dict
        {
            "name": str,
            "current_skills": list[str],
            "experience_years": int,
            "target_role": str,
            "weekly_hours": int
        }
    generate_quiz_for_module : int
        Which module number to generate an assessment for (default = 1).

    Returns
    -------
    dict with keys:
        "gap_report"      – output of Task 1
        "roadmap"         – output of Task 2
        "enriched_roadmap"– output of Task 3
        "assessment"      – output of Task 4
    """

    # --- Instantiate agents ---
    profiler = create_profiler_agent()
    curriculum_designer = create_curriculum_designer_agent()
    resource_curator = create_resource_curator_agent()
    assessment_adapter = create_assessment_adapter_agent()

    # --- Instantiate tasks (sequential: each feeds into the next) ---
    task_profile = create_profiling_task(user_profile, profiler)
    task_curriculum = create_curriculum_task(curriculum_designer)
    task_resources = create_resource_task(resource_curator)
    task_assessment = create_assessment_task(
        module_number=generate_quiz_for_module,
        assessment_agent=assessment_adapter,
    )

    # --- Assemble Crew ---
    crew = Crew(
        agents=[profiler, curriculum_designer, resource_curator, assessment_adapter],
        tasks=[task_profile, task_curriculum, task_resources, task_assessment],
        process=Process.sequential,  # Tasks run in order; output feeds context
        verbose=True,
    )

    # --- Kick off ---
    result = crew.kickoff()

    # CrewAI >=0.30 returns a CrewOutput object; extract individual task outputs
    task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []

    def _get(index: int) -> str:
        try:
            return task_outputs[index].raw if task_outputs else str(result)
        except IndexError:
            return ""

    return {
        "gap_report": _get(0),
        "roadmap": _get(1),
        "enriched_roadmap": _get(2),
        "assessment": _get(3),
        "full_crew_output": str(result),
    }
