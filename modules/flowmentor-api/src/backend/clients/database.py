"""PostgreSQL database client for FlowMentor."""

from typing import Optional, Any, Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
from ..utils import log

logger = log.get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class DatabaseConf(BaseModel):
    """PostgreSQL database configuration."""

    host: str
    port: int = 5432
    database: str
    username: str
    password: str


class DatabaseClient:
    """Client for interacting with PostgreSQL database."""

    def __init__(self, config: DatabaseConf):
        """Initialize the database client with configuration."""
        self.config = config
        self.engine = None
        self.session_maker = None

    async def initialize(self) -> None:
        """Initialize the database connection."""
        try:
            logger.info(
                f"Initializing PostgreSQL connection to {self.config.host}:{self.config.port}/{self.config.database}"
            )

            # Create async engine
            connection_string = (
                f"postgresql+asyncpg://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            self.engine = create_async_engine(
                connection_string,
                echo=False,
                pool_pre_ping=True,
            )

            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("PostgreSQL connection established")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    async def create_tables(self) -> None:
        """Create all database tables."""
        try:
            logger.info("Creating database tables")
            
            async with self.engine.begin() as conn:
                # Create tables for user profiles
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id VARCHAR(255) PRIMARY KEY,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create tables for routines
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS routines (
                        routine_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create tables for check-ins
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS checkins (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        date DATE NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data JSONB NOT NULL
                    )
                """))

                # Create tables for reflections
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reflections (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        date DATE NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create tables for AI plans
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ai_plans (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        date DATE NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create tables for activities
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS activities (
                        id SERIAL PRIMARY KEY,
                        activity_id VARCHAR(255) UNIQUE,
                        user_id VARCHAR(255) NOT NULL,
                        date DATE NOT NULL,
                        activity_type VARCHAR(50) NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create indexes for efficient querying
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_routines_user_id ON routines(user_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_checkins_user_date ON checkins(user_id, date)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reflections_user_date ON reflections(user_id, date)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_plans_user_date ON ai_plans(user_id, date)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activities_user_date ON activities(user_id, date)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type)"))

            logger.info("Database tables created successfully")

        except Exception as e:
            logger.warning(f"Failed to create some tables (they may already exist): {e}")

    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self.session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.session_maker()

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user profile."""
        async with self.get_session() as session:
            result = await session.execute(
                text("SELECT data FROM user_profiles WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            return row[0] if row else None

    async def upsert_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Create or update a user profile."""
        async with self.get_session() as session:
            profile_data["userId"] = user_id
            profile_data["updatedAt"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO user_profiles (user_id, data, updated_at)
                    VALUES (:user_id, :data::jsonb, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET data = :data::jsonb, updated_at = CURRENT_TIMESTAMP
                """),
                {"user_id": user_id, "data": profile_data}
            )
            await session.commit()

    async def get_user_routines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all routines for a user."""
        async with self.get_session() as session:
            result = await session.execute(
                text("SELECT data FROM routines WHERE user_id = :user_id ORDER BY created_at DESC"),
                {"user_id": user_id}
            )
            return [row[0] for row in result.fetchall()]

    async def upsert_routine(self, user_id: str, routine_id: str, routine_data: Dict[str, Any]) -> None:
        """Create or update a routine."""
        async with self.get_session() as session:
            routine_data["userId"] = user_id
            routine_data["routineId"] = routine_id
            routine_data["updatedAt"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO routines (routine_id, user_id, data, updated_at)
                    VALUES (:routine_id, :user_id, :data::jsonb, CURRENT_TIMESTAMP)
                    ON CONFLICT (routine_id)
                    DO UPDATE SET data = :data::jsonb, updated_at = CURRENT_TIMESTAMP
                """),
                {"routine_id": routine_id, "user_id": user_id, "data": routine_data}
            )
            await session.commit()

    async def get_daily_checkins(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get daily check-ins for a user on a specific date."""
        async with self.get_session() as session:
            result = await session.execute(
                text("""
                    SELECT data FROM checkins 
                    WHERE user_id = :user_id AND date = :date
                    ORDER BY timestamp DESC
                """),
                {"user_id": user_id, "date": date}
            )
            return [row[0] for row in result.fetchall()]

    async def insert_checkin(self, user_id: str, date: str, checkin_data: Dict[str, Any]) -> None:
        """Insert a daily check-in."""
        async with self.get_session() as session:
            checkin_data["userId"] = user_id
            checkin_data["date"] = date
            checkin_data["timestamp"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO checkins (user_id, date, data)
                    VALUES (:user_id, :date, :data::jsonb)
                """),
                {"user_id": user_id, "date": date, "data": checkin_data}
            )
            await session.commit()

    async def get_reflections(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get reflections for a user, optionally filtered by date range."""
        async with self.get_session() as session:
            if start_date and end_date:
                result = await session.execute(
                    text("""
                        SELECT data FROM reflections
                        WHERE user_id = :user_id AND date >= :start_date AND date <= :end_date
                        ORDER BY date DESC
                    """),
                    {"user_id": user_id, "start_date": start_date, "end_date": end_date}
                )
            else:
                result = await session.execute(
                    text("SELECT data FROM reflections WHERE user_id = :user_id ORDER BY date DESC"),
                    {"user_id": user_id}
                )
            return [row[0] for row in result.fetchall()]

    async def insert_reflection(self, user_id: str, date: str, reflection_data: Dict[str, Any]) -> None:
        """Insert a reflection."""
        async with self.get_session() as session:
            reflection_data["userId"] = user_id
            reflection_data["date"] = date
            reflection_data["createdAt"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO reflections (user_id, date, data)
                    VALUES (:user_id, :date, :data::jsonb)
                """),
                {"user_id": user_id, "date": date, "data": reflection_data}
            )
            await session.commit()

    async def get_ai_plans(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get AI-generated plans for a user on a specific date."""
        async with self.get_session() as session:
            result = await session.execute(
                text("""
                    SELECT data FROM ai_plans
                    WHERE user_id = :user_id AND date = :date
                    ORDER BY created_at DESC
                """),
                {"user_id": user_id, "date": date}
            )
            return [row[0] for row in result.fetchall()]

    async def insert_ai_plan(self, user_id: str, date: str, plan_data: Dict[str, Any]) -> None:
        """Insert an AI-generated plan."""
        async with self.get_session() as session:
            plan_data["userId"] = user_id
            plan_data["date"] = date
            plan_data["createdAt"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO ai_plans (user_id, date, data)
                    VALUES (:user_id, :date, :data::jsonb)
                """),
                {"user_id": user_id, "date": date, "data": plan_data}
            )
            await session.commit()

    async def get_activities(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get all activities for a user on a date."""
        async with self.get_session() as session:
            result = await session.execute(
                text("""
                    SELECT data FROM activities
                    WHERE user_id = :user_id AND date = :date
                    ORDER BY (data->>'startTime')
                """),
                {"user_id": user_id, "date": date}
            )
            return [row[0] for row in result.fetchall()]

    async def insert_activity(
        self, user_id: str, date: str, activity_type: str, activity_data: Dict[str, Any]
    ) -> None:
        """Insert an activity (focus block, meeting, or routine instance)."""
        async with self.get_session() as session:
            activity_id = f"{activity_type}::{user_id}::{date}::{datetime.utcnow().isoformat()}"
            activity_data["type"] = activity_type
            activity_data["userId"] = user_id
            activity_data["date"] = date
            activity_data["createdAt"] = datetime.utcnow().isoformat()
            
            await session.execute(
                text("""
                    INSERT INTO activities (activity_id, user_id, date, activity_type, data)
                    VALUES (:activity_id, :user_id, :date, :activity_type, :data::jsonb)
                """),
                {
                    "activity_id": activity_id,
                    "user_id": user_id,
                    "date": date,
                    "activity_type": activity_type,
                    "data": activity_data
                }
            )
            await session.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            logger.info("Closing PostgreSQL connection")
            await self.engine.dispose()
            self.engine = None
            self.session_maker = None
