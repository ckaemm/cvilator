"""
CVilator ATS skorlama motoru.

CV'leri 7 kriter üzerinden toplam 100 puan ile değerlendirir.
Saf fonksiyonlar olarak tasarlanmıştır, unit test edilebilir.
"""

import logging
import re
from typing import Optional

from services.keyword_extractor import extract_keywords

logger = logging.getLogger(__name__)

# Genel yazılım keyword listesi (job_description verilmezse kullanılır)
DEFAULT_KEYWORDS: list[str] = [
    "python", "javascript", "java", "sql", "git", "api", "docker", "aws",
    "agile", "react", "node.js", "linux", "ci/cd", "rest", "html", "css",
    "typescript", "postgresql", "mongodb", "kubernetes", "terraform",
    "microservices", "scrum", "jira", "testing",
]

# Güçlü eylem fiilleri (TR + EN)
ACTION_VERBS_TR: set[str] = {
    "geliştirdim", "geliştirdi", "geliştirme", "tasarladım", "tasarladı",
    "yönettim", "yönetti", "yönetim", "optimize ettim", "optimize etti",
    "oluşturdum", "oluşturdu", "oluşturma", "analiz ettim", "analiz etti",
    "entegre ettim", "entegre etti", "entegrasyon", "uyguladım", "uyguladı",
    "kurdum", "kurdu", "kurulum", "çözdüm", "çözdü", "çözüm",
    "otomatikleştirdim", "otomatikleştirdi", "otomasyon",
    "iyileştirdim", "iyileştirdi", "iyileştirme",
    "azalttım", "azalttı", "azaltma", "artırdım", "artırdı", "artırma",
    "dönüştürdüm", "dönüştürdü", "dönüştürme",
    "koordine ettim", "koordine etti", "liderlik ettim", "liderlik etti",
    "planladım", "planladı", "planlama", "raporladım", "raporladı",
    "test ettim", "test etti",
}

ACTION_VERBS_EN: set[str] = {
    "developed", "designed", "managed", "optimized", "created", "analyzed",
    "integrated", "implemented", "led", "built", "architected", "deployed",
    "established", "improved", "reduced", "increased", "delivered",
    "automated", "configured", "maintained", "migrated", "refactored",
    "resolved", "scaled", "streamlined", "coordinated", "mentored",
    "launched", "engineered", "transformed", "spearheaded", "pioneered",
    "orchestrated", "consolidated", "executed", "facilitated",
}


def _score_format(raw_text: str) -> dict:
    """Kriter 1 — Format Uyumu (15 puan).

    Satır uzunluğu, özel karakter yoğunluğu ve yapı tutarlılığını kontrol eder.

    Args:
        raw_text: CV'nin ham metni.

    Returns:
        dict: {"score": int, "max_score": 15, "feedback": str, "details": list}
    """
    score = 15
    details: list[str] = []

    if not raw_text:
        return {
            "score": 0, "max_score": 15,
            "feedback": "CV metni boş, format değerlendirilemedi.",
            "details": ["CV'de metin bulunamadı."],
        }

    lines = raw_text.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]

    # Satır uzunluğu kontrolü
    long_lines = [line for line in non_empty_lines if len(line) > 120]
    if long_lines:
        penalty = min(5, len(long_lines))
        score -= penalty
        details.append(
            f"{len(long_lines)} satır 120 karakterden uzun — kısa satırlar tercih edin."
        )
    else:
        details.append("Satır uzunlukları uygun.")

    # Özel karakter / tablo / emoji kontrolü
    special_chars = re.findall(r"[│┤┐└┴┬├─┼┘┌║╗╝╚╔╩╦╠═╬█▀▄■●▶◆★☆♦♣♠♥🔹🔸]", raw_text)
    if special_chars:
        penalty = min(5, len(special_chars) // 3)
        score -= penalty
        details.append(
            f"{len(special_chars)} özel karakter/tablo tespit edildi — düz metin tercih edin."
        )
    else:
        details.append("Özel karakter/tablo kullanılmamış.")

    # Emoji kontrolü
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF"
        r"\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF]"
    )
    emojis = emoji_pattern.findall(raw_text)
    if emojis:
        score -= min(3, len(emojis))
        details.append(
            f"{len(emojis)} emoji tespit edildi — ATS sistemleri emojiyi okuyamaz."
        )
    else:
        details.append("Emoji kullanılmamış.")

    # Çok kısa satır kontrolü (muhtemelen bozuk format)
    very_short = [line for line in non_empty_lines if 0 < len(line.strip()) < 3]
    if len(very_short) > 5:
        score -= 2
        details.append("Çok kısa satırlar fazla — format bozuk olabilir.")

    score = max(0, score)
    feedback = "Format uygun." if score >= 12 else "Format iyileştirilmeli."
    return {"score": score, "max_score": 15, "feedback": feedback, "details": details}


def _score_sections(sections: dict) -> dict:
    """Kriter 2 — Bölüm Tamlığı (15 puan).

    Zorunlu ve bonus bölümlerin varlığını kontrol eder.

    Args:
        sections: Tespit edilen bölümler dict'i.

    Returns:
        dict: {"score": int, "max_score": 15, "feedback": str, "details": list}
    """
    score = 0
    details: list[str] = []

    if not sections:
        return {
            "score": 0, "max_score": 15,
            "feedback": "Hiçbir bölüm tespit edilemedi. Bölüm başlıkları ekleyin.",
            "details": ["Bölüm başlıkları bulunamadı."],
        }

    # Zorunlu bölümler (her biri 3 puan)
    required = {"contact": "İletişim", "experience": "Deneyim",
                "education": "Eğitim", "skills": "Beceriler"}
    for key, name in required.items():
        if key in sections:
            score += 3
            details.append(f"'{name}' bölümü mevcut.")
        else:
            details.append(f"'{name}' bölümü eksik — eklenmeli.")

    # Bonus bölümler (her biri 1 puan)
    bonus = {"projects": "Projeler", "certifications": "Sertifikalar",
             "languages": "Diller"}
    for key, name in bonus.items():
        if key in sections:
            score += 1
            details.append(f"'{name}' bölümü mevcut (bonus).")

    score = min(15, score)
    feedback = (
        "Bölüm yapısı eksiksiz."
        if score >= 12
        else "Eksik bölümler var, eklenmesi önerilir."
    )
    return {"score": score, "max_score": 15, "feedback": feedback, "details": details}


def _score_keywords(
    raw_text: str, job_description: Optional[str] = None
) -> dict:
    """Kriter 3 — Keyword Eşleşme (25 puan).

    İş ilanı verilmişse ilandan keyword çıkarır, verilmemişse genel listeyi kullanır.

    Args:
        raw_text: CV'nin ham metni.
        job_description: İş ilanı metni (opsiyonel).

    Returns:
        dict: {"score": int, "max_score": 25, "feedback": str, "details": list,
               "keyword_match": {"found": list, "missing": list, "match_rate": float}}
    """
    if not raw_text:
        return {
            "score": 0, "max_score": 25,
            "feedback": "CV metni boş, keyword eşleşme yapılamadı.",
            "details": [],
            "keyword_match": {"found": [], "missing": [], "match_rate": 0.0},
        }

    # İş ilanı yoksa keyword analizi yapma
    if not job_description or not job_description.strip():
        return {
            "score": None, "max_score": 25,
            "feedback": "İş ilanı girilmediğinden keyword analizi yapılmadı.",
            "details": ["Keyword analizi için iş ilanı metni girin."],
            "keyword_match": {"found": [], "missing": [], "match_rate": 0.0},
        }

    keywords = extract_keywords(job_description)
    keywords = keywords[:25]

    if not keywords:
        return {
            "score": None, "max_score": 25,
            "feedback": "İş ilanından keyword çıkarılamadı.",
            "details": ["Yeterli keyword bulunamadı."],
            "keyword_match": {"found": [], "missing": [], "match_rate": 0.0},
        }

    raw_lower = raw_text.lower()
    found: list[str] = []
    missing: list[str] = []

    for kw in keywords:
        pattern = rf"\b{re.escape(kw.lower())}\b"
        if re.search(pattern, raw_lower):
            found.append(kw)
        else:
            missing.append(kw)

    match_rate = len(found) / len(keywords) if keywords else 0.0
    score = round(match_rate * 25)

    details: list[str] = [
        f"Toplam {len(keywords)} keyword kontrol edildi.",
        f"Bulunan: {len(found)}, Eksik: {len(missing)}",
    ]
    if found:
        details.append(f"Eşleşen keyword'ler: {', '.join(found[:10])}")
    if missing:
        details.append(f"Eksik keyword'ler: {', '.join(missing[:10])}")

    feedback = (
        "Keyword eşleşmesi güçlü."
        if match_rate >= 0.6
        else "Keyword eşleşmesini artırın — CV'ye ilgili terimleri ekleyin."
    )

    return {
        "score": score, "max_score": 25, "feedback": feedback,
        "details": details,
        "keyword_match": {
            "found": found, "missing": missing, "match_rate": round(match_rate, 2),
        },
    }


def _score_action_verbs(sections: dict) -> dict:
    """Kriter 4 — Eylem Fiilleri (10 puan).

    Deneyim bölümünde güçlü eylem fiillerinin varlığını kontrol eder.

    Args:
        sections: Tespit edilen bölümler dict'i.

    Returns:
        dict: {"score": int, "max_score": 10, "feedback": str, "details": list}
    """
    experience_text = sections.get("experience", "") if sections else ""

    if not experience_text:
        return {
            "score": 0, "max_score": 10,
            "feedback": "Deneyim bölümü bulunamadı, eylem fiilleri değerlendirilemedi.",
            "details": ["Deneyim bölümü eksik."],
        }

    text_lower = experience_text.lower()
    all_verbs = ACTION_VERBS_TR | ACTION_VERBS_EN

    found_verbs: list[str] = []
    for verb in all_verbs:
        if verb in text_lower:
            found_verbs.append(verb)

    verb_count = len(found_verbs)
    details: list[str] = []

    if verb_count >= 8:
        score = 10
    elif verb_count >= 5:
        score = 8
    elif verb_count >= 3:
        score = 6
    elif verb_count >= 1:
        score = 4
    else:
        score = 0

    if found_verbs:
        details.append(f"{verb_count} eylem fiili tespit edildi: {', '.join(found_verbs[:8])}")
    else:
        details.append("Hiç güçlü eylem fiili bulunamadı.")

    details.append(
        "İpucu: 'geliştirdim', 'optimize ettim', 'implemented', 'designed' "
        "gibi fiiller kullanın."
        if verb_count < 5
        else "Eylem fiili kullanımı yeterli."
    )

    feedback = (
        "Eylem fiili kullanımı güçlü."
        if score >= 8
        else "Daha fazla güçlü eylem fiili kullanın."
    )
    return {"score": score, "max_score": 10, "feedback": feedback, "details": details}


def _score_measurable(raw_text: str) -> dict:
    """Kriter 5 — Ölçülebilir Başarılar (15 puan).

    Rakam içeren ifadeleri (%, x, kişi, proje vb.) arar.

    Args:
        raw_text: CV'nin ham metni.

    Returns:
        dict: {"score": int, "max_score": 15, "feedback": str, "details": list}
    """
    if not raw_text:
        return {
            "score": 0, "max_score": 15,
            "feedback": "CV metni boş, ölçülebilir başarılar değerlendirilemedi.",
            "details": [],
        }

    patterns = [
        r"%\s*\d+", r"\d+\s*%",                       # yüzde
        r"\d+\s*x\b", r"\d+\s*kat\b",                 # çarpan
        r"\d+\s*kişi", r"\d+\s*people", r"\d+\s*team", # ekip büyüklüğü
        r"\d+\s*proje", r"\d+\s*project",              # proje sayısı
        r"\$\s*\d+", r"\d+\s*TL", r"€\s*\d+",         # para birimi
        r"\d+\s*milyon", r"\d+\s*million",             # büyüklük
        r"\d+\s*bin\b", r"\d+k\b",                     # binler
        r"\d+\s*kullanıcı", r"\d+\s*user",             # kullanıcı sayısı
        r"\d+\s*müşteri", r"\d+\s*client",             # müşteri sayısı
    ]

    found_metrics: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        found_metrics.extend(matches)

    # Genel rakam ifadeleri (tarih hariç)
    general_numbers = re.findall(
        r"(?<!\d[/.\-])\b\d{2,}\b(?![/.\-]\d)", raw_text
    )
    # Yıl benzeri sayıları filtrele
    general_numbers = [
        n for n in general_numbers
        if not (1900 <= int(n) <= 2100)
    ]

    metric_count = len(found_metrics)
    details: list[str] = []

    if metric_count >= 3:
        score = 15
        details.append(f"{metric_count} ölçülebilir başarı tespit edildi — harika!")
    elif metric_count == 2:
        score = 10
        details.append(f"{metric_count} ölçülebilir başarı tespit edildi — 1 tane daha ekleyin.")
    elif metric_count == 1:
        score = 5
        details.append(f"{metric_count} ölçülebilir başarı tespit edildi — en az 3 hedefleyin.")
    else:
        score = 0
        details.append("Ölçülebilir başarı bulunamadı.")

    if found_metrics:
        details.append(f"Bulunan ifadeler: {', '.join(found_metrics[:5])}")

    details.append(
        "İpucu: '%30 performans artışı', '5 kişilik ekip', '10+ proje' "
        "gibi somut rakamlar ekleyin."
        if metric_count < 3
        else "Ölçülebilir başarılar yeterli düzeyde."
    )

    feedback = (
        "Ölçülebilir başarılar yeterli."
        if score >= 10
        else "Somut rakamlar ve ölçülebilir başarılar ekleyin."
    )
    return {"score": score, "max_score": 15, "feedback": feedback, "details": details}


def _score_length(raw_text: str, sections: dict) -> dict:
    """Kriter 6 — Uzunluk & Yoğunluk (10 puan).

    Kelime sayısı ve bölüm başına dağılım dengesini kontrol eder.

    Args:
        raw_text: CV'nin ham metni.
        sections: Tespit edilen bölümler dict'i.

    Returns:
        dict: {"score": int, "max_score": 10, "feedback": str, "details": list}
    """
    if not raw_text:
        return {
            "score": 0, "max_score": 10,
            "feedback": "CV metni boş.",
            "details": ["CV'de metin bulunamadı."],
        }

    words = raw_text.split()
    word_count = len(words)
    details: list[str] = [f"Toplam kelime sayısı: {word_count}"]

    # Kelime sayısı değerlendirmesi
    if 300 <= word_count <= 800:
        score = 7
        details.append("Kelime sayısı optimal aralıkta (300-800).")
    elif 200 <= word_count < 300 or 800 < word_count <= 1200:
        score = 5
        if word_count < 300:
            details.append("CV biraz kısa — daha fazla detay eklemeyi düşünün.")
        else:
            details.append("CV biraz uzun — gereksiz detayları kısaltın.")
    elif word_count < 200:
        score = 2
        details.append("CV çok kısa — önemli bilgiler eksik olabilir.")
    else:
        score = 2
        details.append("CV çok uzun (1200+ kelime) — özetlemeye çalışın.")

    # Bölüm dağılımı kontrolü
    if sections and len(sections) >= 2:
        section_lengths = {k: len(v.split()) for k, v in sections.items()}
        avg_length = sum(section_lengths.values()) / len(section_lengths)

        imbalanced = [
            k for k, v in section_lengths.items()
            if v > avg_length * 3 or v < avg_length * 0.2
        ]

        if not imbalanced:
            score += 3
            details.append("Bölümler arası kelime dağılımı dengeli.")
        else:
            score += 1
            details.append(
                f"Dengesiz bölümler: {', '.join(imbalanced)} — dağılımı dengeleyin."
            )
    else:
        score += 1
        details.append("Bölüm dağılımı değerlendirilemedi (yetersiz bölüm).")

    score = min(10, max(0, score))
    feedback = (
        "Uzunluk ve yoğunluk uygun."
        if score >= 7
        else "CV uzunluğu veya bölüm dağılımı iyileştirilmeli."
    )
    return {"score": score, "max_score": 10, "feedback": feedback, "details": details}


def _score_consistency(raw_text: str, sections: dict) -> dict:
    """Kriter 7 — Hata & Tutarlılık (10 puan).

    Tarih formatı tutarlılığı, kelime tekrarı ve iletişim bilgisi formatını kontrol eder.

    Args:
        raw_text: CV'nin ham metni.
        sections: Tespit edilen bölümler dict'i.

    Returns:
        dict: {"score": int, "max_score": 10, "feedback": str, "details": list}
    """
    if not raw_text:
        return {
            "score": 0, "max_score": 10,
            "feedback": "CV metni boş.",
            "details": [],
        }

    score = 10
    details: list[str] = []

    # Tarih formatı tutarlılığı
    date_patterns = {
        "MM/YYYY": re.findall(r"\b\d{2}/\d{4}\b", raw_text),
        "YYYY-MM": re.findall(r"\b\d{4}-\d{2}\b", raw_text),
        "Ay YYYY": re.findall(
            r"\b(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|"
            r"Eylül|Ekim|Kasım|Aralık|January|February|March|April|May|"
            r"June|July|August|September|October|November|December)\s+\d{4}\b",
            raw_text, re.IGNORECASE,
        ),
        "YYYY": re.findall(r"\b(?:19|20)\d{2}\b", raw_text),
    }

    formats_used = [fmt for fmt, matches in date_patterns.items() if matches]
    # YYYY tek başına her zaman bulunabilir, diğerleriyle çakışmasın
    specific_formats = [f for f in formats_used if f != "YYYY"]

    if len(specific_formats) > 1:
        score -= 3
        details.append(
            f"Farklı tarih formatları kullanılmış ({', '.join(specific_formats)}) — "
            "tek format tercih edin."
        )
    else:
        details.append("Tarih formatları tutarlı.")

    # Tekrarlayan fiil kontrolü
    experience_text = sections.get("experience", "") if sections else ""
    if experience_text:
        exp_words = re.findall(r"\b[a-zA-ZçğıöşüÇĞİÖŞÜ]+\b", experience_text.lower())
        word_freq = {}
        check_verbs = ACTION_VERBS_TR | ACTION_VERBS_EN
        for word in exp_words:
            if word in check_verbs:
                word_freq[word] = word_freq.get(word, 0) + 1

        repeated = {w: c for w, c in word_freq.items() if c >= 3}
        if repeated:
            score -= 2
            repeated_str = ", ".join(f"'{w}' ({c}x)" for w, c in repeated.items())
            details.append(f"Tekrarlayan fiiller: {repeated_str} — çeşitlendirin.")
        else:
            details.append("Fiil çeşitliliği yeterli.")

    # E-posta formatı kontrolü
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text)
    if emails:
        details.append(f"E-posta tespit edildi: {emails[0]}")
    else:
        score -= 2
        details.append("Geçerli e-posta adresi bulunamadı — eklenmeli.")

    # Telefon formatı kontrolü
    phones = re.findall(
        r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{2,4}", raw_text
    )
    if phones:
        details.append("Telefon numarası tespit edildi.")
    else:
        score -= 1
        details.append("Telefon numarası bulunamadı — eklenmesi önerilir.")

    score = max(0, score)
    feedback = (
        "Tutarlılık ve format iyi."
        if score >= 7
        else "Tutarlılık sorunları tespit edildi."
    )
    return {"score": score, "max_score": 10, "feedback": feedback, "details": details}


def _calculate_grade(total_score: int) -> str:
    """Toplam skora göre harf derecesi belirler.

    Args:
        total_score: Toplam ATS skoru (0-100).

    Returns:
        str: Derece metni.
    """
    if total_score >= 90:
        return "Mükemmel"
    elif total_score >= 75:
        return "Çok İyi"
    elif total_score >= 60:
        return "İyi"
    elif total_score >= 40:
        return "Orta"
    else:
        return "Zayıf"


def _generate_summary(total_score: int, criteria_results: list[dict]) -> str:
    """Skor ve kriter sonuçlarına göre genel özet oluşturur.

    Args:
        total_score: Toplam ATS skoru.
        criteria_results: Kriter sonuçları listesi.

    Returns:
        str: Türkçe özet metni.
    """
    weak_criteria = [
        c["name"] for c in criteria_results
        if c["score"] < c["max_score"] * 0.5
    ]
    strong_criteria = [
        c["name"] for c in criteria_results
        if c["score"] >= c["max_score"] * 0.8
    ]

    parts: list[str] = []

    if total_score >= 75:
        parts.append("CV'niz ATS sistemleri için genel olarak iyi durumda.")
    elif total_score >= 50:
        parts.append("CV'nizde iyileştirme gerektiren alanlar var.")
    else:
        parts.append("CV'niz ATS sistemleri için önemli iyileştirmeler gerektiriyor.")

    if strong_criteria:
        parts.append(f"Güçlü yönler: {', '.join(strong_criteria)}.")

    if weak_criteria:
        parts.append(f"İyileştirilmesi gereken alanlar: {', '.join(weak_criteria)}.")

    return " ".join(parts)


def calculate_ats_score(
    raw_text: str,
    sections: dict,
    job_description: Optional[str] = None,
) -> dict:
    """CV için ATS uyumluluk skoru hesaplar.

    7 kriter üzerinden toplam 100 puan hesaplar.
    Her kriter bağımsız olarak değerlendirilir.

    Args:
        raw_text: CV'nin ham metni.
        sections: Tespit edilen bölümler dict'i.
        job_description: İş ilanı metni (opsiyonel).

    Returns:
        dict: Toplam skor, derece, kriter detayları, özet ve keyword eşleşmesi.
    """
    logger.info("ATS skoru hesaplanıyor...")

    sections = sections or {}

    # 7 kriteri hesapla
    format_result = _score_format(raw_text)
    section_result = _score_sections(sections)
    keyword_result = _score_keywords(raw_text, job_description)
    verb_result = _score_action_verbs(sections)
    measurable_result = _score_measurable(raw_text)
    length_result = _score_length(raw_text, sections)
    consistency_result = _score_consistency(raw_text, sections)

    # Keyword atlandı mı?
    keyword_skipped = keyword_result["score"] is None

    keyword_criteria = {
        "name": "Keyword Eşleşme",
        "score": keyword_result["score"] if not keyword_skipped else 0,
        "max_score": keyword_result["max_score"],
        "feedback": keyword_result["feedback"],
        "details": keyword_result["details"],
    }

    # Kriter listesi oluştur
    criteria = [
        {"name": "Format Uyumu", **format_result},
        {"name": "Bölüm Tamlığı", **section_result},
        keyword_criteria,
        {"name": "Eylem Fiilleri", **verb_result},
        {"name": "Ölçülebilir Başarılar", **measurable_result},
        {"name": "Uzunluk & Yoğunluk", **length_result},
        {"name": "Hata & Tutarlılık", **consistency_result},
    ]

    if keyword_skipped:
        # Keyword hariç kalan 75 puan üzerinden 100'e ölçekle
        other_score = sum(
            c["score"] for c in criteria if c["name"] != "Keyword Eşleşme"
        )
        total_score = round(other_score / 75 * 100)
    else:
        total_score = sum(c["score"] for c in criteria)

    total_score = min(100, max(0, total_score))

    grade = _calculate_grade(total_score)
    summary = _generate_summary(total_score, criteria)

    result = {
        "total_score": total_score,
        "grade": grade,
        "criteria": criteria,
        "summary": summary,
        "keyword_match": keyword_result["keyword_match"],
    }

    logger.info(
        "ATS skoru hesaplandı: %d/100 (%s)", total_score, grade
    )

    return result
