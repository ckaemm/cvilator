"""
CVilator AI motoru.

Groq API kullanarak CV analizi ve optimizasyonu yapar.
"""

import json
import logging
import os
from typing import Any, Optional

from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

MODEL_ID: str = "llama-3.3-70b-versatile"
MAX_TOKENS: int = 4096


def _get_client() -> Groq:
    """Groq istemcisi oluşturur."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            "GROQ_API_KEY ayarlanmamış. "
            "Lütfen .env dosyasına console.groq.com'dan aldığınız API anahtarını ekleyin."
        )
    return Groq(api_key=api_key)


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


def _call_groq_api(system_prompt: str, user_message: str) -> str:
    """Groq API'ye istek gönderir ve yanıtı döndürür."""
    client = _get_client()
    logger.info("Groq API'ye istek gönderiliyor (model: %s)...", MODEL_ID)
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.3,
    )
    logger.info(
        "Groq API yanıtı alındı. Token: input=%d, output=%d",
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )
    return response.choices[0].message.content


def _parse_json_response(response_text: str) -> dict[str, Any]:
    """Yanıttan JSON ayrıştırır."""
    text = response_text.strip()
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
        raise ValueError(f"Yanıt geçerli JSON formatında değil: {str(e)}") from e


def analyze_cv_with_ai(
    raw_text: str,
    sections: dict[str, Any],
    job_description: Optional[str] = None,
) -> dict[str, Any]:
    """CV'yi Groq AI ile analiz eder."""
    user_parts: list[str] = []
    user_parts.append("## CV Metni:\n")
    user_parts.append(raw_text[:8000])

    if sections:
        user_parts.append("\n\n## Tespit Edilen Bölümler:\n")
        for section_name, content in sections.items():
            content_str = content if isinstance(content, str) else str(content)
            user_parts.append(f"### {section_name}:\n{content_str[:1500]}\n")

    if job_description:
        user_parts.append("\n\n## Hedef İş İlanı:\n")
        user_parts.append(job_description[:3000])

    response_text = _call_groq_api(ANALYSIS_SYSTEM_PROMPT, "".join(user_parts))
    result = _parse_json_response(response_text)

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
    """Kabul edilen önerileri uygulayarak optimize edilmiş CV üretir."""
    accepted_items: list[str] = []
    suggestion_index = 0

    for section_fb in feedback.get("section_feedback", []):
        for suggestion in section_fb.get("suggestions", []):
            if suggestion_index in accepted_suggestions:
                accepted_items.append(f"[{section_fb.get('section_name', 'Bilinmeyen')}] {suggestion}")
            suggestion_index += 1
        for bullet in section_fb.get("rewritten_bullets", []):
            if suggestion_index in accepted_suggestions:
                accepted_items.append(f"Bullet değişikliği: '{bullet.get('original', '')}' -> '{bullet.get('improved', '')}'")
            suggestion_index += 1

    for kp in feedback.get("keyword_placement", []):
        if suggestion_index in accepted_suggestions:
            accepted_items.append(f"Keyword ekle: {kp.get('keyword', '')} - {kp.get('suggestion', '')}")
        suggestion_index += 1

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

    response_text = _call_groq_api(OPTIMIZATION_SYSTEM_PROMPT, "".join(user_parts))
    result = _parse_json_response(response_text)

    defaults: dict[str, Any] = {
        "optimized_text": raw_text,
        "optimized_sections": sections or {},
        "changes_made": [],
    }
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value

    logger.info("CV optimizasyonu tamamlandı. Değişiklik sayısı: %d", len(result["changes_made"]))
    return result
