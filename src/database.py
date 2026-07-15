from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "postgresql://postgres:123456@localhost:5432/sales_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
Base=declarative_base()

def verify_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
            print("successfully connected to database")
    except Exception as e:
        print("fail to connect with database")
        print(e)
        raise e
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

verify_db_connection()