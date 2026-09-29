"""
api.py
------
FastAPI application that exposes the multi-agent learning path
generator as a REST API for the frontend to consume.

Endpoints
---------
POST /generate          – Full pipeline: profile → curriculum → resources → assessment
POST /assess            – Submit quiz answers and receive adaptation report
GET  /health            – Health check
"""

import os
import asyncio
from contextlib import asynccontextmanager
from functools import partial
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()  # Load .env before anything else


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    name: str = Field(..., example="Akhil")
    current_skills: list[str] = Field(
        ..., example=["Python basics", "HTML/CSS", "SQL"]
    )
    experience_years: int = Field(0, ge=0, le=50, example=1)
    target_role: str = Field(..., example="Machine Learning Engineer")
    weekly_hours: int = Field(10, ge=1, le=80, example=15)
    generate_quiz_for_module: Optional[int] = Field(
        1, ge=1, description="Which module number to generate an assessment for"
    )


class QuizSubmission(BaseModel):
    module_number: int = Field(..., ge=1)
    enriched_roadmap: str = Field(..., description="The roadmap context from /generate")
    answers: dict[str, str] = Field(
        ..., example={"q1": "B", "q2": "Gradient descent updates weights..."}
    )


class PipelineResponse(BaseModel):
    gap_report: str
    roadmap: str
    enriched_roadmap: str
    assessment: str


class AssessmentResponse(BaseModel):
    assessment_report: str


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate critical env vars at startup."""
    if not os.getenv("your_groq_api_key_here"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=sk-..."
        )
    yield


app = FastAPI(
    title="Personalized Learning Path Generator API",
    description=(
        "Multi-Agent AI backend (CrewAI + GPT-4o) that generates "
        "fully personalized learning paths, curated resources, and "
        "adaptive assessments."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend dev server (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
async def health_check():
    """Quick liveness probe."""
    return {"status": "ok", "model": os.getenv("OPENAI_MODEL", "gpt-4o")}


@app.post("/generate", response_model=PipelineResponse, tags=["Pipeline"])
async def generate_learning_path(profile: UserProfile):
    """
    Run the full 4-agent pipeline and return the complete learning path.

    CrewAI's kickoff() is synchronous; we run it in a thread-pool executor
    so it does not block FastAPI's async event loop (~30-120 s call).
    """
    try:
        from crew import run_pipeline

        profile_data = profile.model_dump(
            include={
                "name",
                "current_skills",
                "experience_years",
                "target_role",
                "weekly_hours",
            }
        )
        module_num = profile.generate_quiz_for_module or 1

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(run_pipeline, user_profile=profile_data, generate_quiz_for_module=module_num),
        )
        return PipelineResponse(
            gap_report=result["gap_report"],
            roadmap=result["roadmap"],
            enriched_roadmap=result["enriched_roadmap"],
            assessment=result["assessment"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/assess", response_model=AssessmentResponse, tags=["Assessment"])
async def submit_quiz(submission: QuizSubmission):
    """
    Submit learner quiz answers for a specific module and receive
    a mastery score + adaptation report for the next module.
    Runs CrewAI in a thread-pool executor to avoid blocking the event loop.
    """
    try:
        from crewai import Crew, Process
        from tasks import create_assessment_task
        from agents import create_assessment_adapter_agent

        def _run_assessment():
            agent = create_assessment_adapter_agent()
            task = create_assessment_task(
                module_number=submission.module_number,
                quiz_answers=submission.answers,
                assessment_agent=agent,
            )
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            outputs = getattr(result, "tasks_output", [])
            return outputs[0].raw if outputs else str(result)

        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, _run_assessment)
        return AssessmentResponse(assessment_report=report)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
