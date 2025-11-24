from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class BiasLabel(str, Enum):
    LEFT = "Left"
    LEAN_LEFT = "Lean Left"
    CENTER = "Center"
    LEAN_RIGHT = "Lean Right"
    RIGHT = "Right"
    NOT_AVAILABLE = "N/A"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class Article(BaseModel):
    url: str
    headline: str
    summary: str  # Kept for backward compatibility (can be same as tldr)
    tldr_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    bias_label: BiasLabel = BiasLabel.NOT_AVAILABLE
    topic_tags: List[str] = []
    keywords: List[str] = []
    processing_status: ProcessingStatus = ProcessingStatus.PROCESSED # Default to processed for existing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expire_at: datetime

class SearchRequest(BaseModel):
    query: str
