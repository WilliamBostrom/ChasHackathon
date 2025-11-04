"""
DailyReflection Workflow
Triggered at 16:30 daily.
- Prompts user for daily reflection
- Calls AI for summary and micro-tips
- Saves reflection data
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


class DailyReflectionInput(BaseModel):
    """Input for DailyReflection workflow."""

    user_id: str
    date: str
    reflection_text: str
    completed_blocks: int
    total_blocks: int
    overall_productivity: int  # 1-5
    wins: List[str]
    challenges: List[str]


class AISummary(BaseModel):
    """AI-generated summary and insights."""

    summary: str
    key_insights: List[str]
    micro_tips: List[str]
    suggested_improvements: List[str]


class DailyReflectionResponse(BaseModel):
    """Response from DailyReflection workflow."""

    success: bool
    ai_summary: AISummary
    message: str


#### Activities ####


@activity.defn
async def generate_ai_summary_activity(input: DailyReflectionInput) -> AISummary:
    """
    Call AI to generate summary and micro-tips from daily reflection.
    """
    activity.logger.info(
        f"Generating AI summary for user {input.user_id} on {input.date}"
    )

    # TODO: Integrate with actual AI service (OpenAI, Anthropic, etc.)
    # For now, return a mock summary
    completion_rate = (
        input.completed_blocks / input.total_blocks * 100
        if input.total_blocks > 0
        else 0
    )

    summary = AISummary(
        summary=f"You completed {input.completed_blocks} out of {input.total_blocks} focus blocks ({completion_rate:.0f}% completion rate) with an overall productivity rating of {input.overall_productivity}/5. {input.reflection_text[:100]}...",
        key_insights=[
            f"Completion rate: {completion_rate:.0f}%",
            f"Productivity level: {input.overall_productivity}/5",
            f"Number of wins today: {len(input.wins)}",
            f"Challenges faced: {len(input.challenges)}",
        ],
        micro_tips=[
            "Consider scheduling your most challenging tasks earlier in the day",
            "Break down complex tasks into smaller, manageable focus blocks",
            "Review your wins to build momentum for tomorrow",
        ],
        suggested_improvements=[
            "Increase focus block duration for deeper work sessions",
            "Add buffer time between blocks for better transitions",
            "Address recurring challenges with preventive planning",
        ],
    )

    return summary


@activity.defn
async def save_reflection_activity(
    user_id: str, date: str, reflection: DailyReflectionInput, summary: AISummary
) -> bool:
    """
    Save reflection and AI summary to Couchbase.
    """
    activity.logger.info(f"Saving reflection for user {user_id} on {date}")

    # TODO: Get Couchbase client and save reflection
    try:
        # from ..clients.couchbase import CouchbaseClient
        # reflection_data = {
        #     **reflection.model_dump(),
        #     "ai_summary": summary.model_dump()
        # }
        # await couchbase_client.insert_reflection(user_id, date, reflection_data)
        activity.logger.info("Reflection saved successfully")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to save reflection: {e}")
        return False


@activity.defn
async def send_reflection_notification_activity(
    user_id: str, summary: AISummary
) -> bool:
    """
    Send notification with daily summary and tips.
    """
    activity.logger.info(f"Sending reflection notification to user {user_id}")

    # TODO: Integrate with notification service
    try:
        # Example: Send email or push notification with summary
        # await notification_service.send(
        #     user_id,
        #     title="Your Daily Reflection",
        #     body=summary.summary,
        #     data={"tips": summary.micro_tips}
        # )
        activity.logger.info("Reflection notification sent successfully")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to send notification: {e}")
        return False


#### Workflows ####


@workflow.defn
class DailyReflectionWorkflow:
    """
    DailyReflection workflow orchestrates the evening reflection process.
    Triggered at 16:30 when user submits daily reflection.
    """

    @workflow.run
    async def run(self, input: DailyReflectionInput) -> DailyReflectionResponse:
        """
        Execute the daily reflection workflow:
        1. Generate AI summary and tips from reflection
        2. Save reflection data to Couchbase
        3. Send notification with summary
        4. Return summary to user
        """
        workflow.logger.info(
            f"Starting DailyReflection workflow for user {input.user_id} on {input.date}"
        )

        # Step 1: Generate AI summary and tips
        ai_summary = await workflow.execute_activity(
            generate_ai_summary_activity,
            args=[input],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        workflow.logger.info(
            f"Generated AI summary with {len(ai_summary.micro_tips)} tips"
        )

        # Step 2: Save reflection data
        saved = await workflow.execute_activity(
            save_reflection_activity,
            args=[input.user_id, input.date, input, ai_summary],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info(f"Reflection save result: {saved}")

        # Step 3: Send notification with summary
        await workflow.execute_activity(
            send_reflection_notification_activity,
            args=[input.user_id, ai_summary],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info("Notification sent")

        return DailyReflectionResponse(
            success=saved,
            ai_summary=ai_summary,
            message="Daily reflection completed and insights generated successfully",
        )
