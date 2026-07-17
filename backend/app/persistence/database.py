from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

def get_session() -> Session:
    return Session(engine)