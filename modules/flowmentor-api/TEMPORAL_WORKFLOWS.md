# FlowMentor Temporal Workflows Integration

This document describes the Temporal workflow integration for FlowMentor application.

## Overview

FlowMentor uses Temporal to orchestrate the following workflows:

1. **MorningCheck** - Triggered at 08:30 daily
2. **FocusLoop** - Manages focus block timers and notifications
3. **DailyReflection** - Triggered at 16:30 daily
4. **WeeklyGrowth** - Triggered on Sundays
5. **MeetingScheduler** - On-demand for scheduling meetings between users

## Workflows

### 1. MorningCheck Workflow

**Purpose**: Generate daily plan, focus blocks, and routines based on morning check-in

**Trigger**: Scheduled at 08:30 daily OR manually via API

**Input**:

```python
{
  "user_id": "string",
  "date": "YYYY-MM-DD",
  "morning_reflection": "string",
  "energy_level": 1-5,
  "priorities": ["string"]
}
```

**Process**:

1. Calls AI to generate focus plan + blocks + routines
2. Stores plan in Couchbase
3. Returns plan to user

**API Endpoint**: `POST /api/workflows/morning-check`

### 2. FocusLoop Workflow

**Purpose**: Manage focus block lifecycle with timers and notifications

**Trigger**: Started when a focus block begins

**Input**:

```python
{
  "block": {
    "block_id": "string",
    "user_id": "string",
    "date": "YYYY-MM-DD",
    "title": "string",
    "description": "string",
    "duration_minutes": integer
  }
}
```

**Process**:

1. Sends start notification
2. Waits for block duration
3. Sends end notification
4. Waits for user feedback (10 min timeout)
5. Updates Couchbase with feedback

**API Endpoint**: `POST /api/workflows/focus-loop`

**Signals**:

- `submit_feedback`: Receive user feedback about completed block

### 3. DailyReflection Workflow

**Purpose**: End-of-day reflection with AI insights and tips

**Trigger**: Scheduled at 16:30 daily OR manually via API

**Input**:

```python
{
  "user_id": "string",
  "date": "YYYY-MM-DD",
  "reflection_text": "string",
  "completed_blocks": integer,
  "total_blocks": integer,
  "overall_productivity": 1-5,
  "wins": ["string"],
  "challenges": ["string"]
}
```

**Process**:

1. Generates AI summary and micro-tips
2. Saves reflection data to Couchbase
3. Sends notification with summary
4. Returns summary to user

**API Endpoint**: `POST /api/workflows/daily-reflection`

### 4. WeeklyGrowth Workflow

**Purpose**: Weekly review and goal setting

**Trigger**: Scheduled on Sundays at 10:00 OR manually via API

**Input**:

```python
{
  "user_id": "string",
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD"
}
```

**Process**:

1. Aggregates data from past week
2. AI generates 3 micro-goals
3. Waits for user to select a goal (24h timeout)
4. Saves weekly summary and selected goal
5. Returns results

**API Endpoint**: `POST /api/workflows/weekly-growth`

**Signals**:

- `select_goal`: Receive user's selected micro-goal

### 5. MeetingScheduler Workflow

**Purpose**: Find optimal meeting slot between two users

**Trigger**: On-demand via API

**Input**:

```python
{
  "meeting_id": "string",
  "user1_id": "string",
  "user2_id": "string",
  "user1_time_windows": [TimeWindow],
  "user2_time_windows": [TimeWindow],
  "meeting_duration_minutes": integer,
  "meeting_title": "string",
  "meeting_description": "string"
}
```

**Process**:

1. AI finds best available slot
2. Updates both users' schedules
3. Sends notifications to both users
4. Returns scheduled meeting details

**API Endpoint**: `POST /api/workflows/meeting-scheduler`

## Getting Started

### 1. Start Temporal Services

```bash
# Start all services including Temporal
polytope run default
```

This will start:

- Temporal Server (port 7233)
- Temporal UI (port 8080)
- Postgres (for Temporal storage)
- Couchbase
- FlowMentor API
- FlowMentor Frontend

### 2. Access Temporal UI

Visit http://localhost:8080 to see the Temporal Web UI where you can:

- View running workflows
- See workflow history
- Query workflow state
- View scheduled workflows

### 3. Test Workflows

#### Start a Morning Check Workflow

```bash
curl -X POST http://localhost:3030/api/workflows/morning-check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "date": "2025-01-04",
    "morning_reflection": "Feeling energized today",
    "energy_level": 4,
    "priorities": ["Complete project proposal", "Team meeting prep"]
  }'
```

#### Start a Focus Loop Workflow

```bash
curl -X POST http://localhost:3030/api/workflows/focus-loop \
  -H "Content-Type: application/json" \
  -d '{
    "block": {
      "block_id": "block-123",
      "user_id": "demo-user",
      "date": "2025-01-04",
      "title": "Deep Work Session",
      "description": "Focus on project proposal",
      "duration_minutes": 25
    }
  }'
```

#### Get Workflow Result

```bash
curl http://localhost:3030/api/workflows/{workflow_id}/result
```

## Scheduled Workflows

Scheduled workflows are automatically set up on application startup for the demo user. In production, you would create schedules for each registered user.

### View Active Schedules

Check the Temporal UI under "Schedules" to see:

- `morning-check-demo-user`: Runs daily at 08:30
- `daily-reflection-demo-user`: Runs daily at 16:30
- `weekly-growth-demo-user`: Runs Sundays at 10:00

## Development

### Adding New Workflows

1. Create workflow file:

```bash
polytope run flowmentor-api-add-temporal-workflow new_workflow_name
```

2. Implement workflow logic in `src/backend/workflows/new_workflow_name.py`

3. Add API route in `src/backend/routes/base.py`

4. (Optional) Add to scheduler in `src/backend/workflows/scheduler.py`

### Workflow Best Practices

1. **Determinism**: Workflows must be deterministic

   - No random numbers, current time, or external API calls in workflow code
   - Use activities for non-deterministic operations

2. **Activities**: Use activities for:

   - Database operations
   - External API calls
   - File I/O
   - Any non-deterministic code

3. **Signals**: Use signals for:

   - External input during workflow execution
   - User interactions
   - Cancellation requests

4. **Timeouts**: Always set appropriate timeouts:
   - Activity timeouts
   - Workflow timeouts
   - Signal wait timeouts

## Monitoring

### Temporal UI

Access at http://localhost:8080 to:

- Monitor workflow execution
- View workflow history
- Debug failed workflows
- See scheduled workflows

### Health Check

```bash
curl http://localhost:3030/health?services=temporal
```

## Troubleshooting

### Workflows Not Appearing in UI

1. Check Temporal is running:

```bash
polytope list-services
```

2. Check API logs:

```bash
polytope get-container-logs flowmentor-api
```

### Schedule Not Triggering

1. Verify schedule exists in Temporal UI
2. Check schedule time zone configuration
3. Restart services if needed

### Activity Failures

1. Check activity timeout settings
2. Review activity logs in Temporal UI
3. Implement retry policies for transient failures

## Production Considerations

1. **User-Specific Schedules**: Create schedule for each user dynamically
2. **AI Integration**: Connect real AI services (OpenAI, Anthropic)
3. **Notification Service**: Implement real notification system
4. **Database Connection**: Pass Couchbase client to activities properly
5. **Error Handling**: Implement comprehensive error handling and logging
6. **Monitoring**: Set up alerts for workflow failures
7. **Scaling**: Configure Temporal workers based on load

## Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Workflow Patterns](https://docs.temporal.io/dev-guide/python/features)
