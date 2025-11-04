"""
FocusLoop Workflow
Manages timers for each focus block.
- Sends notifications when a block starts or ends
- Updates Couchbase with feedback
"""
from datetime import timedelta
from typing import Optional

from pydantic import BaseModel
from temporalio import activity, workflow
from ..utils.log import get_logger

logger = get_logger(__name__)

#### Constants ####

ACTIVITY_TIMEOUT_SECONDS = 30

#### Models ####


class FocusBlockInfo(BaseModel):
    """Information about a focus block."""

    block_id: str
    user_id: str
    date: str
    title: str
    description: str
    duration_minutes: int


class FocusLoopInput(BaseModel):
    """Input for FocusLoop workflow."""

    block: FocusBlockInfo


class BlockFeedback(BaseModel):
    """Feedback from user after completing a focus block."""

    completed: bool
    actual_duration_minutes: int
    productivity_rating: int  # 1-5
    notes: Optional[str] = None


class FocusLoopResponse(BaseModel):
    """Response from FocusLoop workflow."""

    success: bool
    block_id: str
    message: str


#### Activities ####


@activity.defn
async def send_block_start_notification_activity(block: FocusBlockInfo) -> bool:
    """
    Send notification when a focus block starts.
    This could be push notification, SMS via Twilio, or browser notification.
    """
    activity.logger.info(
        f"Sending start notification for block {block.block_id}: {block.title}"
    )

    # TODO: Integrate with notification service (Twilio, FCM, browser notifications)
    # For now, simulate notification
    try:
        # Example: await twilio_client.send_sms(user_phone, f"Focus block started: {block.title}")
        activity.logger.info(f"Notification sent for block start: {block.title}")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to send notification: {e}")
        return False


@activity.defn
async def send_block_end_notification_activity(block: FocusBlockInfo) -> bool:
    """
    Send notification when a focus block ends.
    """
    activity.logger.info(
        f"Sending end notification for block {block.block_id}: {block.title}"
    )

    # TODO: Integrate with notification service
    try:
        # Example: await twilio_client.send_sms(user_phone, f"Focus block completed: {block.title}")
        activity.logger.info(f"Notification sent for block end: {block.title}")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to send notification: {e}")
        return False


@activity.defn
async def update_block_feedback_activity(
    block_id: str, user_id: str, date: str, feedback: BlockFeedback
) -> bool:
    """
    Update Couchbase with feedback about the focus block.
    """
    activity.logger.info(f"Updating feedback for block {block_id}")

    # TODO: Get Couchbase client and update block feedback
    try:
        # from ..clients.couchbase import CouchbaseClient
        # await couchbase_client.upsert_document(
        #     f"feedback::{user_id}::{date}::{block_id}",
        #     {
        #         "type": "block_feedback",
        #         "block_id": block_id,
        #         "user_id": user_id,
        #         "date": date,
        #         **feedback.model_dump()
        #     }
        # )
        activity.logger.info("Block feedback updated successfully")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to update feedback: {e}")
        return False


#### Workflows ####


@workflow.defn
class FocusLoopWorkflow:
    """
    FocusLoop workflow manages the lifecycle of a focus block.
    It handles timing, notifications, and feedback collection.
    """

    def __init__(self):
        self._feedback_received = False
        self._feedback: Optional[BlockFeedback] = None

    @workflow.signal
    async def submit_feedback(self, feedback: BlockFeedback):
        """
        Signal to receive feedback from the user.
        This can be called externally to submit feedback.
        """
        workflow.logger.info(f"Received feedback signal: {feedback}")
        self._feedback_received = True
        self._feedback = feedback

    @workflow.run
    async def run(self, input: FocusLoopInput) -> FocusLoopResponse:
        """
        Execute the focus loop workflow:
        1. Send start notification
        2. Wait for the duration of the focus block
        3. Send end notification
        4. Wait for user feedback (with timeout)
        5. Store feedback in Couchbase
        """
        block = input.block
        workflow.logger.info(
            f"Starting FocusLoop workflow for block {block.block_id}: {block.title}"
        )

        # Step 1: Send start notification
        await workflow.execute_activity(
            send_block_start_notification_activity,
            args=[block],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        workflow.logger.info(
            f"Start notification sent, waiting {block.duration_minutes} minutes"
        )

        # Step 2: Wait for the duration of the focus block
        await workflow.sleep(timedelta(minutes=block.duration_minutes))

        workflow.logger.info(
            f"Focus block duration elapsed for {block.block_id}, sending end notification"
        )

        # Step 3: Send end notification
        await workflow.execute_activity(
            send_block_end_notification_activity,
            args=[block],
            start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        # Step 4: Wait for user feedback (with 10 minute timeout)
        workflow.logger.info("Waiting for user feedback")
        try:
            await workflow.wait_condition(
                lambda: self._feedback_received, timeout=timedelta(minutes=10)
            )
            workflow.logger.info("Feedback received from user")
        except Exception:
            workflow.logger.info(
                "No feedback received within timeout, using default values"
            )
            # If no feedback is received, assume minimal completion
            self._feedback = BlockFeedback(
                completed=True,
                actual_duration_minutes=block.duration_minutes,
                productivity_rating=3,
                notes="No feedback provided",
            )

        # Step 5: Store feedback in Couchbase
        if self._feedback:
            await workflow.execute_activity(
                update_block_feedback_activity,
                args=[block.block_id, block.user_id, block.date, self._feedback],
                start_to_close_timeout=timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS),
                retry_policy=workflow.RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                ),
            )

        workflow.logger.info(f"FocusLoop workflow completed for {block.block_id}")

        return FocusLoopResponse(
            success=True,
            block_id=block.block_id,
            message=f"Focus block '{block.title}' completed successfully",
        )
