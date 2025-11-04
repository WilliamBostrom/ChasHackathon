"""
WeeklyGrowth Workflow
Triggered on Sundays.
- Aggregates week data
- AI generates 3 micro-goals for next week
- Saves selected goal and integrates into next week's planning
"""
from datetime import timedelta
from typing import List, Dict, Any, Optional

from pydantic import BaseModel
from temporalio import activity, workflow
from ..utils.log import get_logger

logger = get_logger(__name__)

#### Constants ####

ACTIVITY_TIMEOUT_SECONDS = 60

#### Models ####


class WeeklyStats(BaseModel):
    """Aggregated weekly statistics."""

    total_blocks_completed: int
    total_blocks_planned: int
    average_productivity: float
    total_focus_hours: float
    top_achievements: List[str]
    recurring_challenges: List[str]
    completion_rate: float


class MicroGoal(BaseModel):
    """A micro-goal for the next week."""

    goal_id: str
    title: str
    description: str
    rationale: str
    suggested_actions: List[str]
    difficulty: int  # 1-5


class WeeklyGrowthInput(BaseModel):
    """Input for WeeklyGrowth workflow."""

    user_id: str
    week_start: str  # ISO date format
    week_end: str  # ISO date format


class WeeklyGrowthResponse(BaseModel):
    """Response from WeeklyGrowth workflow."""

    success: bool
    weekly_stats: WeeklyStats
    micro_goals: List[MicroGoal]
    selected_goal: Optional[MicroGoal]
    message: str


#### Activities ####


@activity.defn
async def aggregate_week_data_activity(
    user_id: str, week_start: str, week_end: str
) -> WeeklyStats:
    """
    Aggregate data from the past week from Couchbase.
    """
    activity.logger.info(
        f"Aggregating week data for user {user_id} from {week_start} to {week_end}"
    )

    # TODO: Query Couchbase for all reflections, blocks, and feedback from the week
    # For now, return mock stats
    try:
        # from ..clients.couchbase import CouchbaseClient
        # reflections = await couchbase_client.get_reflections(user_id, week_start, week_end)
        # activities = await couchbase_client.get_activities_range(user_id, week_start, week_end)

        stats = WeeklyStats(
            total_blocks_completed=24,
            total_blocks_planned=30,
            average_productivity=3.8,
            total_focus_hours=40.0,
            top_achievements=[
                "Completed major project milestone",
                "Maintained consistent morning routine",
                "Improved focus duration by 15%",
            ],
            recurring_challenges=[
                "Afternoon energy dips",
                "Meeting interruptions",
                "Email distractions",
            ],
            completion_rate=80.0,
        )

        activity.logger.info(f"Aggregated stats: {stats.completion_rate}% completion")
        return stats

    except Exception as e:
        activity.logger.error(f"Failed to aggregate week data: {e}")
        raise


@activity.defn
async def generate_micro_goals_activity(
    user_id: str, stats: WeeklyStats
) -> List[MicroGoal]:
    """
    Call AI to generate 3 micro-goals for next week based on weekly stats.
    """
    activity.logger.info(f"Generating micro-goals for user {user_id}")

    # TODO: Integrate with actual AI service
    # For now, return mock goals
    goals = [
        MicroGoal(
            goal_id="goal-1",
            title="Increase Focus Block Completion",
            description="Aim to complete 90% of planned focus blocks",
            rationale="Your current completion rate is 80%, which is good but can be improved. Completing more blocks will boost productivity.",
            suggested_actions=[
                "Schedule blocks earlier in the day",
                "Add buffer time between blocks",
                "Review and adjust block durations",
            ],
            difficulty=2,
        ),
        MicroGoal(
            goal_id="goal-2",
            title="Combat Afternoon Energy Dips",
            description="Implement strategies to maintain energy in afternoons",
            rationale="You identified afternoon energy dips as a recurring challenge. Addressing this will improve overall productivity.",
            suggested_actions=[
                "Take a 10-minute walk after lunch",
                "Schedule lighter tasks for early afternoon",
                "Consider a brief power nap or meditation",
            ],
            difficulty=3,
        ),
        MicroGoal(
            goal_id="goal-3",
            title="Reduce Meeting Interruptions",
            description="Batch meetings and protect focus blocks",
            rationale="Meeting interruptions were a recurring challenge. Batching meetings can create longer uninterrupted work periods.",
            suggested_actions=[
                "Designate specific meeting hours",
                "Communicate focus block schedule to team",
                "Use 'Do Not Disturb' mode during blocks",
            ],
            difficulty=4,
        ),
    ]

    return goals


@activity.defn
async def save_weekly_summary_activity(
    user_id: str,
    week_start: str,
    stats: WeeklyStats,
    goals: List[MicroGoal],
    selected_goal: Optional[MicroGoal],
) -> bool:
    """
    Save weekly summary and goals to Couchbase.
    """
    activity.logger.info(f"Saving weekly summary for user {user_id}")

    # TODO: Save to Couchbase
    try:
        # from ..clients.couchbase import CouchbaseClient
        # summary_data = {
        #     "type": "weekly_summary",
        #     "user_id": user_id,
        #     "week_start": week_start,
        #     "stats": stats.model_dump(),
        #     "micro_goals": [goal.model_dump() for goal in goals],
        #     "selected_goal": selected_goal.model_dump() if selected_goal else None
        # }
        # await couchbase_client.upsert_document(
        #     f"weekly_summary::{user_id}::{week_start}",
        #     summary_data
        # )
        activity.logger.info("Weekly summary saved successfully")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to save weekly summary: {e}")
        return False


#### Workflows ####


@workflow.defn
class WeeklyGrowthWorkflow:
    """
    WeeklyGrowth workflow orchestrates the weekly review process.
    Triggered on Sundays to review the past week and plan for next week.
    """

    def __init__(self):
        self._goal_selected = False
        self._selected_goal: Optional[MicroGoal] = None

    @workflow.signal
    async def select_goal(self, goal_id: str, goals: List[MicroGoal]):
        """
        Signal to receive user's selected goal.
        """
        workflow.logger.info(f"Received goal selection: {goal_id}")
        for goal in goals:
            if goal.goal_id == goal_id:
                self._selected_goal = goal
                self._goal_selected = True
                break

    @workflow.run
    async def run(self, input: WeeklyGrowthInput) -> WeeklyGrowthResponse:
        """
        Execute the weekly growth workflow:
        1. Aggregate data from the past week
        2. Generate 3 micro-goals using AI
        3. Wait for user to select a goal (with timeout)
        4. Save weekly summary and selected goal
        5. Return results
        """
        workflow.logger.info(
            f"Starting WeeklyGrowth workflow for user {input.user_id}, week {input.week_start} to {input.week_end}"
        )

        # Step 1: Aggregate week data
        stats = await workflow.execute_activity(
            aggregate_week_data_activity,
            args=[input.user_id, input.week_start, input.week_end],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        workflow.logger.info(
            f"Aggregated stats: {stats.total_blocks_completed}/{stats.total_blocks_planned} blocks"
        )

        # Step 2: Generate micro-goals
        micro_goals = await workflow.execute_activity(
            generate_micro_goals_activity,
            args=[input.user_id, stats],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        workflow.logger.info(f"Generated {len(micro_goals)} micro-goals")

        # Step 3: Wait for user to select a goal (24 hour timeout)
        workflow.logger.info("Waiting for user to select a goal")
        try:
            await workflow.wait_condition(
                lambda: self._goal_selected, timeout=timedelta(hours=24)
            )
            workflow.logger.info(
                f"User selected goal: {self._selected_goal.title if self._selected_goal else 'None'}"
            )
        except Exception:
            workflow.logger.info(
                "No goal selected within timeout, using first goal as default"
            )
            self._selected_goal = micro_goals[0] if micro_goals else None

        # Step 4: Save weekly summary
        saved = await workflow.execute_activity(
            save_weekly_summary_activity,
            args=[
                input.user_id,
                input.week_start,
                stats,
                micro_goals,
                self._selected_goal,
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info(f"Weekly summary save result: {saved}")

        return WeeklyGrowthResponse(
            success=saved,
            weekly_stats=stats,
            micro_goals=micro_goals,
            selected_goal=self._selected_goal,
            message="Weekly growth review completed successfully",
        )
