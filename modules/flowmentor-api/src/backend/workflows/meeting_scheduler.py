"""
MeetingScheduler Workflow
Triggered on demand between users.
- Takes time windows from two users
- AI finds the best available slot
- Updates both users' schedules
"""
from datetime import timedelta
from typing import List, Optional

from pydantic import BaseModel
from temporalio import activity, workflow
from ..utils.log import get_logger

logger = get_logger(__name__)

#### Constants ####

ACTIVITY_TIMEOUT_SECONDS = 60

#### Models ####


class TimeWindow(BaseModel):
    """Available time window for scheduling."""

    start_time: str  # ISO format datetime
    end_time: str  # ISO format datetime
    date: str  # ISO date format


class MeetingSchedulerInput(BaseModel):
    """Input for MeetingScheduler workflow."""

    meeting_id: str
    user1_id: str
    user2_id: str
    user1_time_windows: List[TimeWindow]
    user2_time_windows: List[TimeWindow]
    meeting_duration_minutes: int
    meeting_title: str
    meeting_description: Optional[str] = None


class ScheduledMeeting(BaseModel):
    """Details of the scheduled meeting."""

    meeting_id: str
    scheduled_time: TimeWindow
    user1_id: str
    user2_id: str
    title: str
    description: Optional[str]
    confidence_score: float  # 0-1, how optimal the slot is


class MeetingSchedulerResponse(BaseModel):
    """Response from MeetingScheduler workflow."""

    success: bool
    scheduled_meeting: Optional[ScheduledMeeting]
    message: str


#### Activities ####


@activity.defn
async def find_optimal_slot_activity(
    user1_windows: List[TimeWindow],
    user2_windows: List[TimeWindow],
    duration_minutes: int,
) -> Optional[TimeWindow]:
    """
    Use AI to find the best available slot for both users.
    """
    activity.logger.info(
        f"Finding optimal slot for {duration_minutes} minute meeting"
    )

    # TODO: Integrate with actual AI service to find optimal slot
    # AI can consider factors like:
    # - Time of day preferences
    # - Energy levels
    # - Existing focus blocks
    # - Travel time between meetings
    # For now, return first overlapping window

    try:
        # Find overlapping time windows
        for window1 in user1_windows:
            for window2 in user2_windows:
                if window1.date == window2.date:
                    # Simple overlap check (in production, use proper datetime comparison)
                    if (
                        window1.start_time <= window2.end_time
                        and window2.start_time <= window1.end_time
                    ):
                        # Found overlap, return as optimal slot
                        optimal_slot = TimeWindow(
                            start_time=max(window1.start_time, window2.start_time),
                            end_time=min(window1.end_time, window2.end_time),
                            date=window1.date,
                        )
                        activity.logger.info(
                            f"Found optimal slot: {optimal_slot.date} at {optimal_slot.start_time}"
                        )
                        return optimal_slot

        activity.logger.warning("No overlapping time windows found")
        return None

    except Exception as e:
        activity.logger.error(f"Failed to find optimal slot: {e}")
        return None


@activity.defn
async def update_user_schedule_activity(
    user_id: str, meeting: ScheduledMeeting
) -> bool:
    """
    Update a user's schedule in Couchbase with the new meeting.
    """
    activity.logger.info(
        f"Updating schedule for user {user_id} with meeting {meeting.meeting_id}"
    )

    # TODO: Get Couchbase client and update schedule
    try:
        # from ..clients.couchbase import CouchbaseClient
        # meeting_data = {
        #     "type": "meeting",
        #     "meeting_id": meeting.meeting_id,
        #     "user_id": user_id,
        #     "date": meeting.scheduled_time.date,
        #     "start_time": meeting.scheduled_time.start_time,
        #     "end_time": meeting.scheduled_time.end_time,
        #     "title": meeting.title,
        #     "description": meeting.description,
        #     "other_user_id": meeting.user2_id if user_id == meeting.user1_id else meeting.user1_id
        # }
        # await couchbase_client.insert_activity(
        #     user_id,
        #     meeting.scheduled_time.date,
        #     "meeting",
        #     meeting_data
        # )
        activity.logger.info(f"Schedule updated for user {user_id}")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to update schedule for user {user_id}: {e}")
        return False


@activity.defn
async def send_meeting_notification_activity(
    user_id: str, meeting: ScheduledMeeting
) -> bool:
    """
    Send notification to user about the scheduled meeting.
    """
    activity.logger.info(
        f"Sending meeting notification to user {user_id} for meeting {meeting.meeting_id}"
    )

    # TODO: Integrate with notification service
    try:
        # Example: Send email, SMS, or push notification
        # await notification_service.send(
        #     user_id,
        #     title=f"Meeting Scheduled: {meeting.title}",
        #     body=f"Your meeting is scheduled for {meeting.scheduled_time.date} at {meeting.scheduled_time.start_time}",
        #     data={"meeting_id": meeting.meeting_id}
        # )
        activity.logger.info(f"Notification sent to user {user_id}")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to send notification to user {user_id}: {e}")
        return False


#### Workflows ####


@workflow.defn
class MeetingSchedulerWorkflow:
    """
    MeetingScheduler workflow orchestrates meeting scheduling between two users.
    Triggered on demand when users want to schedule a meeting.
    """

    @workflow.run
    async def run(self, input: MeetingSchedulerInput) -> MeetingSchedulerResponse:
        """
        Execute the meeting scheduler workflow:
        1. Use AI to find optimal slot from available windows
        2. Update both users' schedules in Couchbase
        3. Send notifications to both users
        4. Return scheduled meeting details
        """
        workflow.logger.info(
            f"Starting MeetingScheduler workflow for meeting {input.meeting_id} between {input.user1_id} and {input.user2_id}"
        )

        # Step 1: Find optimal slot using AI
        optimal_slot = await workflow.execute_activity(
            find_optimal_slot_activity,
            args=[
                input.user1_time_windows,
                input.user2_time_windows,
                input.meeting_duration_minutes,
            ],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        if not optimal_slot:
            workflow.logger.warning("No optimal slot found")
            return MeetingSchedulerResponse(
                success=False,
                scheduled_meeting=None,
                message="No available time slots found for both users",
            )

        workflow.logger.info(
            f"Found optimal slot: {optimal_slot.date} at {optimal_slot.start_time}"
        )

        # Create scheduled meeting object
        scheduled_meeting = ScheduledMeeting(
            meeting_id=input.meeting_id,
            scheduled_time=optimal_slot,
            user1_id=input.user1_id,
            user2_id=input.user2_id,
            title=input.meeting_title,
            description=input.meeting_description,
            confidence_score=0.95,  # In production, AI would provide this
        )

        # Step 2: Update both users' schedules
        user1_updated = await workflow.execute_activity(
            update_user_schedule_activity,
            args=[input.user1_id, scheduled_meeting],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        user2_updated = await workflow.execute_activity(
            update_user_schedule_activity,
            args=[input.user2_id, scheduled_meeting],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        if not (user1_updated and user2_updated):
            workflow.logger.error("Failed to update one or both user schedules")
            return MeetingSchedulerResponse(
                success=False,
                scheduled_meeting=scheduled_meeting,
                message="Failed to update user schedules",
            )

        workflow.logger.info("Both user schedules updated successfully")

        # Step 3: Send notifications to both users
        await workflow.execute_activity(
            send_meeting_notification_activity,
            args=[input.user1_id, scheduled_meeting],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )

        await workflow.execute_activity(
            send_meeting_notification_activity,
            args=[input.user2_id, scheduled_meeting],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info("Notifications sent to both users")

        return MeetingSchedulerResponse(
            success=True,
            scheduled_meeting=scheduled_meeting,
            message=f"Meeting '{input.meeting_title}' scheduled successfully for {optimal_slot.date} at {optimal_slot.start_time}",
        )
