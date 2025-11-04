"""
Temporal workflows registry.

All workflows are automatically registered here.
"""

# Import workflows here
# They will be auto-added by the add-temporal-workflow tool

# Registry of all workflows

from .morning_check import MorningCheckWorkflow
from .focus_loop import FocusLoopWorkflow
from .daily_reflection import DailyReflectionWorkflow
from .weekly_growth import WeeklyGrowthWorkflow
from .meeting_scheduler import MeetingSchedulerWorkflow





WORKFLOWS = [
    MorningCheckWorkflow,
    FocusLoopWorkflow,
    DailyReflectionWorkflow,
    WeeklyGrowthWorkflow,
    MeetingSchedulerWorkflow,
]
