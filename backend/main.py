"""
CVilator API - ATS CV Optimizasyon Platformu.

Ana uygulama modülü. FastAPI uygulamasını yapılandırır,
middleware'leri ekler ve router'ları bağlar.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import create_tables
from routers.analyze import router as analyze_router
from routers.cv import router as cv_router

# .env dosyasını yükle
load_dotenv()

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Uygulama yaşam döngüsü yöneticisi.

    Uygulama başlatıldığında veritabanı tablolarını oluşturur
    ve uploads klasörünü hazırlar.

    Args:
        app: FastAPI uygulama örneği.
    """
    # Startup
    logger.info("CVilator API başlatılıyor...")

    # Veritabanı tablolarını oluştur
    create_tables()

    # uploads/ klasörünü oluştur (yoksa)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.info("Upload dizini hazır: %s", UPLOAD_DIR)

    logger.info("CVilator API başarıyla başlatıldı.")
    yield
    # Shutdown
    logger.info("CVilator API kapatılıyor...")


app = FastAPI(
    title="CVilator API",
    version="0.1.0",
    description="ATS CV Optimizasyon Platformu API'si",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(cv_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """API kök endpoint'i. Sağlık kontrolü için kullanılabilir.

    Returns:
        dict: API bilgileri.
    """
    return {
        "name": "CVilator API",
        "version": "0.1.0",
        "status": "running",
    }
