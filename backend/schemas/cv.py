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
