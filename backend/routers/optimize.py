"""
CVilator AI optimizasyon router'ı.

Claude API kullanarak CV analizi ve optimizasyon endpoint'lerini içerir.
PDF indirme endpoint'i de burada tanımlanmıştır.
"""

import logging
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
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
from services.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimize", tags=["Optimize"])


@router.post("/{cv_id}", response_model=OptimizationResponse)
async def optimize_cv(
    cv_id: int,
    body: Optional[JobDescriptionInput] = None,
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

        job_desc = body.job_description if body else ""

        # 1. Kural tabanlı ATS skorlaması
        ats_result = calculate_ats_score(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            job_description=job_desc,
        )

        # 2. Claude AI analizi
        ai_feedback = analyze_cv_with_ai(
            raw_text=cv.raw_text,
            sections=cv.sections or {},
            job_description=job_desc,
        )

        # 3. Optimizasyon sayacını artır
        cv.optimization_count = (cv.optimization_count or 0) + 1

        # 4. Sonuçları DB'ye kaydet
        cv.ats_score = ats_result["total_score"]
        cv.last_analysis = ats_result
        cv.job_description = job_desc or None
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
    except Exception as e:
        logger.exception("Öneri uygulama sırasında hata oluştu: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Öneri uygulama sırasında beklenmeyen bir hata oluştu.",
        ) from e


@router.get("/{cv_id}/download")
async def download_optimized_cv(
    cv_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Optimize edilmiş CV'yi PDF olarak indirir.

    Args:
        cv_id: CV kaydının benzersiz ID'si.
        db: Veritabanı oturumu.

    Returns:
        FileResponse: PDF dosyası.

    Raises:
        HTTPException 404: CV bulunamazsa.
        HTTPException 400: Optimize edilmiş metin yoksa.
        HTTPException 500: PDF oluşturulamazsa.
    """
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if cv is None:
        raise HTTPException(
            status_code=404,
            detail=f"ID {cv_id} ile CV bulunamadı.",
        )

    # Optimize edilmiş metin veya orijinal metin kullan
    text = cv.optimized_text or cv.raw_text
    if not text:
        raise HTTPException(
            status_code=400,
            detail="CV'de indirilebilir metin bulunamadı. Önce CV yükleyin ve analiz edin.",
        )

    try:
        # Geçici dosyaya PDF oluştur
        original_name = Path(cv.filename).stem
        # Türkçe ve özel karakterleri ASCII'ye çevir
        ascii_name = unicodedata.normalize("NFKD", original_name)
        ascii_name = ascii_name.encode("ascii", "ignore").decode("ascii")
        ascii_name = re.sub(r"[^\w\s-]", "", ascii_name).strip()
        ascii_name = re.sub(r"\s+", "_", ascii_name) or "cv"
        pdf_filename = f"CVilator_optimized_{ascii_name}.pdf"

        # uploads dizinine kaydet (temizlik için)
        output_dir = os.path.join(".", "uploads", "pdf")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"cv_{cv_id}_{pdf_filename}")

        generate_pdf(
            optimized_text=text,
            sections=cv.sections or {},
            output_path=output_path,
        )

        logger.info("PDF indirildi: CV ID %d -> %s", cv_id, pdf_filename)

        return FileResponse(
            path=output_path,
            filename=pdf_filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"',
            },
        )

    except Exception as e:
        logger.exception("PDF oluşturma hatası: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="PDF oluşturulurken bir hata oluştu.",
        ) from e
