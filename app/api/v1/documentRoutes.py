from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Optional
from app.database.models import User, Document, ParsedProfile
from app.utils import dbSession, apiResponse
from app.database.repositories import (
    get_current_user, user_uploads, update_document, 
    add_supporting_doc, delete_document, list_user_documents, 
    get_document
    )

router = APIRouter()

from fastapi import BackgroundTasks

@router.post("/upload")
def upload_documents(
    background: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    cv: UploadFile = File(...),
    cover_letter: UploadFile = File(...),
    supporting: Optional[UploadFile] = File(None),
    db: Session = Depends(dbSession),
):
    from app.database.repositories import parse_cv_task
    # 1. save files (your existing helper)
    saved = user_uploads(user_id=current_user.id,
                        file_map={"cv": cv, "cover_letter": cover_letter}
                                | ({"supporting_document": supporting} if supporting else {}))

    docs_out = []
    for meta in saved:
        doc = Document(
            user_id=current_user.id,
            file_name=meta["original_name"],
            file_type=meta["file_type"],
            file_path=meta["file_path"],
        )
        db.add(doc)
        db.flush()          # get doc.id without commit
        docs_out.append(doc)

        # 2. schedule parsing **only for CV**
        if doc.file_type == "cv":
            background.add_task(parse_cv_task, current_user.id, doc.id, doc.file_path)

    db.commit()

    return apiResponse(
        "success",
        "Documents uploaded. CV parsing queued.",
        [{"document_id": str(d.id),
          "file_name": d.file_name,
          "file_type": d.file_type,
          "is_parsed": bool(d.parsed_profile)} for d in docs_out]
    )

@router.put("/document/{doc_id}")
async def change_document(
    doc_id: UUID,
    background: BackgroundTasks,
    new_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    data = update_document(
        background,
        db=db,
        doc_id=doc_id,
        user_id=current_user.id,
        new_file=new_file,
    )
    return apiResponse("success", "Document replaced", data)


@router.post("/supporting")
async def upsert_supporting_documents(
    current_user: User = Depends(get_current_user),
    file: UploadFile | None = File(None),   # None = remove supporting
    db: Session = Depends(dbSession),
):
    data = add_supporting_doc(db, current_user.id, file)
    return apiResponse("success", "Supporting document updated", data)


@router.delete("/document/{doc_id}")
async def remove_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    delete_document(db, doc_id, current_user.id)
    return apiResponse("success", "Document deleted")

@router.get("/documents")
async def my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    docs = list_user_documents(db, current_user.id)
    return apiResponse("success", None, docs)

# ------------------ get single document metadata ------------------------------
@router.get("/document/{doc_id}")
async def fetch_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    meta = get_document(db, doc_id, current_user.id)
    return apiResponse("success", None, meta)


@router.get("/parsed-profile")
def get_matching_payload(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    """Return the newest parsed CV data for the logged-in user."""
    row = (
        db.query(ParsedProfile)
        .join(Document)
        .filter(ParsedProfile.user_id == current_user.id,
                Document.file_type == "cv")
        .order_by(ParsedProfile.updated_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, "No parsed CV found")
    return apiResponse("success", None, row.payload)