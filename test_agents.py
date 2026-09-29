"""
test_agents.py
--------------
Local smoke-test that verifies agent + task + crew wiring WITHOUT
making any real OpenAI API calls.

Run with:
    source venv/bin/activate
    python test_agents.py
"""

import os
import sys
from dotenv import load_dotenv

# Load real .env (GROQ_API_KEY etc.) before importing agents
load_dotenv()

# Safety fallback so the file still works without a .env
os.environ.setdefault("GROQ_API_KEY", "gsk-placeholder")
os.environ.setdefault("GROQ_MODEL", "llama-3.1-8b-instant")


def test_agents_import():
    """All four agent constructors should import and instantiate without errors."""
    from agents import (
        create_profiler_agent,
        create_curriculum_designer_agent,
        create_resource_curator_agent,
        create_assessment_adapter_agent,
        build_all_agents,
    )

    profiler = create_profiler_agent()
    assert profiler.role == "Profiler & Diagnostic Specialist"
    print(f"  [PASS] Profiler agent: role='{profiler.role}'")

    designer = create_curriculum_designer_agent()
    assert designer.role == "Curriculum Architect"
    print(f"  [PASS] Curriculum designer: role='{designer.role}'")

    curator = create_resource_curator_agent()
    assert curator.role == "Resource Curation Specialist"
    print(f"  [PASS] Resource curator: role='{curator.role}'")

    adapter = create_assessment_adapter_agent()
    assert adapter.role == "Assessment & Adaptive Learning Specialist"
    print(f"  [PASS] Assessment adapter: role='{adapter.role}'")

    all_agents = build_all_agents()
    assert len(all_agents) == 4
    print(f"  [PASS] build_all_agents() returned {len(all_agents)} agents")


def test_tasks_import():
    """All four task constructors should import and build Task objects."""
    from tasks import (
        create_profiling_task,
        create_curriculum_task,
        create_resource_task,
        create_assessment_task,
    )

    sample_profile = {
        "name": "TestUser",
        "current_skills": ["Python", "SQL"],
        "experience_years": 1,
        "target_role": "ML Engineer",
        "weekly_hours": 10,
    }

    t1 = create_profiling_task(sample_profile)
    assert "TestUser" in t1.description
    print(f"  [PASS] profiling_task created (description length: {len(t1.description)})")

    t2 = create_curriculum_task()
    assert t2.description is not None
    print(f"  [PASS] curriculum_task created")

    t3 = create_resource_task()
    assert t3.description is not None
    print(f"  [PASS] resource_task created")

    t4 = create_assessment_task(module_number=2)
    assert "Module 2" in t4.description
    print(f"  [PASS] assessment_task created for module 2")

    t5 = create_assessment_task(module_number=1, quiz_answers={"q1": "B", "q2": "gradient descent"})
    assert "Learner's Quiz Answers" in t5.description
    print(f"  [PASS] assessment_task with answers created")


def test_crew_assembly():
    """Crew should assemble all 4 agents and 4 tasks without errors."""
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

    sample_profile = {
        "name": "Akhil",
        "current_skills": ["Python", "HTML"],
        "experience_years": 0,
        "target_role": "Full Stack Developer",
        "weekly_hours": 12,
    }

    profiler = create_profiler_agent()
    designer = create_curriculum_designer_agent()
    curator = create_resource_curator_agent()
    adapter = create_assessment_adapter_agent()

    crew = Crew(
        agents=[profiler, designer, curator, adapter],
        tasks=[
            create_profiling_task(sample_profile, profiler),
            create_curriculum_task(designer),
            create_resource_task(curator),
            create_assessment_task(assessment_agent=adapter),
        ],
        process=Process.sequential,
        verbose=False,
    )

    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4
    print(f"  [PASS] Crew assembled: {len(crew.agents)} agents, {len(crew.tasks)} tasks")


def main():
    tests = [
        ("Agent instantiation", test_agents_import),
        ("Task creation",       test_tasks_import),
        ("Crew assembly",       test_crew_assembly),
    ]

    passed = failed = 0
    for name, fn in tests:
        print(f"\n--- {name} ---")
        try:
            fn()
            passed += 1
        except Exception as exc:
            print(f"  [FAIL] {exc}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    else:
        print("All smoke tests passed! Ready to run with a real OPENAI_API_KEY.")


if __name__ == "__main__":
    main()
