# Kişisel Muhasebe Sistemi

Telegram botu ve web paneli ile kişisel fiş/fatura takip sistemi.

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.12+
- Node.js 18+
- PostgreSQL 16+
- Tesseract OCR

### Kurulum

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker ile

```bash
docker-compose up -d
```

## 📱 Telegram Bot

1. [@BotFather](https://t.me/BotFather) ile bot oluşturun
2. Token'ı `.env` dosyasına ekleyin
3. Deploy sonrası webhook ayarlayın:
   ```
   GET /telegram/set-webhook?webhook_url=https://api.example.com/telegram/webhook
   ```

## 🌐 Deployment

### Backend (Render)
1. GitHub repo'yu Render'a bağlayın
2. Docker runtime seçin
3. PostgreSQL database oluşturun
4. Environment variables ekleyin

### Frontend (Vercel)
1. GitHub repo'yu Vercel'e import edin
2. Root directory: `frontend`
3. `NEXT_PUBLIC_API_URL` ekleyin

## 📁 Proje Yapısı

```
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # API endpoints
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # OCR, extraction, matching
│   └── alembic/              # DB migrations
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   └── lib/                  # API client
├── render.yaml               # Render config
└── docker-compose.yml        # Local dev
```

## 🔧 API Endpoints

| Endpoint | Açıklama |
|----------|----------|
| `POST /documents/upload` | Fiş/fatura yükle |
| `GET /documents/` | Belge listesi |
| `POST /documents/{id}/confirm` | Taslak onayla |
| `GET /vendors/` | Cari listesi |
| `GET /reports/summary` | Özet rapor |
| `POST /telegram/webhook` | Telegram webhook |

## 📄 Lisans

MIT
