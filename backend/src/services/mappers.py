# services/mappers.py
"""
Mapping functions between DB models and API schemas.

WHY: Keeps DB models separate from API contracts.
Routes should never return SQLAlchemy models directly - always map to schemas.
"""
from typing import List
from src.schemas.segment import Segment
from src.schemas.style import Style
from src.models.segment import SegmentRow
from src.models.style import StyleRow


def segment_row_to_schema(row: SegmentRow) -> Segment:
    """
    Convert SegmentRow (DB model) to Segment (API schema).
    
    WHY: Routes should return Pydantic models, not SQLAlchemy models.
    This ensures API contracts are stable even if DB schema changes.
    """
    return Segment(
        id=row.id,
        start=row.start,
        end=row.end,
        text=row.text
    )


def segments_rows_to_schemas(rows: List[SegmentRow]) -> List[Segment]:
    """
    Convert list of SegmentRows to list of Segments.
    
    WHY: Convenience function for endpoints that return multiple segments.
    """
    return [segment_row_to_schema(row) for row in rows]


def style_row_to_schema(row: StyleRow) -> Style:
    """
    Convert StyleRow (DB model) to Style (API schema).
    
    WHY: Extracts JSONB data and validates it against Pydantic schema.
    """
    return Style(**row.style_json)

