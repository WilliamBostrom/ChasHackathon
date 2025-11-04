"""Couchbase client for database operations."""

from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.exceptions import CouchbaseException
from ..utils import log

logger = log.get_logger(__name__)


class CouchbaseConf(BaseModel):
    """Couchbase connection configuration."""

    connection_string: str
    username: str
    password: str
    bucket_name: str


class CouchbaseClient:
    """Client for interacting with Couchbase."""

    def __init__(self, config: CouchbaseConf):
        """Initialize the Couchbase client with configuration."""
        self.config = config
        self.cluster: Optional[Cluster] = None
        self.bucket = None
        self.collection = None

    async def initialize(self) -> None:
        """Initialize the Couchbase connection."""
        try:
            logger.info(
                f"Initializing Couchbase connection to {self.config.connection_string}"
            )

            # Create authenticator
            auth = PasswordAuthenticator(self.config.username, self.config.password)

            # Connect to cluster
            self.cluster = Cluster(self.config.connection_string, ClusterOptions(auth))

            # Wait for cluster to be ready
            await self.cluster.wait_until_ready(timedelta(seconds=30))

            logger.info("Couchbase cluster connection established")

        except CouchbaseException as e:
            logger.error(f"Failed to initialize Couchbase: {e}")
            raise

    async def init_connection(self) -> None:
        """Initialize bucket and collection connections."""
        try:
            logger.info(f"Connecting to bucket: {self.config.bucket_name}")

            # Get bucket
            self.bucket = self.cluster.bucket(self.config.bucket_name)

            # Get default collection
            self.collection = self.bucket.default_collection()

            logger.info("Couchbase bucket and collection initialized")

        except CouchbaseException as e:
            logger.error(f"Failed to initialize bucket/collection: {e}")
            raise

    async def create_indexes(self) -> None:
        """Create necessary indexes for efficient querying."""
        try:
            logger.info("Creating Couchbase indexes")

            # Index for user lookups
            await self.cluster.query(
                f"""
                CREATE INDEX IF NOT EXISTS idx_userId 
                ON `{self.config.bucket_name}`(userId)
                """
            )

            # Index for date-based queries
            await self.cluster.query(
                f"""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON `{self.config.bucket_name}`(date)
                """
            )

            # Index for user + date queries
            await self.cluster.query(
                f"""
                CREATE INDEX IF NOT EXISTS idx_userId_date 
                ON `{self.config.bucket_name}`(userId, date)
                """
            )

            # Index for document type
            await self.cluster.query(
                f"""
                CREATE INDEX IF NOT EXISTS idx_type 
                ON `{self.config.bucket_name}`(type)
                """
            )

            # Index for embeddings (for future vector search integration)
            await self.cluster.query(
                f"""
                CREATE INDEX IF NOT EXISTS idx_embeddings 
                ON `{self.config.bucket_name}`(embedding)
                """
            )

            logger.info("Couchbase indexes created successfully")

        except CouchbaseException as e:
            logger.warning(
                f"Failed to create some indexes (they may already exist): {e}"
            )

    async def insert_document(self, doc_id: str, document: Dict[str, Any]) -> None:
        """Insert a document into Couchbase."""
        try:
            result = self.collection.insert(doc_id, document)
            logger.debug(f"Document inserted: {doc_id}")
            return result
        except CouchbaseException as e:
            logger.error(f"Failed to insert document {doc_id}: {e}")
            raise

    async def upsert_document(self, doc_id: str, document: Dict[str, Any]) -> None:
        """Upsert (insert or update) a document in Couchbase."""
        try:
            result = self.collection.upsert(doc_id, document)
            logger.debug(f"Document upserted: {doc_id}")
            return result
        except CouchbaseException as e:
            logger.error(f"Failed to upsert document {doc_id}: {e}")
            raise

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document from Couchbase."""
        try:
            result = self.collection.get(doc_id)
            return result.content_as[dict]
        except CouchbaseException as e:
            logger.warning(f"Document not found: {doc_id}")
            return None

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document from Couchbase."""
        try:
            self.collection.remove(doc_id)
            logger.debug(f"Document deleted: {doc_id}")
        except CouchbaseException as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    async def query(self, query_string: str, **kwargs) -> List[Dict[str, Any]]:
        """Execute a N1QL query."""
        try:
            result = self.cluster.query(query_string, QueryOptions(**kwargs))
            return [row for row in result]
        except CouchbaseException as e:
            logger.error(f"Query failed: {e}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user profile."""
        doc_id = f"profile::{user_id}"
        return await self.get_document(doc_id)

    async def upsert_user_profile(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> None:
        """Create or update a user profile."""
        doc_id = f"profile::{user_id}"
        document = {
            "type": "profile",
            "userId": user_id,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            **profile_data,
        }
        await self.upsert_document(doc_id, document)

    async def get_user_routines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all routines for a user."""
        query_string = f"""
        SELECT * FROM `{self.config.bucket_name}`
        WHERE type = 'routine' AND userId = $userId
        ORDER BY createdAt DESC
        """
        results = await self.query(query_string, userId=user_id)
        return [row[self.config.bucket_name] for row in results]

    async def upsert_routine(
        self, user_id: str, routine_id: str, routine_data: Dict[str, Any]
    ) -> None:
        """Create or update a routine."""
        doc_id = f"routine::{user_id}::{routine_id}"
        document = {
            "type": "routine",
            "userId": user_id,
            "routineId": routine_id,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            **routine_data,
        }
        await self.upsert_document(doc_id, document)

    async def get_daily_checkins(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get daily check-ins for a user on a specific date."""
        query_string = f"""
        SELECT * FROM `{self.config.bucket_name}`
        WHERE type = 'checkin' AND userId = $userId AND date = $date
        ORDER BY timestamp DESC
        """
        results = await self.query(query_string, userId=user_id, date=date)
        return [row[self.config.bucket_name] for row in results]

    async def insert_checkin(
        self, user_id: str, date: str, checkin_data: Dict[str, Any]
    ) -> None:
        """Insert a daily check-in."""
        timestamp = datetime.utcnow().isoformat()
        doc_id = f"checkin::{user_id}::{date}::{timestamp}"
        document = {
            "type": "checkin",
            "userId": user_id,
            "date": date,
            "timestamp": timestamp,
            **checkin_data,
        }
        await self.insert_document(doc_id, document)

    async def get_reflections(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get reflections for a user, optionally filtered by date range."""
        if start_date and end_date:
            query_string = f"""
            SELECT * FROM `{self.config.bucket_name}`
            WHERE type = 'reflection' AND userId = $userId 
            AND date >= $startDate AND date <= $endDate
            ORDER BY date DESC
            """
            results = await self.query(
                query_string, userId=user_id, startDate=start_date, endDate=end_date
            )
        else:
            query_string = f"""
            SELECT * FROM `{self.config.bucket_name}`
            WHERE type = 'reflection' AND userId = $userId
            ORDER BY date DESC
            """
            results = await self.query(query_string, userId=user_id)

        return [row[self.config.bucket_name] for row in results]

    async def insert_reflection(
        self, user_id: str, date: str, reflection_data: Dict[str, Any]
    ) -> None:
        """Insert a reflection."""
        doc_id = f"reflection::{user_id}::{date}"
        document = {
            "type": "reflection",
            "userId": user_id,
            "date": date,
            "createdAt": datetime.utcnow().isoformat(),
            **reflection_data,
        }
        await self.upsert_document(doc_id, document)

    async def get_ai_plans(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get AI-generated plans for a user on a specific date."""
        query_string = f"""
        SELECT * FROM `{self.config.bucket_name}`
        WHERE type = 'ai_plan' AND userId = $userId AND date = $date
        ORDER BY createdAt DESC
        """
        results = await self.query(query_string, userId=user_id, date=date)
        return [row[self.config.bucket_name] for row in results]

    async def insert_ai_plan(
        self, user_id: str, date: str, plan_data: Dict[str, Any]
    ) -> None:
        """Insert an AI-generated plan."""
        timestamp = datetime.utcnow().isoformat()
        doc_id = f"ai_plan::{user_id}::{date}::{timestamp}"
        document = {
            "type": "ai_plan",
            "userId": user_id,
            "date": date,
            "createdAt": timestamp,
            "activities": plan_data.get("activities", []),
            "embedding": plan_data.get("embedding"),  # For vector search
            **plan_data,
        }
        await self.insert_document(doc_id, document)

    async def get_activities(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get all activities (focus blocks, meetings, routines) for a user on a date."""
        query_string = f"""
        SELECT * FROM `{self.config.bucket_name}`
        WHERE type IN ['focus_block', 'meeting', 'routine_instance'] 
        AND userId = $userId AND date = $date
        ORDER BY startTime
        """
        results = await self.query(query_string, userId=user_id, date=date)
        return [row[self.config.bucket_name] for row in results]

    async def insert_activity(
        self, user_id: str, date: str, activity_type: str, activity_data: Dict[str, Any]
    ) -> None:
        """Insert an activity (focus block, meeting, or routine instance)."""
        timestamp = datetime.utcnow().isoformat()
        doc_id = f"{activity_type}::{user_id}::{date}::{timestamp}"
        document = {
            "type": activity_type,
            "userId": user_id,
            "date": date,
            "createdAt": timestamp,
            **activity_data,
        }
        await self.insert_document(doc_id, document)

    async def close(self) -> None:
        """Close the Couchbase connection."""
        if self.cluster:
            logger.info("Closing Couchbase connection")
            # Couchbase Python SDK handles cleanup automatically
            self.cluster = None
            self.bucket = None
            self.collection = None
