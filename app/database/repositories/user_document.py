import os
from uuid import uuid4
from fastapi import HTTPException, status
from typing import Dict, List
from uuid import UUID
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.database.models import Document
from sqlalchemy import func 
from fastapi import BackgroundTasks

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {".pdf", ".doc", ".docx"}

def user_uploads(user_id: UUID, file_map: Dict[str, UploadFile]) -> List[dict]:
    """
    file_map keys:  'cv', 'cover_letter', 'supporting_document'(optional)
    Returns list of metadata dicts for each saved file.
    """
    required = {"cv", "cover_letter"}
    if not required.issubset(file_map.keys()):
        raise HTTPException(400, "CV and Cover Letter are mandatory.")

    saved: List[dict] = []
    for doc_type, upload_file in file_map.items():
        ext = os.path.splitext(upload_file.filename)[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"Forbidden file type: {ext}")

        unique_name = f"{uuid4().hex}{ext}"
        dest = os.path.join(UPLOAD_DIR, unique_name)

        with open(dest, "wb") as f:
            f.write(upload_file.file.read())

        saved.append({
            "user_id": str(user_id),
            "file_type": doc_type,
            "original_name": upload_file.filename,
            "file_path": dest,
        })
    return  saved

def _validate_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Forbidden extension: {ext}")
    return ext

def _save_upload(upload: UploadFile) -> str:
    ext = _validate_ext(upload.filename)
    unique = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, unique)
    with open(path, "wb") as f:
        f.write(upload.file.read())
    return path

def _guard_last_required(db: Session, user_id: UUID, doc: Document) -> None:
    """
    Block deletion/replacement of the final CV or cover-letter.
    """
    if doc.file_type not in {"cv", "cover_letter"}:
        return                       # supporting docs are not required

    remaining = (
        db.query(Document)
        .filter_by(user_id=user_id, file_type=doc.file_type)
        .count()
    )
    if remaining <= 1:
        raise HTTPException(
            409,
            f"Cannot delete/overwrite your only {doc.file_type.replace('_', ' ')}."
        ) 

def delete_document(db: Session, doc_id: UUID, user_id: UUID) -> None:
    doc = db.get(Document, doc_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(404, "Document not found")

    _guard_last_required(db, user_id, doc)   # <-- guard

    path = doc.file_path
    db.delete(doc)
    db.commit()
    if os.path.isfile(path):
        os.remove(path)


def update_document(background: BackgroundTasks, db: Session, doc_id: UUID, user_id: UUID, new_file: UploadFile) -> dict:
    from .document_parser import parse_cv_task
    
    doc = db.get(Document, doc_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(404, "Document not found")
    if doc.file_type == "supporting_document":
        raise HTTPException(400, "Use /supporting endpoint for supporting docs")

    _guard_last_required(db, user_id, doc)   # <-- guard

    old_path = doc.file_path
    new_path = _save_upload(new_file)

    if doc.file_type == "cv":
        background.add_task(parse_cv_task, db, user_id, doc.id, new_path)
    doc.file_name = new_file.filename
    doc.file_path  = new_path
    db.commit()

    if os.path.isfile(old_path):
        os.remove(old_path)

    return {"doc_id": doc.id, "file_name": doc.file_name, "file_type": doc.file_type}

def list_user_documents(db: Session, user_id: UUID) -> List[dict]:
    rows = db.query(Document).filter(Document.user_id == user_id).all()
    return [
        {
            "doc_id": str(r.id),
            "file_name": r.file_name,
            "file_type": r.file_type,
            
        }
        for r in rows
    ] 

def add_supporting_doc(db: Session, user_id: UUID, file: UploadFile | None) -> dict:
    """
    Add a *new* supporting document.
    Rejects duplicate file-name (case-insensitive) for this user.
    """
    if not file:
        raise HTTPException(400, "File is required to add a supporting document")

    # normalise name for comparison
    norm_name = file.filename.strip().lower()

    exists = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.file_type == "supporting_document",
            func.lower(Document.file_name) == norm_name,
        )
        .first()
    )
    if exists:
        raise HTTPException(409, f"A supporting document named '{file.filename}' already exists.")

    new_path = _save_upload(file)
    doc = Document(
        user_id=user_id,
        file_name=file.filename,
        file_type="supporting_document",
        file_path=new_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"doc_id": str(doc.id), "file_name": doc.file_name, "file_type": doc.file_type}


def get_document(db: Session, doc_id: UUID, user_id: UUID) -> dict:
    doc = db.get(Document, doc_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(404, "Document not found")
    return {
        "doc_id": str(doc.id),
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "file_path": doc.file_path,   # server path; expose only if you need it
        "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
    }