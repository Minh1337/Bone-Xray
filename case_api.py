"""API routes for case management: save, list, detail, comments, corrections, dashboard."""
import logging
from time import monotonic

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

import database as db

logger = logging.getLogger('uvicorn.error')
router = APIRouter(tags=['cases'])

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SaveCaseRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    prediction_id: str = Field(..., min_length=32, max_length=128)
    true_label: str | None = None

    @field_validator('true_label')
    @classmethod
    def valid_true_label(cls, value):
        if value is not None and value not in db.VALID_LABELS:
            raise ValueError('Unknown true label')
        return value


class CommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CorrectionRequest(BaseModel):
    corrected_label: str = Field(..., min_length=1)
    reason: str = Field('', max_length=2000)

# ---------------------------------------------------------------------------
# Case endpoints
# ---------------------------------------------------------------------------

@router.post('/cases')
def create_case(req: SaveCaseRequest, request: Request):
    """Save a completed prediction as a case."""
    try:
        with request.app.state.pending_lock:
            pending = request.app.state.pending_predictions.get(req.prediction_id)
            if pending is None or monotonic() - pending[0] >= 600:
                raise HTTPException(422, 'Prediction expired or unknown; analyze the image again')
            case = db.save_case({**pending[1], 'true_label': req.true_label})
            del request.app.state.pending_predictions[req.prediction_id]
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Failed to save case')
        raise HTTPException(500, 'Failed to save case; inspect server log')


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
