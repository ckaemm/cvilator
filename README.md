# CVilator

**AI destekli CV analizi ve ATS optimizasyon platformu.**

CV'nizi yukleyin, ATS (Applicant Tracking System) uyumlulugunu analiz edin ve Claude AI ile optimize edilmis, profesyonel bir CV indirin.

![Dashboard](screenshots/dashboard.png)

## Ozellikler

- **ATS Skorlama** — 8 farkli kritere gore 100 uzerinden uyumluluk skoru
- **AI Optimizasyon** — Claude AI ile bolum bazli iyilestirme onerileri
- **Keyword Analizi** — Is ilanina ozel eksik anahtar kelime tespiti
- **PDF Indirme** — Optimize edilmis CV'yi ATS-uyumlu PDF olarak indirin
- **Diff Gorunumu** — Mevcut ve onerilen metni yan yana karsilastirin
- **Dashboard** — Tum CV'lerinizi tek ekrandan yonetin
- **Responsive** — Masaustu ve mobil uyumlu arayuz

## Teknolojiler

### Backend
- **Python 3.14** + **FastAPI** — REST API
- **SQLAlchemy** — ORM & SQLite veritabani
- **Anthropic Claude API** — AI analiz motoru
- **ReportLab** — PDF uretimi (Turkce karakter destekli)
- **pdfplumber / python-docx** — CV parse (PDF & DOCX)

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** — Utility-first styling, dark mode
- **Lucide React** — Ikon seti
- **SWR** — Data fetching

## Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 18+
- Anthropic API anahtari ([console.anthropic.com](https://console.anthropic.com))

### Backend

```bash
cd backend

# Sanal ortam olustur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bagimliliklari yukle
pip install -r requirements.txt

# Ortam degiskenleri
cp .env.example .env
# .env dosyasina ANTHROPIC_API_KEY degerini girin

# Sunucuyu baslat
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Bagimliliklari yukle
npm install

# Gelistirme sunucusu
npm run dev
```

Tarayicida [http://localhost:3000](http://localhost:3000) adresini acin.

## API Dokumantasyonu

Sunucu calisirken: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

### Endpointler

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `POST` | `/api/cv/upload` | CV yukle (PDF/DOCX) |
| `GET` | `/api/cv/list` | Tum CV'leri listele |
| `GET` | `/api/cv/{id}` | CV detayi getir |
| `DELETE` | `/api/cv/{id}` | CV sil |
| `POST` | `/api/analyze/{id}` | ATS analizi yap |
| `POST` | `/api/analyze/{id}/with-job` | Is ilanina ozel analiz |
| `POST` | `/api/optimize/{id}` | AI optimizasyon baslat |
| `POST` | `/api/optimize/{id}/apply` | Onerileri uygula |
| `GET` | `/api/optimize/{id}/download` | PDF olarak indir |

## Kullanim

1. **CV Yukle** — Dashboard veya Analiz sayfasindan PDF/DOCX dosyanizi yukleyin
2. **Analiz Et** — ATS skorunuzu gorun, kriter detaylarini inceleyin
3. **Is Ilani Ekle** (opsiyonel) — Hedef ilani yapistirarak ilana ozel analiz alin
4. **Optimize Et** — AI onerilerini inceleyin, kabul ettiklerinizi secin
5. **Indir** — Optimize edilmis CV'nizi PDF olarak indirin

## Proje Yapisi

```
cvilator/
├── backend/
│   ├── main.py              # FastAPI uygulama giris noktasi
│   ├── routers/             # API endpoint'leri
│   │   ├── cv.py            # CV CRUD islemleri
│   │   ├── analyze.py       # ATS skorlama
│   │   └── optimize.py      # AI optimizasyon + PDF indirme
│   ├── services/            # Is mantigi
│   │   ├── ats_scorer.py    # Kural tabanli ATS skorlama
│   │   ├── ai_engine.py     # Claude AI entegrasyonu
│   │   ├── pdf_parser.py    # PDF/DOCX parse
│   │   └── pdf_generator.py # PDF uretimi
│   ├── models/              # Veritabani modelleri
│   ├── schemas/             # Pydantic semalari
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js sayfalari
│   │   ├── page.tsx         # Dashboard
│   │   ├── analyze/         # Analiz sayfasi
│   │   └── optimize/[id]/   # Optimizasyon sayfasi
│   ├── components/          # React componentleri
│   │   ├── ui/              # Temel UI (Button, Card, Badge...)
│   │   ├── cv-upload.tsx    # Drag & drop yukleyici
│   │   ├── ats-score-card.tsx
│   │   ├── criteria-breakdown.tsx
│   │   ├── keyword-analysis.tsx
│   │   ├── section-feedback.tsx
│   │   └── optimized-preview.tsx
│   ├── lib/                 # API client & TypeScript tipleri
│   └── package.json
├── .gitignore
└── README.md
```

## Roadmap

- [ ] Kullanici kimlik dogrulama (auth)
- [ ] Coklu dil destegi (EN/TR)
- [ ] CV sablonlari
- [ ] Toplu CV analizi
- [ ] Analiz gecmisi grafikleri
- [ ] LinkedIn profil entegrasyonu
- [ ] CV karsilastirma (A/B test)

## Lisans

MIT

## Iletisim

[github.com/ckaemm](https://github.com/ckaemm)
