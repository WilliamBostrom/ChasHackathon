import asyncio
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query

from ..utils import log
from .. import conf
from ..models import (
    UserProfile,
    Routine,
    CheckIn,
    Reflection,
    AIPlan,
    Activity,
    UserProfileResponse,
    RoutineListResponse,
    CheckInListResponse,
    ReflectionListResponse,
    AIPlanListResponse,
    ActivityListResponse,
    SuccessResponse,
)
# from .utils import RequestPrincipal # NOTE: uncomment to use auth

logger = log.get_logger(__name__)
router = APIRouter()

#### Utilities ####


def get_app_version() -> str:
    """Read version from pyproject.toml."""
    try:
        # Look for pyproject.toml from the current file up to project root
        current_path = Path(__file__).resolve()
        for parent in [current_path] + list(current_path.parents):
            pyproject_path = parent / "pyproject.toml"
            if pyproject_path.exists():
                content = pyproject_path.read_text()
                for line in content.split("\n"):
                    if line.strip().startswith("version = "):
                        # Extract version from 'version = "0.1.0"'
                        return line.split("=")[1].strip().strip("\"'")
                break
        return "unknown"
    except Exception as e:
        logger.warning(f"Failed to read version from pyproject.toml: {e}")
        return "unknown"


#### Routes ####


@router.get("/")
async def root():
    return {"message": "Hello World"}


# ============================================================================
# Frontend API Endpoints (integrated with Database)
# ============================================================================

# Use a default user for demo purposes
DEFAULT_USER_ID = "default-user"

@router.get("/tasks")
async def get_tasks(request: Request, date: str = Query(...)):
    """Get tasks for a specific date."""
    if not conf.USE_DATABASE:
        return []
    
    try:
        db_client = request.app.state.db_client
        activities = await db_client.get_activities(DEFAULT_USER_ID, date)
        
        # Filter and format tasks
        tasks = []
        for activity in activities:
            if activity.get("type") in ["task", "todo", "gym", "meeting"]:
                task_data = {
                    "id": activity.get("id", f"task-{len(tasks)}"),
                    "type": activity.get("type", "todo"),
                    "title": activity.get("title", ""),
                    "completed": activity.get("completed", False),
                }
                if activity.get("duration"):
                    task_data["duration"] = activity["duration"]
                if activity.get("startTime"):
                    task_data["time"] = activity["startTime"]
                tasks.append(task_data)
        
        return tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return []


@router.post("/tasks")
async def create_task(request: Request, task: dict):
    """Create a new task."""
    logger.info(f"POST /tasks - USE_DATABASE={conf.USE_DATABASE}")
    
    if not conf.USE_DATABASE:
        logger.warning("Database is disabled - returning stub response")
        return {"id": f"task-{uuid.uuid4()}", **task}
    
    try:
        if not hasattr(request.app.state, "db_client"):
            logger.error("Database client not initialized")
            raise HTTPException(status_code=500, detail="Database client not initialized")
            
        db_client = request.app.state.db_client
        task_id = str(uuid.uuid4())
        date = task.get("date", time.strftime("%Y-%m-%d"))
        
        logger.info(f"Creating task: {task_id} for date: {date}")
        
        activity_data = {
            "id": task_id,
            "type": task.get("type", "todo"),
            "title": task.get("title", ""),
            "completed": task.get("completed", False),
        }
        
        if task.get("duration"):
            activity_data["duration"] = task["duration"]
        if task.get("time"):
            activity_data["startTime"] = task["time"]
        if task.get("description"):
            activity_data["description"] = task["description"]
        
        await db_client.insert_activity(DEFAULT_USER_ID, date, "task", activity_data)
        logger.info(f"Successfully created task: {task_id}")
        
        return {"id": task_id, **task}
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}")
async def update_task(request: Request, task_id: str, updates: dict):
    """Update a task."""
    if not conf.USE_DATABASE:
        return {"id": task_id, **updates}
    
    try:
        db_client = request.app.state.db_client
        date = updates.get("date", time.strftime("%Y-%m-%d"))

        # Fetch existing activities for the date and find the current task payload
        activities = await db_client.get_activities(DEFAULT_USER_ID, date)
        current = next((a for a in activities if a.get("id") == task_id), None)
        if not current:
            # If not found, return 404-like error
            raise HTTPException(status_code=404, detail="Task not found")

        # Merge updates onto the existing JSON payload
        merged = {**current, **updates}
        # Ensure id and type are preserved
        merged["id"] = task_id
        if "type" not in merged:
            merged["type"] = current.get("type", "task")

        await db_client.update_activity(DEFAULT_USER_ID, date, task_id, merged)

        return {"id": task_id, **merged}
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(request: Request, task_id: str):
    """Delete a task."""
    if not conf.USE_DATABASE:
        return {"success": True}

    try:
        db_client = request.app.state.db_client
        # We operate on today's list (UI shows today's tasks)
        date = time.strftime("%Y-%m-%d")
        await db_client.delete_activity(DEFAULT_USER_ID, date, task_id)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/morning-checkin")
async def morning_checkin(request: Request, data: dict):
    """Submit morning check-in."""
    if not conf.USE_DATABASE:
        return {"success": True, "data": data}
    
    try:
        db_client = request.app.state.db_client
        date = data.get("date", time.strftime("%Y-%m-%d"))
        
        checkin_data = {
            "feeling": data.get("feeling", ""),
            "focus": data.get("focus", ""),
            "timestamp": time.time(),
        }
        
        await db_client.insert_checkin(DEFAULT_USER_ID, date, checkin_data)
        
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error saving morning check-in: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-plan")
async def generate_plan(request: Request, data: dict):
    """Generate an AI day plan."""
    if not conf.USE_DATABASE:
        return {
            "date": data.get("date"),
            "blocks": [],
            "morningRoutine": [],
            "eveningRoutine": []
        }
    
    try:
        db_client = request.app.state.db_client
        date = data.get("date", time.strftime("%Y-%m-%d"))
        
        # Create a sample plan for demonstration
        plan_data = {
            "blocks": [
                {
                    "id": f"block-{uuid.uuid4()}",
                    "title": "Deep Work Session",
                    "startTime": "09:00",
                    "endTime": "11:00",
                    "duration": 120,
                    "type": "focus"
                },
                {
                    "id": f"block-{uuid.uuid4()}",
                    "title": "Break",
                    "startTime": "11:00",
                    "endTime": "11:15",
                    "duration": 15,
                    "type": "break"
                }
            ],
            "morningRoutine": ["Meditation", "Exercise", "Healthy breakfast"],
            "eveningRoutine": ["Review day", "Plan tomorrow", "Wind down"]
        }
        
        await db_client.insert_ai_plan(DEFAULT_USER_ID, date, plan_data)
        
        return {"date": date, **plan_data}
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan")
async def get_plan(request: Request, date: str = Query(...)):
    """Get day plan for a specific date."""
    if not conf.USE_DATABASE:
        return {
            "date": date,
            "blocks": [],
            "morningRoutine": [],
            "eveningRoutine": []
        }
    
    try:
        db_client = request.app.state.db_client
        plans = await db_client.get_ai_plans(DEFAULT_USER_ID, date)
        
        if plans:
            plan = plans[0]
            return {
                "date": date,
                "blocks": plan.get("blocks", []),
                "morningRoutine": plan.get("morningRoutine", []),
                "eveningRoutine": plan.get("eveningRoutine", [])
            }
        
        return {
            "date": date,
            "blocks": [],
            "morningRoutine": [],
            "eveningRoutine": []
        }
    except Exception as e:
        logger.error(f"Error getting plan: {e}")
        return {
            "date": date,
            "blocks": [],
            "morningRoutine": [],
            "eveningRoutine": []
        }


@router.post("/focus/{block_id}/start")
async def start_focus(request: Request, block_id: str):
    """Start a focus block."""
    if not conf.USE_DATABASE:
        return {"success": True, "blockId": block_id}
    
    try:
        # Could add tracking logic here
        return {"success": True, "blockId": block_id}
    except Exception as e:
        logger.error(f"Error starting focus block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/focus/{block_id}/feedback")
async def focus_feedback(request: Request, block_id: str, feedback: dict):
    """Submit focus feedback."""
    if not conf.USE_DATABASE:
        return {"success": True}
    
    try:
        db_client = request.app.state.db_client
        date = time.strftime("%Y-%m-%d")
        
        reflection_data = {
            "blockId": block_id,
            "feedback": feedback.get("feedback", ""),
            "timestamp": time.time(),
        }
        
        await db_client.insert_reflection(DEFAULT_USER_ID, date, reflection_data)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error saving focus feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/afternoon-reflection")
async def afternoon_reflection(request: Request, data: dict):
    """Submit afternoon reflection."""
    if not conf.USE_DATABASE:
        return {"success": True, "data": data}
    
    try:
        db_client = request.app.state.db_client
        date = data.get("date", time.strftime("%Y-%m-%d"))
        
        reflection_data = {
            "accomplishments": data.get("accomplishments", ""),
            "challenges": data.get("challenges", ""),
            "learnings": data.get("learnings", ""),
            "timestamp": time.time(),
        }
        
        await db_client.insert_reflection(DEFAULT_USER_ID, date, reflection_data)
        
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error saving afternoon reflection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-summary")
async def ai_summary(request: Request, date: str = Query(...)):
    """Get AI summary for a date."""
    if not conf.USE_DATABASE:
        return {"summary": "No data available yet", "date": date}
    
    try:
        db_client = request.app.state.db_client
        reflections = await db_client.get_reflections(DEFAULT_USER_ID, date, date)
        
        if reflections:
            reflection = reflections[0]
            summary = f"Accomplishments: {reflection.get('accomplishments', 'None')}\n"
            summary += f"Challenges: {reflection.get('challenges', 'None')}\n"
            summary += f"Learnings: {reflection.get('learnings', 'None')}"
            return {"summary": summary, "date": date}
        
        return {"summary": "No data available yet", "date": date}
    except Exception as e:
        logger.error(f"Error getting AI summary: {e}")
        return {"summary": "No data available yet", "date": date}


@router.get("/weekly-summary")
async def weekly_summary(request: Request, week: int = Query(...)):
    """Get weekly summary."""
    if not conf.USE_DATABASE:
        return {
            "weekNumber": week,
            "suggestedGoals": [],
            "insights": "No data available yet",
            "completionRate": 0
        }
    
    try:
        # This would need more sophisticated date handling
        return {
            "weekNumber": week,
            "suggestedGoals": [
                {
                    "id": "goal-1",
                    "title": "Improve focus time",
                    "description": "Increase deep work sessions",
                    "aiReasoning": "Based on your recent patterns"
                }
            ],
            "insights": "You've been making good progress this week!",
            "completionRate": 75
        }
    except Exception as e:
        logger.error(f"Error getting weekly summary: {e}")
        return {
            "weekNumber": week,
            "suggestedGoals": [],
            "insights": "No data available yet",
            "completionRate": 0
        }


@router.post("/micro-goal/select")
async def select_goal(request: Request, data: dict):
    """Select a micro goal."""
    if not conf.USE_DATABASE:
        return {"success": True}
    
    try:
        # Could store selected goal in database
        return {"success": True}
    except Exception as e:
        logger.error(f"Error selecting goal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    request: Request,
    quick: bool = Query(False, description="Return basic status only"),
    services: Optional[str] = Query(
        None,
        description="Comma-separated list of services to check (couchbase,temporal,twilio)",
    ),
    timeout: float = Query(
        2.0, description="Timeout in seconds for health checks", ge=0.1, le=10.0
    ),
):
    """Fast health check endpoint."""
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "service": "backend",
        "timestamp": int(start_time),
    }

    # Add more extensive response if error surfacing is enabled
    if conf.get_http_expose_errors():
        health_status["dev_info"] = {
            "version": get_app_version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "features": {
                "twilio": conf.USE_TWILIO,
                "auth": conf.USE_AUTH,
            },
            "configuration": {
                "log_level": conf.get_log_level(),
                "http_autoreload": conf.env.parse(conf.HTTP_AUTORELOAD),
            },
        }

    # Parse services filter
    services_to_check = None
    if services:
        services_to_check = [s.strip().lower() for s in services.split(",")]

    # Quick mode - just return basic status
    if quick:
        health_status["mode"] = "quick"
        health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        return health_status

    await asyncio.wait_for(
        _check_all_services(request, health_status, services_to_check), timeout=timeout
    )

    # Add response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    return health_status


async def _check_all_services(
    request: Request, health_status: dict, services_filter: Optional[List[str]]
):
    """Check all enabled services with proper error handling."""

    # Check Database if requested
    if not services_filter or "couchbase" in services_filter:
        if conf.USE_DATABASE and hasattr(request.app.state, "couchbase_client"):
            try:
                couchbase_client = request.app.state.couchbase_client
                # Simple health check - try to access the cluster
                if couchbase_client.cluster is not None:
                    health_status["couchbase"] = {
                        "connected": True,
                        "status": "connected",
                        "bucket": couchbase_client.config.bucket_name,
                    }
                else:
                    health_status["couchbase"] = {
                        "connected": False,
                        "status": "disconnected",
                    }
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["couchbase"] = {
                    "connected": False,
                    "status": "error",
                    "message": str(e),
                }
                health_status["status"] = "degraded"
        else:
            health_status["couchbase"] = {
                "status": "disabled",
                "message": "Database is disabled (USE_COUCHBASE=False)",
            }

    # Check Temporal if requested (with timeout protection)
    if not services_filter or "temporal" in services_filter:
        if hasattr(request.app.state, "temporal_client"):
            temporal_client = request.app.state.temporal_client
            # Use health_check if available, otherwise use is_connected with timeout
            if hasattr(temporal_client, "health_check"):
                temporal_health = temporal_client.health_check()
            else:
                # Wrap potentially blocking call in timeout
                try:
                    is_connected = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, temporal_client.is_connected
                        ),
                        timeout=0.5,
                    )
                    temporal_health = {
                        "connected": is_connected,
                        "status": "connected" if is_connected else "disconnected",
                    }
                except asyncio.TimeoutError:
                    temporal_health = {
                        "connected": False,
                        "status": "timeout",
                        "message": "Connection check timed out",
                    }

            health_status["temporal"] = temporal_health
            if not temporal_health.get("connected", False):
                health_status["status"] = "degraded"
        else:
            health_status["temporal"] = {
                "status": "not_configured",
                "message": "Temporal client not configured (run add-temporal-client to set up)",
            }

    # Check Twilio if requested
    if not services_filter or "twilio" in services_filter:
        if conf.USE_TWILIO:
            twilio_client = request.app.state.twilio_client
            # Use health_check if available
            if hasattr(twilio_client, "health_check"):
                twilio_health = twilio_client.health_check()
            else:
                twilio_health = {"connected": True, "status": "connected"}
            health_status["twilio"] = twilio_health
        else:
            health_status["twilio"] = {
                "status": "disabled",
                "message": "Twilio is disabled (USE_TWILIO=False)",
            }

    return health_status


# PostgreSQL route example using SQLModel (uncomment when using PostgreSQL)
#
# from .utils import DBSession
# from ..db.models import User, create_user, get_user, get_users
#
# @router.post("/users", response_model=User)
# async def create_user_route(user: User, session: DBSession):
#     """Create a new user."""
#     return await create_user(session, user)
#
# @router.get("/users/{user_id}", response_model=User)
# async def get_user_route(user_id: int, session: DBSession):
#     """Get a user by ID."""
#     user = await get_user(session, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
#
# @router.get("/users", response_model=list[User])
# async def list_users_route(session: DBSession, skip: int = 0, limit: int = 100):
#     """List all users with pagination."""
#     return await get_users(session, skip=skip, limit=limit)


# Database route example (uncomment when using Database)
#
# from .utils import DatabaseDB
# from ..clients.couchbase_models import DatabaseUser, create_user, get_user, list_users
#
# @router.post("/cb/users", response_model=DatabaseUser)
# async def create_user_cb(user: DatabaseUser, cb: DatabaseDB):
#     """Create a user in Database."""
#     user_id = await create_user(cb, user)
#     user.id = user_id
#     return user
#
# @router.get("/cb/users/{user_id}", response_model=DatabaseUser)
# async def get_user_cb(user_id: str, cb: DatabaseDB):
#     """Get a user from Database."""
#     user = await get_user(cb, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
#
# @router.get("/cb/users", response_model=list[DatabaseUser])
# async def list_users_cb(cb: DatabaseDB, limit: int = 100, offset: int = 0):
#     """List users from Database."""
#     return await list_users(cb, limit=limit, offset=offset)


# ============================================================================
# Temporal Workflow Routes
# ============================================================================

import uuid
from ..workflows.morning_check import (
    MorningCheckWorkflow,
    MorningCheckInput,
)
from ..workflows.focus_loop import (
    FocusLoopWorkflow,
    FocusLoopInput,
    FocusBlockInfo,
)
from ..workflows.daily_reflection import (
    DailyReflectionWorkflow,
    DailyReflectionInput,
)
from ..workflows.weekly_growth import (
    WeeklyGrowthWorkflow,
    WeeklyGrowthInput,
)
from ..workflows.meeting_scheduler import (
    MeetingSchedulerWorkflow,
    MeetingSchedulerInput,
)


@router.post("/api/workflows/morning-check")
async def start_morning_check_workflow(
    request: Request, workflow_input: MorningCheckInput
):
    """Start a MorningCheck workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    workflow_id = f"morning-check-{workflow_input.user_id}-{workflow_input.date}"

    try:
        handle = await temporal_client.start_workflow(
            MorningCheckWorkflow.run,
            args=[workflow_input],
            id=workflow_id,
            task_queue=temporal_client._config.task_queue,
        )
        return {
            "workflow_id": workflow_id,
            "message": "MorningCheck workflow started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start MorningCheck workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/workflows/focus-loop")
async def start_focus_loop_workflow(request: Request, workflow_input: FocusLoopInput):
    """Start a FocusLoop workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    workflow_id = f"focus-loop-{workflow_input.block.user_id}-{workflow_input.block.block_id}"

    try:
        handle = await temporal_client.start_workflow(
            FocusLoopWorkflow.run,
            args=[workflow_input],
            id=workflow_id,
            task_queue=temporal_client._config.task_queue,
        )
        return {
            "workflow_id": workflow_id,
            "message": "FocusLoop workflow started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start FocusLoop workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/workflows/daily-reflection")
async def start_daily_reflection_workflow(
    request: Request, workflow_input: DailyReflectionInput
):
    """Start a DailyReflection workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    workflow_id = f"daily-reflection-{workflow_input.user_id}-{workflow_input.date}"

    try:
        handle = await temporal_client.start_workflow(
            DailyReflectionWorkflow.run,
            args=[workflow_input],
            id=workflow_id,
            task_queue=temporal_client._config.task_queue,
        )
        return {
            "workflow_id": workflow_id,
            "message": "DailyReflection workflow started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start DailyReflection workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/workflows/weekly-growth")
async def start_weekly_growth_workflow(
    request: Request, workflow_input: WeeklyGrowthInput
):
    """Start a WeeklyGrowth workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    workflow_id = f"weekly-growth-{workflow_input.user_id}-{workflow_input.week_start}"

    try:
        handle = await temporal_client.start_workflow(
            WeeklyGrowthWorkflow.run,
            args=[workflow_input],
            id=workflow_id,
            task_queue=temporal_client._config.task_queue,
        )
        return {
            "workflow_id": workflow_id,
            "message": "WeeklyGrowth workflow started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start WeeklyGrowth workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/workflows/meeting-scheduler")
async def start_meeting_scheduler_workflow(
    request: Request, workflow_input: MeetingSchedulerInput
):
    """Start a MeetingScheduler workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    workflow_id = f"meeting-scheduler-{workflow_input.meeting_id}"

    try:
        handle = await temporal_client.start_workflow(
            MeetingSchedulerWorkflow.run,
            args=[workflow_input],
            id=workflow_id,
            task_queue=temporal_client._config.task_queue,
        )
        return {
            "workflow_id": workflow_id,
            "message": "MeetingScheduler workflow started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start MeetingScheduler workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/workflows/{workflow_id}/result")
async def get_workflow_result(request: Request, workflow_id: str):
    """Get the result of a workflow."""
    if not hasattr(request.app.state, "temporal_client"):
        raise HTTPException(status_code=503, detail="Temporal is not configured")

    temporal_client = request.app.state.temporal_client
    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        result = await handle.result()

        # Convert Pydantic models to dict for JSON serialization
        if hasattr(result, "model_dump"):
            result = result.model_dump()

        return {"workflow_id": workflow_id, "result": result, "status": "completed"}
    except Exception as e:
        logger.error(f"Failed to get workflow result: {e}")
        return {"workflow_id": workflow_id, "error": str(e), "status": "error"}

# POST endpoint pattern: Create DB record + Start workflow (works with any database backend)
#
# from pydantic import BaseModel
# from uuid import UUID
#
# class JobRequest(BaseModel):
#     name: str
#     data: dict = {}
#
# class JobResponse(BaseModel):
#     id: UUID
#     name: str
#     status: str
#     created_at: datetime
#
# # PostgreSQL implementation (uncomment if using PostgreSQL)
# async def create_job_record(session: AsyncSession, name: str):
#     job = Job(name=name, status="pending")
#     session.add(job)
#     await session.flush()
#     await session.refresh(job)
#     return job
#
# async def get_job_by_id(session: AsyncSession, job_id: UUID):
#     statement = select(Job).where(Job.id == job_id)
#     result = await session.execute(statement)
#     return result.scalar_one_or_none()
#
# # Database implementation (uncomment if using Database)
# async def create_job_record(cb: DatabaseDB, name: str):
#     job_id = str(uuid.uuid4())
#     job_data = {
#         "id": job_id,
#         "name": name,
#         "status": "pending",
#         "created_at": datetime.utcnow().isoformat()
#     }
#     keyspace = cb.get_keyspace("jobs")
#     await cb.insert_document(keyspace, job_id, job_data)
#     return type('Job', (), job_data)()  # Simple object with attributes
#
# async def get_job_by_id(cb: DatabaseDB, job_id: UUID):
#     keyspace = cb.get_keyspace("jobs")
#     try:
#         doc = await cb.get_document(keyspace, str(job_id))
#         return type('Job', (), doc)()  # Simple object with attributes
#     except DocumentNotFoundException:
#         return None
#
# @router.post("/jobs", response_model=JobResponse, status_code=201)
# async def create_job(request: Request, job_request: JobRequest, session: DBSession):
#     """Create a database record and start a workflow."""
#     # Create database record first
#     job = await create_job_record(session, job_request.name)
#
#     # Start Temporal workflow
#     temporal_client = request.app.state.temporal_client
#     workflow_id = f"job-{job.id}"
#
#     await temporal_client.start_workflow(
#         ProcessJobWorkflow.run,
#         args=[str(job.id), job_request.data],
#         id=workflow_id,
#         task_queue=temporal_client._config.task_queue,
#     )
#
#     return JobResponse(
#         id=job.id,
#         name=job.name,
#         status="pending",
#         created_at=job.created_at
#     )
#
# @router.get("/jobs/{job_id}", response_model=JobResponse)
# async def get_job(job_id: UUID, session: DBSession):
#     """Get job status by ID."""
#     job = await get_job_by_id(session, job_id)
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#
#     return JobResponse(
#         id=job.id,
#         name=job.name,
#         status=job.status,
#         created_at=job.created_at
#     )


# Twilio SMS route examples (uncomment when using Twilio)
#
# To enable Twilio SMS functionality:
# 1. Set USE_TWILIO = True in conf.py
# 2. Set environment variables:
#    - TWILIO_ACCOUNT_SID: Your Twilio Account SID
#    - TWILIO_AUTH_TOKEN: Your Twilio Auth Token
#    - TWILIO_FROM_PHONE_NUMBER: Your Twilio phone number (e.g., '+15551234567')
# 3. Uncomment the routes below
#
# from pydantic import BaseModel
# from twilio.base.exceptions import TwilioRestException
#
# class SMSRequest(BaseModel):
#     to_phone_number: str
#     message: str
#
# @router.post("/sms/send")
# async def send_sms(request: Request, sms_request: SMSRequest):
#     """Send an SMS message via Twilio."""
#     if not conf.USE_TWILIO:
#         raise HTTPException(status_code=503, detail="Twilio SMS is disabled")
#     try:
#         twilio_client = request.app.state.twilio_client
#         result = await twilio_client.send_sms(
#             sms_request.to_phone_number,
#             sms_request.message
#         )
#         return {
#             "success": True,
#             "message_sid": result["sid"],
#             "status": result["status"],
#             "to": result["to"],
#             "message": "SMS sent successfully"
#         }
#     except TwilioRestException as e:
#         logger.error(f"Twilio error: {e}")
#         raise HTTPException(status_code=400, detail=f"Failed to send SMS: {e.msg}")
#     except Exception as e:
#         logger.error(f"Unexpected error sending SMS: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#

# # Example: Send SMS with Temporal workflow for delayed/scheduled messages
# @router.post("/sms/send-delayed")
# async def send_delayed_sms(request: Request, sms_request: SMSRequest, delay_minutes: int = 5):
#     """Send a delayed SMS message using Temporal workflow."""
#     if not conf.USE_TWILIO:
#         raise HTTPException(status_code=503, detail="Twilio SMS is disabled")
#     if not hasattr(request.app.state, 'temporal_client'):
#         raise HTTPException(status_code=503, detail="Temporal is not configured")
#
#     # This would require implementing a Temporal workflow for SMS
#     # Example workflow implementation would go in clients/temporal.py:
#     #
#     # @workflow.defn
#     # class DelayedSMSWorkflow:
#     #     @workflow.run
#     #     async def run(self, phone_number: str, message: str, delay_minutes: int) -> dict:
#     #         await asyncio.sleep(delay_minutes * 60)
#     #         return await workflow.execute_activity(
#     #             send_sms_activity,
#     #             args=[phone_number, message],
#     #             start_to_close_timeout=timedelta(minutes=1)
#     #         )
#
#     temporal_client = request.app.state.temporal_client
#     workflow_id = f"delayed-sms-{uuid.uuid4()}"
#
#     # Start workflow (implementation would depend on your Temporal setup)
#     # handle = await temporal_client.client.start_workflow(
#     #     DelayedSMSWorkflow.run,
#     #     args=[sms_request.to_phone_number, sms_request.message, delay_minutes],
#     #     id=workflow_id,
#     #     task_queue=temporal_client.config.task_queue
#     # )
#
#     return {
#         "workflow_id": workflow_id,
#         "message": f"Delayed SMS scheduled for {delay_minutes} minutes",
#         "to": sms_request.to_phone_number
#     }
#


# ============================================================================
# FlowMentor Database Routes
# ============================================================================


# User Profile Routes
@router.post("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def create_update_profile(request: Request, user_id: str, profile: UserProfile):
    """Create or update a user profile."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        profile_data = profile.model_dump(exclude={"userId"})
        await db_client.upsert_user_profile(user_id, profile_data)

        return UserProfileResponse(
            success=True,
            data=profile.model_dump(),
            message="Profile updated successfully",
        )
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_profile(request: Request, user_id: str):
    """Get a user profile."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        profile = await db_client.get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return UserProfileResponse(
            success=True, data=profile, message="Profile retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Routine Routes
@router.post(
    "/api/users/{user_id}/routines/{routine_id}", response_model=SuccessResponse
)
async def create_update_routine(
    request: Request, user_id: str, routine_id: str, routine: Routine
):
    """Create or update a routine."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        routine_data = routine.model_dump(exclude={"routineId"})
        await db_client.upsert_routine(user_id, routine_id, routine_data)

        return SuccessResponse(
            success=True, message="Routine created/updated successfully"
        )
    except Exception as e:
        logger.error(f"Error creating/updating routine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}/routines", response_model=RoutineListResponse)
async def get_routines(request: Request, user_id: str):
    """Get all routines for a user."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        routines = await db_client.get_user_routines(user_id)

        return RoutineListResponse(
            success=True, data=routines, message=f"Retrieved {len(routines)} routines"
        )
    except Exception as e:
        logger.error(f"Error retrieving routines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Check-in Routes
@router.post("/api/users/{user_id}/checkins", response_model=SuccessResponse)
async def create_checkin(request: Request, user_id: str, date: str, checkin: CheckIn):
    """Create a daily check-in."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        checkin_data = checkin.model_dump()
        await db_client.insert_checkin(user_id, date, checkin_data)

        return SuccessResponse(success=True, message="Check-in recorded successfully")
    except Exception as e:
        logger.error(f"Error creating check-in: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}/checkins/{date}", response_model=CheckInListResponse)
async def get_checkins(request: Request, user_id: str, date: str):
    """Get daily check-ins for a specific date."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        checkins = await db_client.get_daily_checkins(user_id, date)

        return CheckInListResponse(
            success=True, data=checkins, message=f"Retrieved {len(checkins)} check-ins"
        )
    except Exception as e:
        logger.error(f"Error retrieving check-ins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Reflection Routes
@router.post("/api/users/{user_id}/reflections", response_model=SuccessResponse)
async def create_reflection(
    request: Request, user_id: str, date: str, reflection: Reflection
):
    """Create a reflection."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        reflection_data = reflection.model_dump()
        await db_client.insert_reflection(user_id, date, reflection_data)

        return SuccessResponse(success=True, message="Reflection saved successfully")
    except Exception as e:
        logger.error(f"Error creating reflection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}/reflections", response_model=ReflectionListResponse)
async def get_reflections(
    request: Request,
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get reflections for a user, optionally filtered by date range."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        reflections = await db_client.get_reflections(user_id, start_date, end_date)

        return ReflectionListResponse(
            success=True,
            data=reflections,
            message=f"Retrieved {len(reflections)} reflections",
        )
    except Exception as e:
        logger.error(f"Error retrieving reflections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Plan Routes
@router.post("/api/users/{user_id}/plans", response_model=SuccessResponse)
async def create_ai_plan(request: Request, user_id: str, date: str, plan: AIPlan):
    """Create an AI-generated plan."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        plan_data = plan.model_dump()
        await db_client.insert_ai_plan(user_id, date, plan_data)

        return SuccessResponse(success=True, message="AI plan created successfully")
    except Exception as e:
        logger.error(f"Error creating AI plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}/plans/{date}", response_model=AIPlanListResponse)
async def get_ai_plans(request: Request, user_id: str, date: str):
    """Get AI-generated plans for a specific date."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        plans = await db_client.get_ai_plans(user_id, date)

        return AIPlanListResponse(
            success=True, data=plans, message=f"Retrieved {len(plans)} AI plans"
        )
    except Exception as e:
        logger.error(f"Error retrieving AI plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Activity Routes
@router.post("/api/users/{user_id}/activities", response_model=SuccessResponse)
async def create_activity(
    request: Request, user_id: str, date: str, activity_type: str, activity: Activity
):
    """Create an activity (focus block, meeting, or routine instance)."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    if activity_type not in ["focus_block", "meeting", "routine_instance"]:
        raise HTTPException(status_code=400, detail="Invalid activity type")

    try:
        db_client = request.app.state.db_client
        activity_data = activity.model_dump(exclude={"type"})
        await db_client.insert_activity(user_id, date, activity_type, activity_data)

        return SuccessResponse(
            success=True, message=f"{activity_type} created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/users/{user_id}/activities/{date}", response_model=ActivityListResponse
)
async def get_activities(request: Request, user_id: str, date: str):
    """Get all activities for a user on a specific date."""
    if not conf.USE_DATABASE:
        raise HTTPException(status_code=503, detail="Database is not enabled")

    try:
        db_client = request.app.state.db_client
        activities = await db_client.get_activities(user_id, date)

        return ActivityListResponse(
            success=True,
            data=activities,
            message=f"Retrieved {len(activities)} activities",
        )
    except Exception as e:
        logger.error(f"Error retrieving activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
