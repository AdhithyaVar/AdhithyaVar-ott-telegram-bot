from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from .config import settings

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    series_id = Column(String, index=True)
    episode_number = Column(Integer)
    source_url = Column(String)
    processed = Column(Boolean, default=False)
    published_message_id = Column(Integer, nullable=True)
    meta = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("series_id", "episode_number", name="uq_series_episode"),)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    job_type = Column(String)
    status = Column(String, default="pending")  # pending|running|error|done
    payload = Column(JSON, default={})
    result = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    provider = Column(String, index=True)
    user_id = Column(String)
    password_enc = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("provider", "user_id", name="uq_provider_user"),
        Index("ix_accounts_provider_user", "provider", "user_id"),
    )

class SiteCredential(Base):
    __tablename__ = "site_credentials"
    id = Column(Integer, primary_key=True)
    domain = Column(String, index=True)
    user_id = Column(String)
    password_enc = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("domain", "user_id", name="uq_domain_user"),
        Index("ix_sitecred_domain_user", "domain", "user_id"),
    )

# New: explicit allowlist for yt-dlp usage
class YtDlpAllowedDomain(Base):
    __tablename__ = "ytdlp_allowed_domains"
    id = Column(Integer, primary_key=True)
    domain = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()