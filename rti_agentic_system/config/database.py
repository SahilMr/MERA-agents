from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event

DATABASE_URL = "sqlite:///./rti_system.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')
    dbapi_con.execute('pragma journal_mode=WAL')

event.listen(engine, 'connect', _fk_pragma_on_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
