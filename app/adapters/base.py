"""
Base models and contracts for KisanRadar data adapters.
STRICT RULE: REAL DATA ONLY. No synthetic, random or fabricated data.
"""
from datetime import datetime
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class SourceResult(BaseModel):
    source: str = Field(..., description="Human-readable name of the source")
    dataset_id: str = Field(..., description="Official provider dataset identifier")
    status: str = Field(..., description="live | cached | unavailable | SKIPPED-no-credentials")
    observed_through: Optional[str] = Field(None, description="ISO date of the latest observation returned")
    freshness_note: Optional[str] = Field(None, description="Detailed observation freshness explanation")
    fetched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    latency_ms: int = Field(0, description="Time taken to fetch data in milliseconds")
    n_obs: int = Field(0, description="Number of observations / pixels / records returned")
    units: Optional[str] = Field(None, description="Measurement units")
    error: Optional[str] = Field(None, description="Error detail if status is unavailable or skipped")
    data: Optional[Any] = Field(None, description="Actual data payload (or None on failure)")
