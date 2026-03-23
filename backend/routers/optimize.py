"""
CVilator AI optimizasyon router'ı.

Claude API kullanarak CV analizi ve optimizasyon endpoint'lerini içerir.
"""

import logging
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import CV, get_db
from schemas.cv import (
    ApplySuggestionsInput,
    JobDescriptionInput,
    OptimizationResponse,
    OptimizedCVResponse,
)
from services.ai_engine import analyze_cv_with_ai, generate_optimized_cv
from services.ats_scorer import calculate_ats_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimize", tags=["Optimize"])


@router.post("/{cv_id}", response_model=OptimizationResponse)
async def optimize_cv(
    cv_id: int,
    body: JobDescriptionInput,
    db: Session = Depends(get_db),
) -> OptimizationResponse:
    """CV'yi AI ile analiz eder ve optimizasyon önerileri sunar.

    Kural tabanlı ATS skorlaması ve Claude AI geri bildirimini
    birleştirerek kapsamlı bir optimizasyon raporu döndürür.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        body: İş ilanı metni.
        db: Veritabanı oturumu.

    Returns:
        OptimizationResponse: ATS skoru + AI geri bildirimi.

    Raises:
        HTTPException 404: CV bulunamazsa.
        HTTPException 400: CV'de metin yoksa.
        HTTPException 503: Claude API erişilemezse.
        HTTPException 500: Beklenmeyen hata oluşursa.
    """
    try:
        # CV'yi getir
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

        # 1. Kural tabanlı ATS skorlaması
        ats_result = calculate_ats_score(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            job_description=body.job_description,
        )

        # 2. Claude AI analizi
        ai_feedback = analyze_cv_with_ai(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            job_description=body.job_description,
        )

        # 3. Optimizasyon sayacını artır
        cv.optimization_count = (cv.optimization_count or 0) + 1

        # 4. Sonuçları DB'ye kaydet
        cv.ats_score = ats_result["total_score"]
        cv.last_analysis = ats_result
        cv.job_description = body.job_description
        cv.ai_feedback = ai_feedback
        cv.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "CV (ID: %d) optimize edildi. ATS: %d/100, Optimizasyon #%d",
            cv_id,
            ats_result["total_score"],
            cv.optimization_count,
        )

        return OptimizationResponse(
            cv_id=cv_id,
            ats_score=ats_result,
            ai_feedback=ai_feedback,
            optimization_count=cv.optimization_count,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Yapılandırma hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e
    except anthropic.BadRequestError as e:
        logger.error("Claude API bad request hatası: %s", str(e))
        error_msg = str(e)
        if "credit balance" in error_msg.lower():
            detail = "Anthropic hesabında yeterli kredi yok. Lütfen Plans & Billing sayfasından kredi yükleyin."
        else:
            detail = f"Claude API istek hatası: {error_msg}"
        raise HTTPException(status_code=402, detail=detail) from e
    except anthropic.AuthenticationError as e:
        logger.error("Claude API kimlik doğrulama hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API anahtarı geçersiz. Lütfen .env dosyasını kontrol edin.",
        ) from e
    except anthropic.RateLimitError as e:
        logger.error("Claude API rate limit hatası: %s", str(e))
        raise HTTPException(
            status_code=429,
            detail="Claude API istek limiti aşıldı. Lütfen birkaç dakika bekleyin.",
        ) from e
    except anthropic.APIStatusError as e:
        logger.error("Claude API hatası (status %d): %s", e.status_code, str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API geçici olarak kullanılamıyor. Lütfen tekrar deneyin.",
        ) from e
    except anthropic.APIConnectionError as e:
        logger.error("Claude API bağlantı hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API'ye bağlanılamadı. İnternet bağlantınızı kontrol edin.",
        ) from e
    except Exception as e:
        logger.exception("CV optimizasyonu sırasında hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="CV optimizasyonu sırasında beklenmeyen bir hata oluştu.",
        ) from e


@router.post("/{cv_id}/apply", response_model=OptimizedCVResponse)
async def apply_suggestions(
    cv_id: int,
    body: ApplySuggestionsInput,
    db: Session = Depends(get_db),
) -> OptimizedCVResponse:
    """Kabul edilen AI önerilerini CV'ye uygular.

    Daha önce optimize endpoint'i ile üretilen geri bildirimdeki
    önerilerden seçilenleri uygulayarak optimize edilmiş CV üretir.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        body: Kabul edilen öneri indeksleri.
        db: Veritabanı oturumu.

    Returns:
        OptimizedCVResponse: Optimize edilmiş CV metni ve değişiklik listesi.

    Raises:
        HTTPException 404: CV bulunamazsa.
        HTTPException 400: AI geri bildirimi yoksa.
        HTTPException 503: Claude API erişilemezse.
        HTTPException 500: Beklenmeyen hata oluşursa.
    """
    try:
        # CV'yi getir
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if cv is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {cv_id} ile CV bulunamadı.",
            )

        if not cv.raw_text:
            raise HTTPException(
                status_code=400,
                detail="CV'de metin bulunamadı.",
            )

        if not cv.ai_feedback:
            raise HTTPException(
                status_code=400,
                detail="Önce /optimize endpoint'i ile AI analizi yapılmalı.",
            )

        # Optimize edilmiş CV üret
        result = generate_optimized_cv(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            feedback=cv.ai_feedback,
            accepted_suggestions=body.accepted_suggestions,
        )

        # Sonuçları DB'ye kaydet
        cv.optimized_text = result["optimized_text"]
        cv.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "CV (ID: %d) önerileri uygulandı. Değişiklik sayısı: %d",
            cv_id,
            len(result["changes_made"]),
        )

        return OptimizedCVResponse(
            cv_id=cv_id,
            optimized_text=result["optimized_text"],
            optimized_sections=result["optimized_sections"],
            changes_made=result["changes_made"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Yapılandırma hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e
    except anthropic.AuthenticationError as e:
        logger.error("Claude API kimlik doğrulama hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API anahtarı geçersiz. Lütfen .env dosyasını kontrol edin.",
        ) from e
    except anthropic.RateLimitError as e:
        logger.error("Claude API rate limit hatası: %s", str(e))
        raise HTTPException(
            status_code=429,
            detail="Claude API istek limiti aşıldı. Lütfen birkaç dakika bekleyin.",
        ) from e
    except anthropic.APIStatusError as e:
        logger.error("Claude API hatası (status %d): %s", e.status_code, str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API geçici olarak kullanılamıyor. Lütfen tekrar deneyin.",
        ) from e
    except anthropic.APIConnectionError as e:
        logger.error("Claude API bağlantı hatası: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="Claude API'ye bağlanılamadı. İnternet bağlantınızı kontrol edin.",
        ) from e
    except Exception as e:
        logger.exception("Öneri uygulama sırasında hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Öneri uygulama sırasında beklenmeyen bir hata oluştu.",
        ) from e
