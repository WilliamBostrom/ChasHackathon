"""Data models for the FlowMentor API."""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserProfile(BaseModel):
    """User profile data model."""

    userId: str
    name: Optional[str] = None
    email: Optional[str] = None
    preferences: Optional[dict] = None
    timezone: Optional[str] = None


class Activity(BaseModel):
    """Activity data model (focus blocks, meetings, routines)."""

    title: str
    startTime: str
    endTime: str
    type: str  # 'focus_block', 'meeting', 'routine_instance'
    description: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None


class Routine(BaseModel):
    """Routine data model."""

    routineId: str
    name: str
    description: Optional[str] = None
    frequency: str  # 'daily', 'weekly', 'custom'
    timeOfDay: Optional[str] = None
    duration: Optional[int] = None  # in minutes
    activities: List[Activity] = []
    isActive: bool = True


class CheckIn(BaseModel):
    """Daily check-in data model."""

    mood: Optional[str] = None
    energy: Optional[int] = Field(None, ge=1, le=10)
    focus: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    goals: Optional[List[str]] = None


class Reflection(BaseModel):
    """Reflection data model."""

    content: str
    achievements: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    learnings: Optional[str] = None
    gratitude: Optional[List[str]] = None
    mood: Optional[str] = None
    embedding: Optional[List[float]] = None  # For vector search


class AIPlan(BaseModel):
    """AI-generated plan data model."""

    title: str
    description: Optional[str] = None
    activities: List[Activity]
    recommendations: Optional[List[str]] = None
    focusAreas: Optional[List[str]] = None
    estimatedProductivity: Optional[float] = None
    embedding: Optional[List[float]] = None  # For vector search


class UserProfileResponse(BaseModel):
    """Response model for user profile."""

    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class RoutineListResponse(BaseModel):
    """Response model for routine list."""

    success: bool
    data: Optional[List[dict]] = None
    message: Optional[str] = None


class CheckInListResponse(BaseModel):
    """Response model for check-in list."""

    success: bool
    data: Optional[List[dict]] = None
    message: Optional[str] = None


class ReflectionListResponse(BaseModel):
    """Response model for reflection list."""

    success: bool
    data: Optional[List[dict]] = None
    message: Optional[str] = None


class AIPlanListResponse(BaseModel):
    """Response model for AI plan list."""

    success: bool
    data: Optional[List[dict]] = None
    message: Optional[str] = None


class ActivityListResponse(BaseModel):
    """Response model for activity list."""

    success: bool
    data: Optional[List[dict]] = None
    message: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool
    message: str
