"""
Workflow Scheduler
Configures scheduled (cron) workflows for FlowMentor.
- MorningCheck: Triggered at 08:30 daily
- DailyReflection: Triggered at 16:30 daily
- WeeklyGrowth: Triggered on Sundays
"""
from datetime import datetime, timedelta
from typing import List
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, ScheduleCalendarSpec
from ..utils.log import get_logger
from .morning_check import MorningCheckWorkflow, MorningCheckInput
from .daily_reflection import DailyReflectionWorkflow, DailyReflectionInput
from .weekly_growth import WeeklyGrowthWorkflow, WeeklyGrowthInput

logger = get_logger(__name__)


async def setup_scheduled_workflows(client: Client, task_queue: str) -> None:
    """
    Set up all scheduled workflows for FlowMentor.
    This should be called once on application startup.
    """
    logger.info("Setting up scheduled workflows...")

    # Note: In production, you would get actual user IDs from the database
    # For now, we'll create schedules for demo user
    demo_user_id = "demo-user"

    try:
        await setup_morning_check_schedule(client, task_queue, demo_user_id)
        await setup_daily_reflection_schedule(client, task_queue, demo_user_id)
        await setup_weekly_growth_schedule(client, task_queue, demo_user_id)
        logger.info("All scheduled workflows set up successfully")
    except Exception as e:
        logger.error(f"Failed to setup scheduled workflows: {e}")
        raise


async def setup_morning_check_schedule(
    client: Client, task_queue: str, user_id: str
) -> None:
    """
    Set up MorningCheck workflow to run at 08:30 daily.
    """
    schedule_id = f"morning-check-{user_id}"

    try:
        # Create or update schedule
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    MorningCheckWorkflow.run,
                    MorningCheckInput(
                        user_id=user_id,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        morning_reflection="Scheduled check-in",
                        energy_level=3,
                        priorities=["Focus on high-priority tasks"],
                    ),
                    id=f"morning-check-{user_id}-scheduled",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    # Run at 08:30 every day
                    calendars=[
                        ScheduleCalendarSpec(
                            hour=[8],
                            minute=[30],
                        )
                    ]
                ),
            ),
        )
        logger.info(f"MorningCheck schedule created: {schedule_id}")
    except Exception as e:
        logger.warning(f"MorningCheck schedule may already exist or failed: {e}")


async def setup_daily_reflection_schedule(
    client: Client, task_queue: str, user_id: str
) -> None:
    """
    Set up DailyReflection workflow to run at 16:30 daily.
    """
    schedule_id = f"daily-reflection-{user_id}"

    try:
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    DailyReflectionWorkflow.run,
                    DailyReflectionInput(
                        user_id=user_id,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        reflection_text="Scheduled reflection",
                        completed_blocks=0,
                        total_blocks=0,
                        overall_productivity=3,
                        wins=[],
                        challenges=[],
                    ),
                    id=f"daily-reflection-{user_id}-scheduled",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    # Run at 16:30 every day
                    calendars=[
                        ScheduleCalendarSpec(
                            hour=[16],
                            minute=[30],
                        )
                    ]
                ),
            ),
        )
        logger.info(f"DailyReflection schedule created: {schedule_id}")
    except Exception as e:
        logger.warning(f"DailyReflection schedule may already exist or failed: {e}")


async def setup_weekly_growth_schedule(
    client: Client, task_queue: str, user_id: str
) -> None:
    """
    Set up WeeklyGrowth workflow to run on Sundays.
    """
    schedule_id = f"weekly-growth-{user_id}"

    try:
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    WeeklyGrowthWorkflow.run,
                    WeeklyGrowthInput(
                        user_id=user_id,
                        week_start=(
                            datetime.now() - timedelta(days=7)
                        ).strftime("%Y-%m-%d"),
                        week_end=datetime.now().strftime("%Y-%m-%d"),
                    ),
                    id=f"weekly-growth-{user_id}-scheduled",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    # Run on Sundays at 10:00
                    calendars=[
                        ScheduleCalendarSpec(
                            day_of_week=[0],  # 0 = Sunday
                            hour=[10],
                            minute=[0],
                        )
                    ]
                ),
            ),
        )
        logger.info(f"WeeklyGrowth schedule created: {schedule_id}")
    except Exception as e:
        logger.warning(f"WeeklyGrowth schedule may already exist or failed: {e}")


async def list_schedules(client: Client) -> List[str]:
    """
    List all active schedules.
    """
    try:
        schedules = []
        async for schedule in client.list_schedules():
            schedules.append(schedule.id)
        return schedules
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        return []


async def delete_schedule(client: Client, schedule_id: str) -> bool:
    """
    Delete a schedule by ID.
    """
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        logger.info(f"Schedule deleted: {schedule_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {e}")
        return False
