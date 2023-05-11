from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings."""

    MYSQL_HOST: Optional[str]
    MYSQL_DATABASE: Optional[str]
    MYSQL_USER: Optional[str]
    MYSQL_PASSWORD: Optional[str]

    SQLITE: bool = False
    SQLITE_DATABASE_FILE: str = "database.db"

    DATABASE_URI: Optional[str] = None

    @validator("DATABASE_URI", pre=True, allow_reuse=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """
        Assemble the database connection URI.

        If the `DATABASE_URI` value is already provided as a string, it is returned
        as is.
        Otherwise, if SQLite is enabled, the connection URI is generated using the
        `SQLITE_DATABASE_FILE`.
        If SQLite is not enabled, the connection URI is generated using the MySQL
        configuration values.

        Args:
            v: The value of `DATABASE_URI`.
            values: A dictionary of all the settings values.

        Returns:
            The assembled database connection URI.
        """
        if isinstance(v, str):
            return v

        if values.get("SQLITE", True):
            return f"sqlite:///{values.get('SQLITE_DATABASE_FILE')}"

        return (
            f"mysql+pymysql://{values.get('MYSQL_USER')}:{values.get('MYSQL_PASSWORD')}@{values.get('MYSQL_HOST')}"
            f"/{values.get('MYSQL_DATABASE')}"
        )

    class Config:
        """Settings configuration."""

        case_sensitive = True
        env_file = str(Path.home() / ".env.default"), ".env"


settings = Settings()
