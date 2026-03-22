# CVilator

ATS CV Optimization Platform

## Kurulum

### Backend

```bash
cd backend

# Sanal ortam oluştur
python -m venv venv

# Sanal ortamı aktifleştir
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Bağımlılıkları kur
pip install -r requirements.txt

# .env dosyasını oluştur
cp .env.example .env

# Sunucuyu başlat
uvicorn main:app --reload --port 8000
```

### API Dokümantasyonu

Sunucu çalıştıktan sonra:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/cv/upload` | CV dosyası yükle (PDF/DOCX) |
| GET | `/api/cv/list` | Tüm CV'leri listele |
| GET | `/api/cv/{id}` | CV detayını görüntüle |
| DELETE | `/api/cv/{id}` | CV'yi sil |
