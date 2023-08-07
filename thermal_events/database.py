import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from tempfile import mkdtemp

from thermal_events import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URI else {}

if hasattr(sys, "_called_from_test"):
    temp_folder_path = mkdtemp()
    path = Path(temp_folder_path) / "test_database.sqlite"

    engine = create_engine("sqlite:///" + str(path))
else:
    engine = create_engine(
        settings.DATABASE_URI,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args,
        isolation_level="READ COMMITTED"
        if "sqlite" not in settings.DATABASE_URI
        else "SERIALIZABLE",
    )


def _fk_pragma_on_connect(dbapi_con, con_record):
    """Enable foreign key support for SQLite connections."""
    dbapi_con.execute("pragma foreign_keys=ON")


if "sqlite" in settings.DATABASE_URI:
    event.listen(engine, "connect", _fk_pragma_on_connect)

SessionLocal = sessionmaker(
    bind=engine,
)


# Dependency
def get_db():
    """Create a new database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
