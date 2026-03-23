"""
CVilator Pydantic şemaları.

API request/response modellerini tanımlar.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CVUploadResponse(BaseModel):
    """CV yükleme yanıt modeli.

    CV başarıyla yüklenip parse edildikten sonra döndürülür.
    raw_text alanı maksimum 500 karakter olarak kısaltılır.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="CV kaydının benzersiz ID'si")
    filename: str = Field(..., description="Orijinal dosya adı")
    raw_text: Optional[str] = Field(
        None, description="Parse edilen ham metin (kısaltılmış, maks 500 karakter)"
    )
    sections: Optional[dict] = Field(
        None, description="Tespit edilen bölümler (dict)"
    )
    created_at: datetime = Field(..., description="Oluşturulma tarihi")


class CVListItem(BaseModel):
    """CV listesi öğe modeli.

    CV listeleme endpoint'inde her bir CV için döndürülür.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="CV kaydının benzersiz ID'si")
    filename: str = Field(..., description="Orijinal dosya adı")
    ats_score: Optional[int] = Field(
        None, description="ATS uyumluluk skoru (0-100)"
    )
    created_at: datetime = Field(..., description="Oluşturulma tarihi")


class CVDetail(BaseModel):
    """CV detay modeli.

    Tek bir CV'nin tüm alanlarını içerir.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="CV kaydının benzersiz ID'si")
    filename: str = Field(..., description="Orijinal dosya adı")
    file_path: str = Field(..., description="Kaydedilen dosya yolu")
    raw_text: Optional[str] = Field(None, description="Parse edilen ham metin")
    sections: Optional[dict] = Field(
        None, description="Tespit edilen bölümler (dict)"
    )
    ats_score: Optional[int] = Field(
        None, description="ATS uyumluluk skoru (0-100)"
    )
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    updated_at: datetime = Field(..., description="Son güncelleme tarihi")


# --- ATS Analiz Şemaları ---


class CriteriaDetail(BaseModel):
    """Tek bir skorlama kriterinin detay modeli."""

    name: str = Field(..., description="Kriter adı")
    score: int = Field(..., description="Alınan puan")
    max_score: int = Field(..., description="Maksimum puan")
    feedback: str = Field(..., description="Kullanıcıya yönelik geri bildirim")
    details: list[str] = Field(
        default_factory=list, description="Detaylı bulgular listesi"
    )


class KeywordMatch(BaseModel):
    """Keyword eşleşme detayları."""

    found: list[str] = Field(default_factory=list, description="Bulunan keyword'ler")
    missing: list[str] = Field(
        default_factory=list, description="Eksik keyword'ler"
    )
    match_rate: float = Field(0.0, description="Eşleşme oranı (0.0 - 1.0)")


class ATSScoreResponse(BaseModel):
    """ATS skorlama yanıt modeli."""

    total_score: int = Field(..., description="Toplam ATS skoru (0-100)")
    grade: str = Field(..., description="Derece (Mükemmel/Çok İyi/İyi/Orta/Zayıf)")
    criteria: list[CriteriaDetail] = Field(
        ..., description="Kriter bazlı skor detayları"
    )
    summary: str = Field(..., description="Genel özet ve öneriler")
    keyword_match: KeywordMatch = Field(
        ..., description="Keyword eşleşme detayları"
    )


class JobDescriptionInput(BaseModel):
    """İş ilanı girdi modeli."""

    job_description: str = Field(
        ..., min_length=10, description="İş ilanı metni"
    )


# --- AI Optimizasyon Şemaları ---


class RewrittenBullet(BaseModel):
    """Yeniden yazılmış bullet point."""

    original: str = Field(..., description="Orijinal bullet point")
    improved: str = Field(..., description="İyileştirilmiş versiyon")


class SectionFeedback(BaseModel):
    """Bölüm bazlı AI geri bildirimi."""

    section_name: str = Field(..., description="Bölüm adı")
    current_quality: str = Field(..., description="Mevcut kalite (iyi/orta/zayıf)")
    issues: list[str] = Field(default_factory=list, description="Tespit edilen sorunlar")
    suggestions: list[str] = Field(default_factory=list, description="İyileştirme önerileri")
    rewritten_bullets: list[RewrittenBullet] = Field(
        default_factory=list, description="Yeniden yazılmış bullet point'ler"
    )


class KeywordPlacement(BaseModel):
    """Keyword yerleştirme önerisi."""

    keyword: str = Field(..., description="Eksik keyword")
    suggestion: str = Field(..., description="Nereye, nasıl eklenmeli")


class AIFeedback(BaseModel):
    """Claude AI tarafından üretilen detaylı geri bildirim."""

    overall_assessment: str = Field(..., description="Genel değerlendirme")
    section_feedback: list[SectionFeedback] = Field(
        default_factory=list, description="Bölüm bazlı geri bildirim"
    )
    missing_keywords: list[str] = Field(
        default_factory=list, description="Eksik keyword'ler"
    )
    keyword_placement: list[KeywordPlacement] = Field(
        default_factory=list, description="Keyword yerleştirme önerileri"
    )
    action_items: list[str] = Field(
        default_factory=list, description="Öncelikli aksiyon öğeleri"
    )
    ats_tips: list[str] = Field(
        default_factory=list, description="ATS uyumluluk ipuçları"
    )


class OptimizationResponse(BaseModel):
    """Optimizasyon yanıt modeli (AI feedback + ATS skor birleşimi)."""

    cv_id: int = Field(..., description="CV kaydının ID'si")
    ats_score: ATSScoreResponse = Field(..., description="Kural tabanlı ATS skoru")
    ai_feedback: AIFeedback = Field(..., description="Claude AI geri bildirimi")
    optimization_count: int = Field(..., description="Toplam optimizasyon sayısı")


class ApplySuggestionsInput(BaseModel):
    """Uygulanacak önerilerin indeks listesi."""

    accepted_suggestions: list[int] = Field(
        ..., min_length=1, description="Kabul edilen öneri indeksleri"
    )


class OptimizedCVResponse(BaseModel):
    """Optimize edilmiş CV yanıt modeli."""

    cv_id: int = Field(..., description="CV kaydının ID'si")
    optimized_text: str = Field(..., description="Optimize edilmiş CV metni")
    optimized_sections: dict = Field(
        default_factory=dict, description="Optimize edilmiş bölümler"
    )
    changes_made: list[str] = Field(
        default_factory=list, description="Yapılan değişikliklerin listesi"
    )
