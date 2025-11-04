# Troubleshooting Guide

## Issues Fixed

### 1. Frontend Port Configuration ✅

**Problem:** Frontend was running on port 51732 instead of 5173
**Solution:** Updated `modules/flowmentor-frontend/polytope.yml` to use port 5173

### 2. Database Configuration ✅

**Problem:** Couchbase was configured but PostgreSQL should be used
**Solution:**

- Created PostgreSQL module
- Updated main `polytope.yml` to use `postgres` instead of `couchbase`
- Added complete database environment variables to flowmentor-api

### 3. Added Comprehensive Debugging ✅

Added console.logs throughout the application to help diagnose issues:

- API request/response interceptors in `app/lib/api.ts`
- Task addition debugging in `app/routes/tasks.tsx`
- Task loading debugging

## How to Apply Changes

### Step 1: Stop All Services

```bash
# Stop polytope services
polytope stop
```

### Step 2: Restart Services

```bash
# Start all services with new configuration
polytope run
```

The services should now start in this order:

1. `postgres` on port 5432
2. `temporal` on port 7233
3. `temporal-ui` on port 8233
4. `flowmentor-api` on port 3030
5. `flowmentor-frontend` on port 5173

### Step 3: Verify Services Are Running

Check that all services are running correctly:

```bash
polytope status
```

You should see:

```
ID                   Status   Exposed Ports
postgres             Running  TCP 5432
temporal             Running  TCP 7233
temporal-ui          Running  HTTP 8233
flowmentor-api       Running  HTTP 3030
flowmentor-frontend  Running  HTTP 5173  ⬅️ Should be 5173 now!
```

## Accessing the Application

### Frontend

- **URL:** http://localhost:5173
- **Routes:**
  - `/` - Home
  - `/tasks` - Task management
  - `/plan` - AI-generated day plan
  - `/morning` - Morning check-in
  - `/afternoon` - Afternoon reflection
  - `/weekly` - Weekly summary

### API

- **URL:** http://localhost:3030
- **Endpoints:**
  - `GET /tasks?date=YYYY-MM-DD` - Get tasks
  - `POST /tasks` - Add task
  - `PATCH /tasks/{id}` - Update task
  - `DELETE /tasks/{id}` - Delete task

### Temporal UI

- **URL:** http://localhost:8233
- Monitor workflow executions and task queues

## Debugging Task Addition Issues

When you try to add a task, open the browser console (F12) and look for:

### 1. Task Submission Flow

```
🚀 Starting to add task...
📝 Task data to send: {type, title, duration, time, completed, date}
🌐 API Base URL: http://localhost:3030
🌐 API Request: {method, url, baseURL, fullURL, data}
✅ API Response: {status, statusText, url, data}
✅ Task added successfully: [response data]
🔄 Reloading tasks...
📥 Loading tasks for date: YYYY-MM-DD
✅ Tasks loaded: [array of tasks]
🎉 Task form reset
🏁 Task addition process completed
```

### 2. Common Error Patterns

#### Network Error (Can't reach API)

```
❌ API Response Error: {
  message: "Network Error",
  ...
}
```

**Solution:**

- Check that flowmentor-api is running: `polytope status`
- Verify API is accessible: `curl http://localhost:3030/health` (if health endpoint exists)
- Check API logs for errors

#### 404 Not Found

```
❌ API Response Error: {
  status: 404,
  statusText: "Not Found"
}
```

**Solution:**

- Check the API endpoint path is correct
- Verify the backend route handler exists

#### 500 Internal Server Error

```
❌ API Response Error: {
  status: 500,
  data: {error: "..."}
}
```

**Solution:**

- Check API container logs: `docker logs flowmentor-api`
- Check PostgreSQL is running and accessible
- Verify database tables are created

## Database Issues

### Check PostgreSQL is Running

```bash
docker ps | grep postgres
```

### Connect to PostgreSQL

```bash
docker exec -it postgres psql -U postgres -d flowmentor
```

### Check Tables Exist

```sql
\dt
```

You should see tables like:

- `user_profiles`
- `routines`
- `checkins`
- `reflections`
- `ai_plans`
- `activities`

### Check Data

```sql
-- View all activities (tasks)
SELECT * FROM activities WHERE activity_type = 'todo';

-- View today's data
SELECT * FROM activities WHERE date = CURRENT_DATE;
```

## Environment Variables

### Frontend (.env)

The frontend gets its API URL from `VITE_API_BASE_URL` environment variable.

In the polytope configuration, this is set to:

```yaml
VITE_API_BASE_URL: http://localhost:3030
```

You can verify this in the console logs which will show:

```
🌐 API Base URL: http://localhost:3030
```

### API Database Connection

The API connects to PostgreSQL using:

```
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=flowmentor
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=password
```

## Quick Diagnostics Checklist

When tasks aren't being added:

- [ ] PostgreSQL is running: `docker ps | grep postgres`
- [ ] Temporal is running: `docker ps | grep temporal`
- [ ] API is running: `docker ps | grep flowmentor-api`
- [ ] Frontend is running on port 5173: `docker ps | grep flowmentor-frontend`
- [ ] Can access frontend: http://localhost:5173
- [ ] Can access API: http://localhost:3030
- [ ] Browser console shows API requests
- [ ] No error messages in console
- [ ] API container logs show no errors: `docker logs flowmentor-api`
- [ ] Database tables exist

## Getting Logs

### API Logs

```bash
docker logs flowmentor-api
# Or follow logs in real-time
docker logs -f flowmentor-api
```

### Frontend Logs

```bash
docker logs flowmentor-frontend
# Or follow logs in real-time
docker logs -f flowmentor-frontend
```

### PostgreSQL Logs

```bash
docker logs postgres
```

### Temporal Logs

```bash
docker logs temporal
```

## If Nothing Works

1. **Complete Reset:**

   ```bash
   # Stop all services
   polytope stop

   # Remove containers and volumes (WARNING: This deletes all data!)
   docker-compose down -v

   # Restart
   polytope run
   ```

2. **Check network connectivity between containers:**

   ```bash
   # From API container, ping postgres
   docker exec flowmentor-api ping postgres
   ```

3. **Verify API can connect to database:**
   Check API logs on startup for database connection messages

## Additional Resources

- See `POSTGRES_SETUP.md` for database configuration details
- Check Polytope documentation for service management
- Review Temporal UI at http://localhost:8233 for workflow status
