"""
Purifiers API Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.purifier import PurifierCreate, PurifierUpdate, PurifierResponse
from app.services.purifier_service import (
    get_purifiers, get_purifier_by_id, create_purifier, update_purifier, delete_purifier
)

router = APIRouter(prefix="/purifiers", tags=["Purifiers"])

@router.get("", response_model=List[PurifierResponse])
def list_purifiers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all registered virtual purifiers."""
    return get_purifiers(db, skip=skip, limit=limit)

@router.post("", response_model=PurifierResponse, status_code=status.HTTP_201_CREATED)
def add_purifier(data: PurifierCreate, db: Session = Depends(get_db)):
    """Create a new virtual purifier configuration profile."""
    return create_purifier(db, data)

@router.get("/{purifier_id}", response_model=PurifierResponse)
def get_purifier(purifier_id: str, db: Session = Depends(get_db)):
    """Get details of a specific virtual purifier."""
    p = get_purifier_by_id(db, purifier_id)
    if not p:
        raise HTTPException(status_code=404, detail="Purifier profile not found")
    return p

@router.put("/{purifier_id}", response_model=PurifierResponse)
def edit_purifier(purifier_id: str, data: PurifierUpdate, db: Session = Depends(get_db)):
    """Update virtual purifier parameters."""
    p = update_purifier(db, purifier_id, data)
    if not p:
        raise HTTPException(status_code=404, detail="Purifier profile not found")
    return p

@router.delete("/{purifier_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_purifier(purifier_id: str, db: Session = Depends(get_db)):
    """Delete a virtual purifier profile."""
    success = delete_purifier(db, purifier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Purifier profile not found")
    return None
