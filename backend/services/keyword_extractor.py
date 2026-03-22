"""
CVilator keyword çıkarma servisi.

İş ilanlarından teknik keyword'leri çıkarır.
Basit TF-IDF benzeri ağırlıklandırma ile en önemli terimleri belirler.
"""

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Türkçe ve İngilizce stop word'ler
STOP_WORDS: set[str] = {
    # Türkçe
    "bir", "ve", "ile", "için", "bu", "da", "de", "den", "dan", "ya", "ye",
    "olan", "olarak", "gibi", "kadar", "daha", "en", "her", "çok", "az",
    "iyi", "kötü", "büyük", "küçük", "yeni", "eski", "aynı", "diğer",
    "arası", "üzerinde", "altında", "içinde", "dışında", "sonra", "önce",
    "şekilde", "olup", "olmak", "etmek", "yapmak", "sahip", "yer", "alan",
    "ilgili", "gerekli", "tercihen", "aranan", "şartlar", "nitelikler",
    "olması", "edilmesi", "yapılması", "bilgisi", "deneyimi", "yetkinliği",
    "minimum", "maksimum", "yıl", "yılı", "pozisyon", "kadro", "iş",
    # İngilizce
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "must",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "above", "after", "again", "all", "also", "any",
    "because", "before", "between", "both", "each", "few", "more", "most",
    "other", "some", "such", "that", "this", "those", "through", "under",
    "until", "what", "when", "where", "which", "while", "who", "whom",
    "why", "how", "its", "our", "your", "their", "we", "you", "they",
    "experience", "work", "working", "required", "preferred", "ability",
    "strong", "good", "excellent", "knowledge", "understanding", "years",
    "year", "position", "role", "job", "team", "company",
}

# Bilinen teknik terimler (doğrudan eşleşme için)
KNOWN_TECH_TERMS: set[str] = {
    "python", "javascript", "typescript", "java", "c#", "c++", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "react", "angular", "vue", "vue.js", "next.js", "nuxt.js", "svelte",
    "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
    "asp.net", ".net", "rails", "laravel",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "sqlite", "oracle", "cassandra", "dynamodb",
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform",
    "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci",
    "git", "linux", "unix", "bash", "powershell",
    "rest", "restful", "graphql", "grpc", "api", "microservices", "websocket",
    "html", "css", "sass", "tailwind", "bootstrap",
    "machine learning", "deep learning", "nlp", "ai", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn",
    "agile", "scrum", "kanban", "jira", "confluence",
    "figma", "sketch", "adobe xd",
    "rabbitmq", "kafka", "celery",
    "nginx", "apache", "iis",
    "oauth", "jwt", "ssl", "tls",
    "tableau", "power bi", "excel",
    "hadoop", "spark", "airflow", "etl",
    "selenium", "cypress", "jest", "pytest", "unittest",
    "swagger", "postman", "insomnia",
}


def _normalize_text(text: str) -> str:
    """Metni küçük harfe çevirir ve gereksiz boşlukları temizler.

    Args:
        text: Ham metin.

    Returns:
        str: Normalize edilmiş metin.
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_ngrams(words: list[str], n: int) -> list[str]:
    """Kelime listesinden n-gram'lar oluşturur.

    Args:
        words: Kelime listesi.
        n: N-gram boyutu (1, 2 veya 3).

    Returns:
        list[str]: N-gram listesi.
    """
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def extract_keywords(job_description: str) -> list[str]:
    """İş ilanından teknik keyword'leri çıkarır.

    Stop word'leri filtreler, TF-IDF benzeri ağırlıklandırma yapar
    ve en önemli terimleri döndürür.

    Args:
        job_description: İş ilanı metni.

    Returns:
        list[str]: Öncelik sırasına göre sıralanmış keyword listesi.
    """
    if not job_description or not job_description.strip():
        logger.warning("Boş iş ilanı metni, keyword çıkarılamadı.")
        return []

    normalized = _normalize_text(job_description)

    # Bilinen teknik terimleri doğrudan bul
    found_known: list[str] = []
    for term in KNOWN_TECH_TERMS:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, normalized, re.IGNORECASE):
            found_known.append(term)

    # Metni kelimelere ayır
    words = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ#+.]+", normalized)
    words = [w for w in words if len(w) >= 2 and w not in STOP_WORDS]

    # 1-gram, 2-gram ve 3-gram oluştur
    all_candidates: list[str] = []
    all_candidates.extend(words)
    all_candidates.extend(_extract_ngrams(words, 2))
    all_candidates.extend(_extract_ngrams(words, 3))

    # Stop word içeren n-gram'ları filtrele
    filtered: list[str] = []
    for candidate in all_candidates:
        candidate_words = candidate.split()
        if any(w in STOP_WORDS for w in candidate_words):
            continue
        if len(candidate) < 2:
            continue
        filtered.append(candidate)

    # Frekans sayımı (TF benzeri ağırlıklandırma)
    freq = Counter(filtered)

    # Bilinen teknik terimler daha yüksek ağırlık alsın
    for term in found_known:
        freq[term] = freq.get(term, 0) + 5

    # Frekansa göre sırala, tekil terimleri döndür
    sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    # Tekrar eden terimleri kaldır ve sonuç listesini oluştur
    seen: set[str] = set()
    result: list[str] = []
    for term, _ in sorted_terms:
        lower_term = term.lower()
        if lower_term not in seen:
            seen.add(lower_term)
            result.append(term)

    logger.info(
        "İş ilanından %d keyword çıkarıldı. İlk 10: %s",
        len(result),
        result[:10],
    )

    return result
