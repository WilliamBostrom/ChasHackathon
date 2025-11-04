# PostgreSQL Setup Summary

This document summarizes the changes made to configure PostgreSQL and Temporal.io properly.

## Changes Made

### 1. Created PostgreSQL Module (`modules/postgres/polytope.yml`)

- Added PostgreSQL 15 Alpine container configuration
- Configured database with:
  - Username: `postgres`
  - Password: `password`
  - Database: `flowmentor`
  - Port: `5432`
- Set up persistent volume for data storage

### 2. Updated Main Configuration (`polytope.yml`)

- Added `modules/postgres` to the include list
- **Replaced `couchbase` with `postgres`** in the default run tools
- Reordered services to start in correct sequence:
  1. `postgres` (database must start first)
  2. `temporal` (depends on postgres)
  3. `temporal-ui`
  4. `flowmentor-api`
  5. `flowmentor-frontend`

### 3. Updated FlowMentor API Configuration (`modules/flowmentor-api/polytope.yml`)

- Added complete PostgreSQL database environment variables:
  - `DATABASE_HOST=postgres`
  - `DATABASE_PORT=5432`
  - `DATABASE_NAME=flowmentor`
  - `DATABASE_USERNAME=postgres`
  - `DATABASE_PASSWORD=password`

### 4. Temporal Configuration (Already Correct)

The Temporal configuration in `modules/temporal/polytope.yml` was already properly configured to use PostgreSQL:

- `DB=postgres12`
- `POSTGRES_SEEDS=postgres` (connects to postgres service)
- `POSTGRES_USER=postgres`
- `POSTGRES_PWD=password`

## How to Start the Services

Run the following command to start all services:

```bash
polytope run
```

This will start:

1. PostgreSQL database
2. Temporal server (connecting to PostgreSQL)
3. Temporal UI (accessible at http://localhost:8233)
4. FlowMentor API (accessible at http://localhost:3030)
5. FlowMentor Frontend

## Verification Steps

1. **Check PostgreSQL is running:**

   ```bash
   docker ps | grep postgres
   ```

2. **Check Temporal is running:**

   ```bash
   docker ps | grep temporal
   ```

3. **Access Temporal UI:**
   Open http://localhost:8233 in your browser

4. **Check FlowMentor API logs:**
   Look for successful database connection messages

## Database Connection Details

The application connects to PostgreSQL using these settings:

- Host: `postgres` (service name in Docker network)
- Port: `5432`
- Database: `flowmentor`
- Username: `postgres`
- Password: `password`

## Notes

- Couchbase has been completely removed from the configuration
- All services use the internal Docker network for communication
- PostgreSQL data is persisted in a Docker volume named `postgres-data`
- Temporal stores its state in PostgreSQL, not an external database
