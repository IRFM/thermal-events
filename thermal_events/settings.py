from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):

    MYSQL_HOST: Optional[str]
    MYSQL_DATABASE: Optional[str]
    MYSQL_USER: Optional[str]
    MYSQL_PASSWORD: Optional[str]

    SQLITE: bool = False
    SQLITE_DATABASE_FILE: str = "database.db"

    DATABASE_URI: Optional[str] = None

    @validator("DATABASE_URI", pre=True, allow_reuse=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v

        if values.get("SQLITE", True):
            return f"sqlite:///{values.get('SQLITE_DATABASE_FILE')}"

        return (
            f"mysql+pymysql://{values.get('MYSQL_USER')}:{values.get('MYSQL_PASSWORD')}@{values.get('MYSQL_HOST')}"
            f"/{values.get('MYSQL_DATABASE')}"
        )

    class Config:
        case_sensitive = True
        env_file = str(Path.home() / ".env.default"), ".env"


settings = Settings()
