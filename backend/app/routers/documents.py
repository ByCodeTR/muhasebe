"""
Document endpoints - upload, OCR, draft/confirm flow.
"""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentConfirm,
    DocumentDraft,
)

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all documents with optional filtering."""
    query = select(Document).order_by(Document.created_at.desc())
    
    if status_filter:
        query = query.where(Document.status == status_filter)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents


@router.get("/drafts", response_model=list[DocumentResponse])
async def list_drafts(db: AsyncSession = Depends(get_db)):
    """List all draft documents awaiting confirmation."""
    query = (
        select(Document)
        .where(Document.status == DocumentStatus.DRAFT.value)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document by ID."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document


@router.post("/upload", response_model=DocumentDraft)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a receipt/invoice image for OCR processing.
    Returns a draft with extracted fields for confirmation.
    """
    # Imports inside function to avoid circular imports
    from app.services.ocr_service import get_ocr_service
    from app.services.extraction_service import get_extraction_service
    from app.services.vendor_matcher import get_vendor_matcher
    import traceback

    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {allowed_types}",
            )
        
        # Check file size
        content = await file.read()
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.max_upload_size / 1024 / 1024}MB",
            )
        
        # Calculate hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Save file locally
        upload_dir = Path(settings.upload_dir)
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to /tmp if permissions fail
            upload_dir = Path("/tmp/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(file.filename or "image.jpg").suffix
        file_path = upload_dir / f"{file_hash}{file_ext}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # OCR Processing
        ocr_service = get_ocr_service()
        extraction_service = get_extraction_service()
        vendor_matcher = get_vendor_matcher()
        
        # Extract text from image
        ocr_result = ocr_service.extract_text(str(file_path))
        raw_text = ocr_result.get('text', '')
        # Log debug info
        print(f"OCR Result: {ocr_result}")
        
        # Extract structured fields
        extraction = extraction_service.extract(raw_text)
        
        # Try to match vendor
        # Fix: Ensure user_id is UUID
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001") 
        
        vendor_match = await vendor_matcher.find_match(
            db,
            user_id,
            vendor_name=extraction.vendor_name,
            vkn=extraction.vendor_vkn,
            tckn=extraction.vendor_tckn,
        )
        
        # Create document record
        document = Document(
            user_id=user_id,
            vendor_id=vendor_match.vendor_id if not vendor_match.is_new else None,
            status=DocumentStatus.DRAFT.value,
            doc_date=extraction.doc_date,
            doc_no=extraction.doc_no,
            currency=extraction.currency,
            total_gross=extraction.total_gross,
            total_tax=extraction.total_tax,
            total_net=extraction.total_net,
            raw_ocr_text=raw_text,
            extraction_json=extraction.to_dict(),
            confidence_score=ocr_result.get('confidence', 0),
            image_url=str(file_path),
            image_sha256=file_hash,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        ocr_confidence = ocr_result.get('confidence', 0)
        
        return DocumentDraft(
            vendor_name=extraction.vendor_name,
            vendor_confidence=vendor_match.confidence if not vendor_match.is_new else None,
            suggested_vendor_id=vendor_match.vendor_id,
            doc_date=extraction.doc_date,
            total_gross=extraction.total_gross,
            total_tax=extraction.total_tax,
            currency=extraction.currency,
            raw_ocr_text=raw_text[:500] if raw_text else None,
            confidence_score=extraction.confidence,
            extraction_details={
                "document_id": str(document.id),
                "ocr_confidence": ocr_confidence,
                "vendor_match_type": vendor_match.match_type,
                "is_new_vendor": vendor_match.is_new,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Upload Error: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload Error: {str(e)}",
        )




@router.post("/{document_id}/confirm", response_model=DocumentResponse)
async def confirm_document(
    document_id: uuid.UUID,
    data: DocumentConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Confirm a draft document and create ledger entry."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    if document.status != DocumentStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft documents can be confirmed",
        )
    
    # Update document with confirmed values
    document.vendor_id = data.vendor_id
    document.doc_date = data.doc_date
    document.total_gross = data.total_gross
    document.total_tax = data.total_tax
    document.status = DocumentStatus.POSTED.value
    document.updated_at = datetime.utcnow()
    
    # TODO: Create ledger entry
    
    await db.commit()
    await db.refresh(document)
    
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    document.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(document)
    
    return document


@router.post("/{document_id}/cancel")
async def cancel_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a document (soft delete)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    document.status = DocumentStatus.CANCELLED.value
    document.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Document cancelled"}
