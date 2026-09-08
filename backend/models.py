from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class Fact(BaseModel):
    id: str
    subject: str
    predicate: str
    object: str
    normalized_value: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    fiscal_period: Optional[str] = None
    scope: Optional[str] = "consolidated"
    doc_id: str
    page: int
    quote: str
    bbox: Optional[List[float]] = None
    is_verified: bool = True
    confidence: float = 0.90
    fact_type: Optional[str] = "financial"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    is_superseded: bool = False
    superseded_by: Optional[str] = None

class Entity(BaseModel):
    id: str
    canonical_name: str
    entity_type: str = "corporation"
    aliases: List[str] = Field(default_factory=list)

class Reconciliation(BaseModel):
    id: str
    type: Literal["corroboration", "contradiction", "reconciled", "failure"]
    factA: Fact
    factB: Fact
    reasoning: str
    axis_of_difference: Optional[str] = None
    confidence: float = 0.95

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    ingested_at: str

class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    facts_extracted: int
    reconciliations_count: int
    status: str = "success"
