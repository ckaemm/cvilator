"""
CVilator AI motoru.

Claude API kullanarak CV analizi ve optimizasyonu yapar.
Anthropic Python SDK ile entegre edilmiştir.
"""

import json
import logging
import os
import time
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Yapılandırma sabitleri
MODEL_ID: str = "claude-sonnet-4-5"
MAX_TOKENS: int = 4096
TIMEOUT_SECONDS: int = 30
MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 1.0

# API anahtarı kontrolü
ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")


def _get_client() -> anthropic.Anthropic:
    """Anthropic istemcisi oluşturur.

    Returns:
        anthropic.Anthropic: Yapılandırılmış API istemcisi.

    Raises:
        ValueError: API anahtarı ayarlanmamışsa.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            "ANTHROPIC_API_KEY ayarlanmamış. "
            "Lütfen .env dosyasına geçerli bir API anahtarı ekleyin."
        )
    return anthropic.Anthropic(
        api_key=api_key,
        timeout=TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )


# --- Sistem Promptları ---

ANALYSIS_SYSTEM_PROMPT: str = """Sen bir ATS (Applicant Tracking System) CV uzmanısın.
Verilen CV metnini ve bölümlerini analiz edip detaylı geri bildirim üreteceksin.

Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:
{
  "overall_assessment": "Genel değerlendirme metni (2-3 cümle)",
  "section_feedback": [
    {
      "section_name": "Bölüm adı",
      "current_quality": "iyi|orta|zayıf",
      "issues": ["Tespit edilen sorun 1", "Sorun 2"],
      "suggestions": ["İyileştirme önerisi 1", "Öneri 2"],
      "rewritten_bullets": [
        {
          "original": "Orijinal bullet point",
          "improved": "İyileştirilmiş versiyon"
        }
      ]
    }
  ],
  "missing_keywords": ["Eksik keyword 1", "Eksik keyword 2"],
  "keyword_placement": [
    {
      "keyword": "Eksik keyword",
      "suggestion": "Nereye ve nasıl eklenmeli"
    }
  ],
  "action_items": ["Öncelikli aksiyon 1", "Aksiyon 2"],
  "ats_tips": ["ATS uyumluluk ipucu 1", "İpucu 2"]
}

Kurallar:
1. Her bölüm için en az 1 öneri ver.
2. Bullet point'leri güçlü eylem fiilleri ile yeniden yaz.
3. Ölçülebilir başarıları vurgula (sayılar, yüzdeler).
4. ATS anahtar kelime optimizasyonu öner.
5. Yanıt DİLİ: CV'nin dili ne ise o dilde yanıt ver (Türkçe CV ise Türkçe, İngilizce CV ise İngilizce).
6. SADECE JSON formatında yanıt ver, markdown veya açıklama ekleme."""

OPTIMIZATION_SYSTEM_PROMPT: str = """Sen bir CV optimizasyon uzmanısın.
Verilen CV metnini, geri bildirimleri ve kabul edilen önerileri kullanarak
optimize edilmiş bir CV metni üreteceksin.

Yanıtını SADECE aşağıdaki JSON formatında ver:
{
  "optimized_text": "Optimize edilmiş tam CV metni",
  "optimized_sections": {
    "bölüm_adı": "Optimize edilmiş bölüm içeriği"
  },
  "changes_made": ["Yapılan değişiklik 1", "Değişiklik 2"]
}

Kurallar:
1. Sadece kabul edilen önerileri uygula.
2. CV'nin genel yapısını ve formatını koru.
3. Güçlü eylem fiilleri kullan.
4. Ölçülebilir başarıları ekle veya iyileştir.
5. ATS uyumluluğunu artır.
6. Yanıt DİLİ: CV'nin dili ne ise o dilde yanıt ver.
7. SADECE JSON formatında yanıt ver."""


def _call_claude_api(
    system_prompt: str,
    user_message: str,
) -> str:
    """Claude API'ye istek gönderir ve yanıtı döndürür.

    SDK'nın yerleşik retry mekanizmasını kullanır (429 ve 5xx hatalarını
    otomatik olarak exponential backoff ile yeniden dener).

    Args:
        system_prompt: Sistem promptu.
        user_message: Kullanıcı mesajı.

    Returns:
        str: Claude'un yanıt metni.

    Raises:
        ValueError: API anahtarı ayarlanmamışsa.
        anthropic.APIError: API hatası oluşursa.
    """
    client = _get_client()

    logger.info("Claude API'ye istek gönderiliyor (model: %s)...", MODEL_ID)

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # Yanıt metnini çıkar
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    logger.info(
        "Claude API yanıtı alındı. Token kullanımı: input=%d, output=%d",
        response.usage.input_tokens,
        response.usage.output_tokens,
    )

    return text_content


def _parse_json_response(response_text: str) -> dict[str, Any]:
    """Claude yanıtından JSON ayrıştırır.

    Yanıt bazen markdown code block içinde gelebilir,
    bu durumda temizleme yapılır.

    Args:
        response_text: Claude'dan gelen ham yanıt metni.

    Returns:
        dict: Ayrıştırılmış JSON verisi.

    Raises:
        ValueError: JSON ayrıştırma başarısız olursa.
    """
    text = response_text.strip()

    # Markdown code block temizleme
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("JSON ayrıştırma hatası: %s", str(e))
        logger.debug("Ham yanıt: %s", response_text[:500])
        raise ValueError(
            f"Claude yanıtı geçerli JSON formatında değil: {str(e)}"
        ) from e


def analyze_cv_with_ai(
    raw_text: str,
    sections: dict[str, Any],
    job_description: Optional[str] = None,
) -> dict[str, Any]:
    """CV'yi Claude AI ile analiz eder ve detaylı geri bildirim üretir.

    Args:
        raw_text: CV'nin ham metni.
        sections: Ayrıştırılmış bölümler sözlüğü.
        job_description: İş ilanı metni (opsiyonel).

    Returns:
        dict: AIFeedback şemasına uygun geri bildirim verisi.
            Anahtarlar: overall_assessment, section_feedback,
            missing_keywords, keyword_placement, action_items, ats_tips.

    Raises:
        ValueError: API anahtarı yoksa veya yanıt ayrıştırılamıyorsa.
        anthropic.APIError: API hatası oluşursa.
    """
    # Kullanıcı mesajını oluştur
    user_parts: list[str] = []
    user_parts.append("## CV Metni:\n")
    user_parts.append(raw_text[:8000])  # Token limiti için kısalt

    if sections:
        user_parts.append("\n\n## Tespit Edilen Bölümler:\n")
        for section_name, content in sections.items():
            content_str = content if isinstance(content, str) else str(content)
            user_parts.append(f"### {section_name}:\n{content_str[:1500]}\n")

    if job_description:
        user_parts.append("\n\n## Hedef İş İlanı:\n")
        user_parts.append(job_description[:3000])

    user_message = "".join(user_parts)

    # Claude API çağrısı
    response_text = _call_claude_api(ANALYSIS_SYSTEM_PROMPT, user_message)

    # JSON ayrıştırma
    result = _parse_json_response(response_text)

    # Varsayılan alanları garantile
    defaults: dict[str, Any] = {
        "overall_assessment": "",
        "section_feedback": [],
        "missing_keywords": [],
        "keyword_placement": [],
        "action_items": [],
        "ats_tips": [],
    }

    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value

    logger.info("AI analizi tamamlandı. Bölüm sayısı: %d", len(result["section_feedback"]))

    return result


def generate_optimized_cv(
    raw_text: str,
    sections: dict[str, Any],
    feedback: dict[str, Any],
    accepted_suggestions: list[int],
) -> dict[str, Any]:
    """Kabul edilen önerileri uygulayarak optimize edilmiş CV üretir.

    Args:
        raw_text: CV'nin orijinal ham metni.
        sections: Ayrıştırılmış bölümler sözlüğü.
        feedback: AI tarafından üretilen geri bildirim (AIFeedback formatı).
        accepted_suggestions: Kabul edilen öneri indeksleri.

    Returns:
        dict: OptimizedCVResponse şemasına uygun veri.
            Anahtarlar: optimized_text, optimized_sections, changes_made.

    Raises:
        ValueError: API anahtarı yoksa veya yanıt ayrıştırılamıyorsa.
        anthropic.APIError: API hatası oluşursa.
    """
    # Kabul edilen önerileri derle
    accepted_items: list[str] = []

    # section_feedback'ten önerileri topla
    suggestion_index = 0
    for section_fb in feedback.get("section_feedback", []):
        for suggestion in section_fb.get("suggestions", []):
            if suggestion_index in accepted_suggestions:
                accepted_items.append(
                    f"[{section_fb.get('section_name', 'Bilinmeyen')}] {suggestion}"
                )
            suggestion_index += 1

        for bullet in section_fb.get("rewritten_bullets", []):
            if suggestion_index in accepted_suggestions:
                original = bullet.get("original", "")
                improved = bullet.get("improved", "")
                accepted_items.append(
                    f"Bullet değişikliği: '{original}' -> '{improved}'"
                )
            suggestion_index += 1

    # keyword_placement önerilerini ekle
    for kp in feedback.get("keyword_placement", []):
        if suggestion_index in accepted_suggestions:
            accepted_items.append(
                f"Keyword ekle: {kp.get('keyword', '')} - {kp.get('suggestion', '')}"
            )
        suggestion_index += 1

    # action_items ekle
    for item in feedback.get("action_items", []):
        if suggestion_index in accepted_suggestions:
            accepted_items.append(f"Aksiyon: {item}")
        suggestion_index += 1

    if not accepted_items:
        return {
            "optimized_text": raw_text,
            "optimized_sections": sections or {},
            "changes_made": ["Hiçbir öneri kabul edilmedi, değişiklik yapılmadı."],
        }

    # Kullanıcı mesajını oluştur
    user_parts: list[str] = []
    user_parts.append("## Orijinal CV Metni:\n")
    user_parts.append(raw_text[:8000])

    if sections:
        user_parts.append("\n\n## Mevcut Bölümler:\n")
        for section_name, content in sections.items():
            content_str = content if isinstance(content, str) else str(content)
            user_parts.append(f"### {section_name}:\n{content_str[:1500]}\n")

    user_parts.append("\n\n## Uygulanacak Değişiklikler:\n")
    for i, item in enumerate(accepted_items, 1):
        user_parts.append(f"{i}. {item}\n")

    user_message = "".join(user_parts)

    # Claude API çağrısı
    response_text = _call_claude_api(OPTIMIZATION_SYSTEM_PROMPT, user_message)

    # JSON ayrıştırma
    result = _parse_json_response(response_text)

    # Varsayılan alanları garantile
    defaults: dict[str, Any] = {
        "optimized_text": raw_text,
        "optimized_sections": sections or {},
        "changes_made": [],
    }

    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value

    logger.info(
        "CV optimizasyonu tamamlandı. Yapılan değişiklik sayısı: %d",
        len(result["changes_made"]),
    )

    return result
