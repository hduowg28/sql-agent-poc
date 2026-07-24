from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings


# ---------------------------------------------------------------------------
# Singleton Engine
# ---------------------------------------------------------------------------
# Engine được tạo một lần duy nhất, tái sử dụng connection pool trong suốt
# vòng đời ứng dụng. Mọi module chỉ import `engine` từ đây.
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=settings.db_pool_pre_ping,
    echo=settings.debug,   # Log SQL khi debug=True
)

# ---------------------------------------------------------------------------
# SessionLocal Factory
# ---------------------------------------------------------------------------
# autocommit=False  → Phải gọi commit() thủ công
# autoflush=False   → Không tự flush khi query, kiểm soát tốt hơn
# bind=engine       → Gắn session với engine đã tạo
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Dependency: get_db
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency cung cấp database session theo từng request.

    Dùng với Depends:
        @router.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...

    Session được đóng tự động sau khi request kết thúc (kể cả khi có lỗi).
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health-check helper (dùng khi khởi động ứng dụng)
# ---------------------------------------------------------------------------
def verify_db_connection() -> None:
    """
    Kiểm tra kết nối database khi ứng dụng khởi động.
    Raise exception nếu không kết nối được để fail-fast thay vì chạy ngầm lỗi.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB] Kết nối database thành công.")
    except Exception as exc:
        print(f"[DB] Không thể kết nối database: {exc}")
        raise