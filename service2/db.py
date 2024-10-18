from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

CONNECTION_STRING = "postgresql://admin:admin@127.0.0.1:5433/energyia_db"

engine = create_engine(CONNECTION_STRING)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)