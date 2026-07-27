"""
app/core/db_uploader.py
~~~~~~~~~~~~~~~~~~~~~~~
ETL Pipeline: Đọc CSV → Transform → Load vào database thông qua ORM.

Thay thế phương thức df.to_sql() bằng SQLAlchemy bulk_insert_mappings
để tương thích hoàn toàn với ORM models và Connection Pool.

Cách chạy:
    python -m app.core.db_uploader
"""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.core.exceptions import DatabaseUploadError
from app.models.base import Base
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CSV_PATH = Path("data/Sample - Superstore.csv")
BATCH_SIZE = 500   # Số bản ghi insert mỗi lần (tránh quá tải bộ nhớ)


def extract(csv_path: Path) -> pd.DataFrame:
    """Đọc file CSV và chuẩn hóa tên cột."""
    logger.info(f"[Extract] Đọc file: {csv_path}")
    df = pd.read_csv(csv_path, encoding="latin1")
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.lower()
    )
    logger.info(f"[Extract] Đọc thành công. Tổng số dòng: {len(df)}, cột: {list(df.columns)}")
    return df



def transform(df: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Tách DataFrame thô thành 3 tập dữ liệu chuẩn hóa.

    Returns:
        (customers, products, orders) – danh sách dict sẵn sàng để insert.
    """
    logger.info("[Transform] Bắt đầu transform dữ liệu...")

    # --- Customers ---
    customers_df = df[[
        "customer_id", "customer_name", "segment",
        "country", "city", "state", "postal_code", "region",
    ]].drop_duplicates(subset=["customer_id"]).copy()

    # --- Products ---
    products_df = df[[
        "product_id", "category", "sub_category", "product_name",
    ]].drop_duplicates(subset=["product_id"]).copy()

    # --- Orders ---
    orders_df = df[[
        "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "product_id", "sales", "quantity", "discount", "profit",
    ]].copy()
    orders_df["order_date"] = pd.to_datetime(orders_df["order_date"], dayfirst=False, errors="coerce")
    orders_df["ship_date"] = pd.to_datetime(orders_df["ship_date"], dayfirst=False, errors="coerce")
    # Đặt lại index để row_id tự sinh qua autoincrement
    orders_df = orders_df.reset_index(drop=True)

    customers = customers_df.where(customers_df.notna(), None).to_dict(orient="records")
    products = products_df.where(products_df.notna(), None).to_dict(orient="records")
    orders = orders_df.where(orders_df.notna(), None).to_dict(orient="records")

    logger.info(
        f"[Transform] Hoàn tất: {len(customers)} customers, "
        f"{len(products)} products, {len(orders)} orders."
    )
    return customers, products, orders

def _bulk_load(session: Session, model, records: list[dict], table_name: str) -> None:
    """
    Insert danh sách dict vào bảng tương ứng theo từng batch.
    Dùng bulk_insert_mappings thay to_sql để tuân thủ ORM và Connection Pool.
    """
    if not records:
        logger.warning(f"[Load] Không có dữ liệu để tải vào bảng '{table_name}'.")
        return

    try:
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            session.bulk_insert_mappings(model, batch)
            session.flush()
            logger.info(
                f"[Load] '{table_name}': đã insert batch {i // BATCH_SIZE + 1} "
                f"({len(batch)} bản ghi)"
            )
        session.commit()
        logger.info(f"[Load] '{table_name}': commit thành công. Tổng {len(records)} bản ghi.")
    except Exception as exc:
        session.rollback()
        raise DatabaseUploadError(table=table_name, detail=str(exc)) from exc


def load(
    customers: list[dict],
    products: list[dict],
    orders: list[dict],
) -> None:
    """
    Tạo schema (nếu chưa có) và load dữ liệu theo đúng thứ tự:
        1. Customers (không có FK phụ thuộc)
        2. Products  (không có FK phụ thuộc)
        3. Orders    (FK → customers, products)
    """
    # Tạo bảng từ ORM metadata (chỉ tạo bảng chưa tồn tại)
    logger.info("[Load] Tạo bảng (nếu chưa tồn tại) từ ORM metadata...")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        logger.info("[Load] Bắt đầu tải dữ liệu lên database...")
        _bulk_load(session, Customer, customers, "customers")
        _bulk_load(session, Product, products, "products")
        _bulk_load(session, Order, orders, "orders")
    logger.info("[Load] ETL Pipeline hoàn tất.")

def run_etl(csv_path: Path = CSV_PATH) -> None:
    """Chạy toàn bộ ETL Pipeline: Extract → Transform → Load."""
    logger.info("=" * 60)
    logger.info("ETL Pipeline bắt đầu.")
    logger.info("=" * 60)
    try:
        df = extract(csv_path)
        customers, products, orders = transform(df)
        load(customers, products, orders)
        logger.info("ETL Pipeline hoàn thành thành công.")
    except FileNotFoundError:
        logger.error(f"[Extract] Không tìm thấy file CSV: {csv_path}")
        raise
    except DatabaseUploadError as exc:
        logger.error(f"[Load] Lỗi upload: {exc}")
        raise
    except Exception as exc:
        logger.error(f"[ETL] Lỗi không xác định: {exc}")
        raise


if __name__ == "__main__":
    run_etl()