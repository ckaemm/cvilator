"""
CVilator CV yönetimi API router'ı.

CV yükleme, listeleme, detay görüntüleme ve silme endpoint'lerini içerir.
"""

import logging
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from models.database import CV, get_db
from schemas.cv import CVDetail, CVListItem, CVUploadResponse
from services.pdf_parser import parse_docx, parse_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cv", tags=["CV"])

UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx"}


def _get_file_extension(filename: str) -> str:
    """Dosya uzantısını küçük harfle döndürür.

    Args:
        filename: Dosya adı.

    Returns:
        str: Dosya uzantısı (ör. ".pdf").
    """
    return os.path.splitext(filename)[1].lower()


@router.post("/upload", response_model=CVUploadResponse, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CVUploadResponse:
    """CV dosyası yükler, parse eder ve veritabanına kaydeder.

    Desteklenen formatlar: PDF, DOCX.
    Maksimum dosya boyutu: 10 MB.

    Args:
        file: Yüklenen CV dosyası (multipart/form-data).
        db: Veritabanı oturumu.

    Returns:
        CVUploadResponse: Yüklenen CV'nin özet bilgileri.

    Raises:
        HTTPException 400: Geçersiz dosya formatı veya boyut aşımı.
        HTTPException 500: Dosya kaydetme veya parse hatası.
    """
    try:
        # Dosya uzantısı kontrolü
        extension = _get_file_extension(file.filename or "")
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya formatı: '{extension}'. "
                f"Kabul edilen formatlar: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Dosya boyutu kontrolü
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Dosya boyutu çok büyük. Maksimum: {MAX_FILE_SIZE // (1024 * 1024)} MB.",
            )

        # Dosyayı kaydet (UUID ile yeniden adlandır)
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("Dosya kaydedildi: %s -> %s", file.filename, file_path)

        # Parse et
        if extension == ".pdf":
            parsed = parse_pdf(file_path)
        else:
            parsed = parse_docx(file_path)

        # Veritabanına kaydet
        cv_record = CV(
            filename=file.filename or "unknown",
            file_path=file_path,
            raw_text=parsed["raw_text"],
            sections=parsed["sections"],
        )
        db.add(cv_record)
        db.commit()
        db.refresh(cv_record)

        logger.info("CV veritabanına kaydedildi. ID: %d", cv_record.id)

        # raw_text'i kısalt (maks 500 karakter)
        truncated_raw_text = (
            cv_record.raw_text[:500] if cv_record.raw_text else None
        )

        return CVUploadResponse(
            id=cv_record.id,
            filename=cv_record.filename,
            raw_text=truncated_raw_text,
            sections=cv_record.sections,
            created_at=cv_record.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CV yükleme sırasında hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV yüklenirken beklenmeyen bir hata oluştu.",
        ) from e


@router.get("/list", response_model=List[CVListItem])
async def list_cvs(db: Session = Depends(get_db)) -> List[CVListItem]:
    """Tüm CV'leri listeler.

    Oluşturulma tarihine göre azalan sırada (en yeniden en eskiye) döndürür.

    Args:
        db: Veritabanı oturumu.

    Returns:
        List[CVListItem]: CV listesi.
    """
    try:
        cvs = db.query(CV).order_by(CV.created_at.desc()).all()
        logger.info("%d adet CV listelendi.", len(cvs))
        return [
            CVListItem(
                id=cv.id,
                filename=cv.filename,
                ats_score=cv.ats_score,
                created_at=cv.created_at,
            )
            for cv in cvs
        ]
    except Exception as e:
        logger.exception("CV listesi alınırken hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV listesi alınırken beklenmeyen bir hata oluştu.",
        ) from e


@router.get("/{cv_id}", response_model=CVDetail)
async def get_cv(cv_id: int, db: Session = Depends(get_db)) -> CVDetail:
    """Belirtilen ID'ye sahip CV'nin detaylarını döndürür.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        db: Veritabanı oturumu.

    Returns:
        CVDetail: CV'nin tüm alanları.

    Raises:
        HTTPException 404: CV bulunamazsa.
    """
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if cv is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {cv_id} ile CV bulunamadı.",
            )

        logger.info("CV detayı döndürüldü. ID: %d", cv.id)
        return CVDetail(
            id=cv.id,
            filename=cv.filename,
            file_path=cv.file_path,
            raw_text=cv.raw_text,
            sections=cv.sections,
            ats_score=cv.ats_score,
            created_at=cv.created_at,
            updated_at=cv.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CV detayı alınırken hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV detayı alınırken beklenmeyen bir hata oluştu.",
        ) from e


@router.delete("/{cv_id}", status_code=200)
async def delete_cv(cv_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Belirtilen ID'ye sahip CV'yi veritabanından ve diskten siler.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        db: Veritabanı oturumu.

    Returns:
        dict: Silme işlemi başarı mesajı.

    Raises:
        HTTPException 404: CV bulunamazsa.
    """
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if cv is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {cv_id} ile CV bulunamadı.",
            )

        # Dosyayı diskten sil
        if cv.file_path and os.path.exists(cv.file_path):
            os.remove(cv.file_path)
            logger.info("Dosya diskten silindi: %s", cv.file_path)
        else:
            logger.warning(
                "Dosya diskten bulunamadı (zaten silinmiş olabilir): %s",
                cv.file_path,
            )

        # Veritabanından sil
        db.delete(cv)
        db.commit()

        logger.info("CV silindi. ID: %d", cv_id)
        return {"message": f"CV (ID: {cv_id}) başarıyla silindi."}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CV silinirken hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV silinirken beklenmeyen bir hata oluştu.",
        ) from e
