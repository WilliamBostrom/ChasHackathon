"""
MorningCheck Workflow
Triggered at 08:30 daily when user submits morning check.
- Calls AI to generate focus plan + blocks + routines
- Stores plan in Couchbase
"""
from datetime import timedelta
from typing import List, Dict, Any

from pydantic import BaseModel
from temporalio import activity, workflow
from ..utils.log import get_logger

logger = get_logger(__name__)

#### Constants ####

ACTIVITY_TIMEOUT_SECONDS = 60

#### Models ####


class MorningCheckInput(BaseModel):
    """Input for MorningCheck workflow."""

    user_id: str
    date: str
    morning_reflection: str
    energy_level: int  # 1-5
    priorities: List[str]


class FocusBlock(BaseModel):
    """Individual focus block."""

    block_id: str
    title: str
    description: str
    start_time: str
    end_time: str
    duration_minutes: int


class DailyPlan(BaseModel):
    """AI-generated daily plan."""

    focus_blocks: List[FocusBlock]
    routines: List[Dict[str, Any]]
    micro_tips: List[str]


class MorningCheckResponse(BaseModel):
    """Response from MorningCheck workflow."""

    success: bool
    plan: DailyPlan
    message: str


#### Activities ####


@activity.defn
async def generate_ai_plan_activity(input: MorningCheckInput) -> DailyPlan:
    """
    Call AI to generate focus plan, blocks, and routines.
    """
    activity.logger.info(
        f"Generating AI plan for user {input.user_id} on {input.date}"
    )

    # TODO: Integrate with actual AI service (OpenAI, Anthropic, etc.)
    # For now, return a mock plan
    plan = DailyPlan(
        focus_blocks=[
            FocusBlock(
                block_id="block-1",
                title="Deep Work Session",
                description="Focus on high-priority task from morning priorities",
                start_time="09:00",
                end_time="11:00",
                duration_minutes=120,
            ),
            FocusBlock(
                block_id="block-2",
                title="Project Work",
                description="Continue with ongoing projects",
                start_time="13:00",
                end_time="15:00",
                duration_minutes=120,
            ),
        ],
        routines=[
            {"name": "Morning Stretch", "time": "08:45", "duration": 15},
            {"name": "Afternoon Break", "time": "15:00", "duration": 10},
        ],
        micro_tips=[
            "Start with the hardest task when your energy is highest",
            "Take regular breaks to maintain focus",
            "Stay hydrated throughout the day",
        ],
    )

    return plan


@activity.defn
async def store_plan_in_couchbase_activity(
    user_id: str, date: str, plan: DailyPlan
) -> bool:
    """
    Store the generated plan in Couchbase.
    """
    activity.logger.info(f"Storing plan for user {user_id} on {date} in Couchbase")

    # TODO: Get Couchbase client and store plan
    # This would require passing the client or connection info
    # For now, simulate storage
    try:
        # from ..clients.couchbase import CouchbaseClient
        # await couchbase_client.insert_ai_plan(user_id, date, plan.model_dump())
        activity.logger.info("Plan stored successfully")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to store plan: {e}")
        return False


#### Workflows ####


@workflow.defn
class MorningCheckWorkflow:
    """
    MorningCheck workflow orchestrates the morning planning process.
    Triggered at 08:30 when user submits morning check.
    """

    @workflow.run
    async def run(self, input: MorningCheckInput) -> MorningCheckResponse:
        """
        Execute the morning check workflow:
        1. Generate AI plan based on user input
        2. Store plan in Couchbase
        3. Return plan to user
        """
        workflow.logger.info(
            f"Starting MorningCheck workflow for user {input.user_id} on {input.date}"
        )

        # Step 1: Generate AI plan
        plan = await workflow.execute_activity(
            generate_ai_plan_activity,
            args=[input],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        workflow.logger.info(f"Generated plan with {len(plan.focus_blocks)} blocks")

        # Step 2: Store plan in Couchbase
        stored = await workflow.execute_activity(
            store_plan_in_couchbase_activity,
            args=[input.user_id, input.date, plan],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info(f"Plan storage result: {stored}")

        return MorningCheckResponse(
            success=stored,
            plan=plan,
            message="Morning check completed and plan generated successfully",
        )
