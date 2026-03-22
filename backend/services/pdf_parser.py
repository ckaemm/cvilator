"""
CVilator PDF ve DOCX dosya ayrıştırma servisi.

CV dosyalarından metin çıkarma ve bölüm tespit etme işlemlerini yürütür.
Türkçe ve İngilizce bölüm başlıklarını destekler.
"""

import logging
import re
from typing import Optional

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

# Bölüm başlıkları eşleştirme haritası (Türkçe ve İngilizce)
SECTION_HEADERS: dict[str, list[str]] = {
    "contact": [
        r"iletişim",
        r"contact",
        r"kişisel\s*bilgiler",
        r"personal\s*info(?:rmation)?",
    ],
    "experience": [
        r"deneyim",
        r"experience",
        r"iş\s*deneyimi",
        r"work\s*experience",
        r"professional\s*experience",
        r"mesleki\s*deneyim",
    ],
    "education": [
        r"eğitim",
        r"education",
        r"öğrenim",
        r"akademik\s*geçmiş",
    ],
    "skills": [
        r"beceriler",
        r"skills",
        r"yetenekler",
        r"teknik\s*beceriler",
        r"technical\s*skills",
        r"yetkinlikler",
        r"competencies",
    ],
    "projects": [
        r"projeler",
        r"projects",
        r"kişisel\s*projeler",
        r"personal\s*projects",
    ],
    "certifications": [
        r"sertifikalar",
        r"certifications",
        r"certificates",
        r"lisanslar",
        r"licenses",
    ],
    "languages": [
        r"diller",
        r"languages",
        r"yabancı\s*dil(?:ler)?",
        r"foreign\s*languages",
    ],
    "references": [
        r"referanslar",
        r"references",
        r"kaynaklar",
    ],
}


def _build_section_pattern() -> re.Pattern:
    """Tüm bölüm başlıklarını tek bir regex pattern'ine derler.

    Returns:
        re.Pattern: Derlenen regex pattern.
    """
    all_patterns: list[str] = []
    for patterns in SECTION_HEADERS.values():
        all_patterns.extend(patterns)

    combined = "|".join(all_patterns)
    return re.compile(
        rf"^\s*(?P<header>{combined})\s*:?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


def _identify_section(header_text: str) -> Optional[str]:
    """Bir başlık metninin hangi bölüme ait olduğunu belirler.

    Args:
        header_text: Tespit edilen başlık metni.

    Returns:
        Optional[str]: Bölüm anahtarı (ör. "experience") veya None.
    """
    header_text = header_text.strip().lower()
    for section_key, patterns in SECTION_HEADERS.items():
        for pattern in patterns:
            if re.match(rf"^{pattern}$", header_text, re.IGNORECASE):
                return section_key
    return None


def _detect_sections(text: str) -> dict[str, str]:
    """Metinden bölümleri tespit eder ve ayırır.

    Metin içindeki bölüm başlıklarını bulur ve her bölümün
    içeriğini ayrıştırır.

    Args:
        text: Ayrıştırılacak ham metin.

    Returns:
        dict[str, str]: Bölüm anahtarı -> bölüm içeriği eşleştirmesi.
    """
    sections: dict[str, str] = {}
    pattern = _build_section_pattern()

    matches = list(pattern.finditer(text))

    if not matches:
        logger.info("Metin içinde bölüm başlığı tespit edilemedi.")
        return sections

    for i, match in enumerate(matches):
        header_text = match.group("header")
        section_key = _identify_section(header_text)

        if section_key is None:
            continue

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        content = text[start:end].strip()

        if content:
            sections[section_key] = content

    logger.info("Tespit edilen bölümler: %s", list(sections.keys()))
    return sections


def parse_pdf(file_path: str) -> dict[str, object]:
    """PDF dosyasından metin çıkarır ve bölümleri tespit eder.

    pdfplumber kütüphanesi kullanarak PDF dosyasını okur,
    tüm sayfalardan metin çıkarır ve bölüm tespiti yapar.

    Args:
        file_path: PDF dosyasının tam yolu.

    Returns:
        dict: {"raw_text": str, "sections": dict} formatında sonuç.

    Raises:
        FileNotFoundError: Dosya bulunamazsa.
        Exception: PDF okuma hatası oluşursa.
    """
    logger.info("PDF dosyası parse ediliyor: %s", file_path)

    raw_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"
                logger.debug("Sayfa %d: %d karakter çıkarıldı.", page_num, len(page_text))
            else:
                logger.warning("Sayfa %d: Metin çıkarılamadı.", page_num)

    raw_text = raw_text.strip()

    if not raw_text:
        logger.warning("PDF dosyasından hiç metin çıkarılamadı: %s", file_path)
        return {"raw_text": "", "sections": {}}

    sections = _detect_sections(raw_text)

    logger.info(
        "PDF parse tamamlandı. %d karakter, %d bölüm tespit edildi.",
        len(raw_text),
        len(sections),
    )

    return {"raw_text": raw_text, "sections": sections}


def parse_docx(file_path: str) -> dict[str, object]:
    """DOCX dosyasından metin çıkarır ve bölümleri tespit eder.

    python-docx kütüphanesi kullanarak DOCX dosyasını okur,
    tüm paragraflardan metin çıkarır ve bölüm tespiti yapar.

    Args:
        file_path: DOCX dosyasının tam yolu.

    Returns:
        dict: {"raw_text": str, "sections": dict} formatında sonuç.

    Raises:
        FileNotFoundError: Dosya bulunamazsa.
        Exception: DOCX okuma hatası oluşursa.
    """
    logger.info("DOCX dosyası parse ediliyor: %s", file_path)

    doc = Document(file_path)
    paragraphs: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    raw_text = "\n".join(paragraphs).strip()

    if not raw_text:
        logger.warning("DOCX dosyasından hiç metin çıkarılamadı: %s", file_path)
        return {"raw_text": "", "sections": {}}

    sections = _detect_sections(raw_text)

    logger.info(
        "DOCX parse tamamlandı. %d karakter, %d bölüm tespit edildi.",
        len(raw_text),
        len(sections),
    )

    return {"raw_text": raw_text, "sections": sections}
