"""
CVilator veritabanı modelleri ve bağlantı yapılandırması.

SQLAlchemy ORM ile SQLite veritabanı yönetimi.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cvilator.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class CV(Base):
    """CV tablosu modeli.

    Yüklenen CV dosyalarının metadata, ham metin ve
    ayrıştırılmış bölüm bilgilerini tutar.
    """

    __tablename__ = "cvs"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: str = Column(String(255), nullable=False)
    file_path: str = Column(String(500), nullable=False)
    raw_text: str = Column(Text, nullable=True)
    sections: dict = Column(JSON, nullable=True)
    ats_score: int = Column(Integer, nullable=True)
    last_analysis: dict = Column(JSON, nullable=True)
    job_description: str = Column(Text, nullable=True)
    created_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CV(id={self.id}, filename='{self.filename}')>"


def create_tables() -> None:
    """Veritabanı tablolarını oluşturur."""
    logger.info("Veritabanı tabloları oluşturuluyor...")
    Base.metadata.create_all(bind=engine)
    logger.info("Veritabanı tabloları başarıyla oluşturuldu.")


def get_db() -> Generator[Session, None, None]:
    """Veritabanı oturumu dependency fonksiyonu.

    FastAPI dependency injection ile kullanılır.
    Her istek için yeni bir oturum oluşturur ve
    istek tamamlandığında oturumu kapatır.

    Yields:
        Session: SQLAlchemy veritabanı oturumu.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
