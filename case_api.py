"""API routes for case management: save, list, detail, comments, corrections, dashboard."""
import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import database as db

logger = logging.getLogger('uvicorn.error')
router = APIRouter(tags=['cases'])

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SaveCaseRequest(BaseModel):
    image_filename: str = Field(..., min_length=1, max_length=260)
    image_sha256: str = Field(..., min_length=64, max_length=64)
    metadata: dict
    scores: dict
    top1: str
    top1_score: float = Field(..., ge=0, le=1)
    prediction_seconds: float = Field(..., ge=0)
    device: str
    model_sha256: str = Field(..., min_length=64, max_length=64)
    api_version: str = '0.1.0'
    true_label: str | None = None


class CommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CorrectionRequest(BaseModel):
    corrected_label: str = Field(..., min_length=1)
    reason: str = Field('', max_length=2000)

# ---------------------------------------------------------------------------
# Case endpoints
# ---------------------------------------------------------------------------

@router.post('/cases')
def create_case(req: SaveCaseRequest):
    """Save a completed prediction as a case."""
    try:
        case = db.save_case(req.model_dump())
        return case
    except Exception as e:
        logger.exception('Failed to save case')
        raise HTTPException(500, f'Failed to save case: {e}')


@router.get('/cases')
def list_cases(limit: int = 50, offset: int = 0, label: str | None = None):
    """List saved cases with optional filtering and pagination."""
    if limit < 1 or limit > 200:
        raise HTTPException(422, 'limit must be between 1 and 200')
    if offset < 0:
        raise HTTPException(422, 'offset must be >= 0')
    return db.list_cases(limit=limit, offset=offset, label=label)


@router.get('/cases/{case_id}')
def get_case(case_id: str):
    """Get full details of a single case."""
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(404, 'Case not found')
    case['comments'] = db.list_comments(case_id)
    case['corrections'] = db.list_corrections(case_id)
    return case


@router.delete('/cases/{case_id}')
def delete_case(case_id: str):
    """Delete a case and its comments/corrections."""
    if not db.delete_case(case_id):
        raise HTTPException(404, 'Case not found')
    return {'deleted': True}


# ---------------------------------------------------------------------------
# Comment endpoints
# ---------------------------------------------------------------------------

@router.post('/cases/{case_id}/comments')
def add_comment(case_id: str, req: CommentRequest):
    try:
        return db.add_comment(case_id, req.content)
    except ValueError:
        raise HTTPException(404, 'Case not found')


@router.get('/cases/{case_id}/comments')
def list_comments(case_id: str):
    return db.list_comments(case_id)


# ---------------------------------------------------------------------------
# Correction endpoints
# ---------------------------------------------------------------------------

@router.post('/cases/{case_id}/corrections')
def add_correction(case_id: str, req: CorrectionRequest):
    try:
        return db.add_correction(case_id, req.corrected_label, req.reason)
    except ValueError as e:
        raise HTTPException(422 if 'Invalid label' in str(e) else 404, str(e))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get('/dashboard/stats')
def dashboard_stats():
    return db.get_stats()
