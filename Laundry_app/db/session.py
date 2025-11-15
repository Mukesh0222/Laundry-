
from sqlmodel import SQLModel, create_engine, Session
from core.config import settings

DATABASE_URL = "mysql+pymysql://root:kite@localhost:3306/laundry_db"


print(f"\n Connecting to Database: {DATABASE_URL}")  # full connection string shown

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session
