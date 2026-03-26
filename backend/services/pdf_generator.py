"""
CVilator PDF üretici.

Optimize edilmiş CV metninden ATS-friendly PDF oluşturur.
Türkçe karakter desteği için DejaVu Sans fontu kullanır.
"""

import logging
import os
import re

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)

# Türkçe karakter desteği için font kaydı
_registered_font_name: str | None = None


def _register_fonts() -> str:
    """Türkçe destekli fontları kaydeder. Kullanılabilir font adını döndürür."""
    global _registered_font_name
    if _registered_font_name is not None:
        return _registered_font_name

    # DejaVu Sans genellikle Linux'ta, Windows'ta da yüklenebilir
    font_paths = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # Windows
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "DejaVuSans.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "DejaVuSans-Bold.ttf"),
        # Bundled fallback - proje dizininde
        os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf"),
        os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans-Bold.ttf"),
    ]

    regular_path = None
    bold_path = None
    for p in font_paths:
        if os.path.exists(p):
            if "Bold" in p:
                bold_path = p
            else:
                regular_path = p

    if regular_path:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))
            if bold_path:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
            _registered_font_name = "DejaVuSans"
            logger.info("DejaVu Sans fontları kaydedildi: %s", regular_path)
            return _registered_font_name
        except Exception as e:
            logger.warning("DejaVu Sans kaydedilemedi: %s", e)

    # Windows Arial fallback - Türkçe karakterleri destekler
    arial_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf")
    arial_bold = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")
    if os.path.exists(arial_path):
        try:
            pdfmetrics.registerFont(TTFont("ArialTR", arial_path))
            if os.path.exists(arial_bold):
                pdfmetrics.registerFont(TTFont("ArialTR-Bold", arial_bold))
            _registered_font_name = "ArialTR"
            logger.info("Arial fontları kaydedildi (fallback)")
            return _registered_font_name
        except Exception as e:
            logger.warning("Arial kaydedilemedi: %s", e)

    # Son çare: Helvetica (Türkçe sınırlı ama ATS uyumlu)
    logger.warning("TTFont bulunamadı, Helvetica kullanılacak (Türkçe sınırlı)")
    _registered_font_name = "Helvetica"
    return _registered_font_name


def _build_styles(font_name: str) -> dict:
    """PDF için stil tanımları oluşturur."""
    bold_font = f"{font_name}-Bold" if font_name != "Helvetica" else "Helvetica-Bold"

    # Bold font kayıtlı mı kontrol et
    try:
        pdfmetrics.getFont(bold_font)
    except KeyError:
        bold_font = font_name

    line_height = 14

    styles = {
        "name": ParagraphStyle(
            "CVName",
            fontName=bold_font,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=HexColor("#1a1a1a"),
        ),
        "contact": ParagraphStyle(
            "CVContact",
            fontName=font_name,
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=HexColor("#555555"),
        ),
        "section_title": ParagraphStyle(
            "CVSection",
            fontName=bold_font,
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor=HexColor("#1a1a1a"),
        ),
        "body": ParagraphStyle(
            "CVBody",
            fontName=font_name,
            fontSize=10.5,
            leading=10.5 * 1.15,
            spaceAfter=3,
            textColor=HexColor("#2a2a2a"),
        ),
        "bullet": ParagraphStyle(
            "CVBullet",
            fontName=font_name,
            fontSize=10.5,
            leading=10.5 * 1.15,
            leftIndent=12,
            spaceAfter=2,
            bulletIndent=0,
            textColor=HexColor("#2a2a2a"),
        ),
    }
    return styles


def _escape_xml(text: str) -> str:
    """ReportLab Paragraph için XML-unsafe karakterleri escape eder."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _parse_sections(text: str) -> list[dict]:
    """
    CV metnini bölümlere ayırır.

    Çeşitli bölüm başlığı formatlarını tanır:
    - Tamamen büyük harfli satırlar (İŞ DENEYİMİ)
    - "Başlık:" formatı
    """
    lines = text.strip().split("\n")
    sections = []
    current_section = {"title": "", "lines": []}

    # İlk satırlar genellikle isim ve iletişim
    header_lines = []
    body_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not body_started and current_section["lines"]:
                current_section["lines"].append("")
            elif body_started:
                current_section["lines"].append("")
            continue

        # Bölüm başlığı mı?
        is_section_header = False

        # Büyük harfli başlık (en az 3 karakter, harf ağırlıklı)
        alpha_chars = [c for c in stripped if c.isalpha()]
        if (
            len(alpha_chars) >= 3
            and stripped.upper() == stripped
            and any(c.isalpha() for c in stripped)
            and not stripped.startswith("•")
            and not stripped.startswith("-")
        ):
            is_section_header = True

        # "Başlık:" formatı (satırın tamamı başlık gibi kısa ve : ile biten)
        if not is_section_header and stripped.endswith(":") and len(stripped) < 40:
            is_section_header = True

        if is_section_header:
            body_started = True
            if current_section["title"] or current_section["lines"]:
                sections.append(current_section)
            current_section = {"title": stripped.rstrip(":"), "lines": []}
        elif not body_started:
            # Header kısmı (isim, iletişim)
            header_lines.append(stripped)
        else:
            current_section["lines"].append(stripped)

    # Son bölümü ekle
    if current_section["title"] or current_section["lines"]:
        sections.append(current_section)

    return header_lines, sections


def generate_pdf(optimized_text: str, sections: dict, output_path: str) -> str:
    """
    Optimize edilmiş CV metninden ATS-friendly PDF üretir.

    Args:
        optimized_text: Optimize edilmiş düz metin.
        sections: Bölüm bazlı içerik (dict).
        output_path: PDF dosyasının kaydedileceği yol.

    Returns:
        Oluşturulan PDF dosyasının yolu.
    """
    font_name = _register_fonts()
    styles = _build_styles(font_name)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    story = []

    # Bölümler dict'ten mi yoksa metin parse mı?
    if sections and len(sections) > 1:
        # Dict-based sections kullan
        _build_from_sections(story, sections, styles)
    elif optimized_text:
        # Metni parse et
        _build_from_text(story, optimized_text, styles)
    else:
        story.append(Paragraph("CV içeriği bulunamadı.", styles["body"]))

    doc.build(story)
    logger.info("PDF oluşturuldu: %s", output_path)
    return output_path


def _draw_separator(story, styles):
    """Bölümler arası ince çizgi ayırıcı ekler."""
    from reportlab.platypus import HRFlowable
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=HexColor("#cccccc"),
            spaceBefore=4,
            spaceAfter=4,
        )
    )


def _build_from_sections(story, sections: dict, styles: dict):
    """Dict tipindeki bölümlerden PDF içeriği oluşturur."""
    first = True
    for section_name, content in sections.items():
        if not content:
            continue

        # İlk bölüm öncesi ayırıcı ekleme
        if not first:
            _draw_separator(story, styles)
        first = False

        # Bölüm başlığı
        title = _escape_xml(section_name.upper())
        story.append(Paragraph(title, styles["section_title"]))

        # İçerik satırları
        lines = content.split("\n") if isinstance(content, str) else [str(content)]
        for line in lines:
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 4))
                continue

            escaped = _escape_xml(stripped)

            # Bullet point kontrolü
            if stripped.startswith(("•", "-", "*", "–")):
                bullet_text = stripped.lstrip("•-*– ").strip()
                escaped_bullet = _escape_xml(bullet_text)
                story.append(
                    Paragraph(f"•  {escaped_bullet}", styles["bullet"])
                )
            else:
                story.append(Paragraph(escaped, styles["body"]))


def _build_from_text(story, text: str, styles: dict):
    """Düz metinden PDF içeriği oluşturur."""
    header_lines, sections = _parse_sections(text)

    # Header (isim + iletişim)
    if header_lines:
        # İlk satır genellikle isim
        name = _escape_xml(header_lines[0])
        story.append(Paragraph(name, styles["name"]))

        if len(header_lines) > 1:
            contact = _escape_xml(" | ".join(header_lines[1:]))
            story.append(Paragraph(contact, styles["contact"]))

        story.append(Spacer(1, 6))

    # Bölümler
    for i, section in enumerate(sections):
        if i > 0:
            _draw_separator(story, styles)

        if section["title"]:
            title = _escape_xml(section["title"].upper())
            story.append(Paragraph(title, styles["section_title"]))

        for line in section["lines"]:
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 4))
                continue

            escaped = _escape_xml(stripped)

            if stripped.startswith(("•", "-", "*", "–")):
                bullet_text = stripped.lstrip("•-*– ").strip()
                escaped_bullet = _escape_xml(bullet_text)
                story.append(
                    Paragraph(f"•  {escaped_bullet}", styles["bullet"])
                )
            else:
                story.append(Paragraph(escaped, styles["body"]))
