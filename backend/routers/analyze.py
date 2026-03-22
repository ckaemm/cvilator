"""
CVilator ATS analiz router'ı.

CV'leri ATS kriterlerine göre skorlama endpoint'lerini içerir.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import CV, get_db
from schemas.cv import ATSScoreResponse, JobDescriptionInput
from services.ats_scorer import calculate_ats_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post("/{cv_id}", response_model=ATSScoreResponse)
async def analyze_cv(
    cv_id: int,
    db: Session = Depends(get_db),
) -> ATSScoreResponse:
    """CV'yi genel ATS kriterlerine göre skorlar.

    İş ilanı olmadan genel yazılım keyword listesi ile değerlendirir.
    Sonucu veritabanına kaydeder.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        db: Veritabanı oturumu.

    Returns:
        ATSScoreResponse: Detaylı ATS skor sonucu.

    Raises:
        HTTPException 404: CV bulunamazsa.
        HTTPException 500: Skorlama sırasında hata oluşursa.
    """
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if cv is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {cv_id} ile CV bulunamadı.",
            )

        if not cv.raw_text:
            raise HTTPException(
                status_code=400,
                detail="CV'de metin bulunamadı. Lütfen geçerli bir CV yükleyin.",
            )

        result = calculate_ats_score(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
        )

        # Sonuçları DB'ye kaydet
        cv.ats_score = result["total_score"]
        cv.last_analysis = result
        cv.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("CV (ID: %d) skorlandı: %d/100", cv_id, result["total_score"])

        return ATSScoreResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CV analizi sırasında hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV analizi sırasında beklenmeyen bir hata oluştu.",
        ) from e


@router.post("/{cv_id}/with-job", response_model=ATSScoreResponse)
async def analyze_cv_with_job(
    cv_id: int,
    body: JobDescriptionInput,
    db: Session = Depends(get_db),
) -> ATSScoreResponse:
    """CV'yi iş ilanı ile birlikte ATS kriterlerine göre skorlar.

    İş ilanından keyword çıkarır ve CV ile eşleştirir.
    Keyword eşleşme detaylarını da döndürür.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        body: İş ilanı metni.
        db: Veritabanı oturumu.

    Returns:
        ATSScoreResponse: Detaylı ATS skor sonucu (keyword eşleşme dahil).

    Raises:
        HTTPException 404: CV bulunamazsa.
        HTTPException 500: Skorlama sırasında hata oluşursa.
    """
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if cv is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {cv_id} ile CV bulunamadı.",
            )

        if not cv.raw_text:
            raise HTTPException(
                status_code=400,
                detail="CV'de metin bulunamadı. Lütfen geçerli bir CV yükleyin.",
            )

        result = calculate_ats_score(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            job_description=body.job_description,
        )

        # Sonuçları DB'ye kaydet
        cv.ats_score = result["total_score"]
        cv.last_analysis = result
        cv.job_description = body.job_description
        cv.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "CV (ID: %d) iş ilanı ile skorlandı: %d/100",
            cv_id, result["total_score"],
        )

        return ATSScoreResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "CV analizi (iş ilanı ile) sırasında hata oluştu: %s", str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="CV analizi sırasında beklenmeyen bir hata oluştu.",
        ) from e
