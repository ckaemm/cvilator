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
