from typing import Dict

from pydantic import BaseModel, PostgresDsn, ValidationError, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class DatabaseConfig(BaseModel):
    """
    Configuration schema for the PostgreSQL database connection.

    Attributes:
        url (PostgresDsn):
            Full PostgreSQL connection string (DSN).
            Example: "postgresql+psycopg2://user:password@localhost:5432/dbname".
        echo (bool):
            Enables SQLAlchemy engine logging. Default: False.
        echo_pool (bool):
            Enables logging for connection pool checkouts/checkins. Default: False.
        pool_size (int):
            Size of the connection pool. Default: 50.
        max_overflow (int):
            Maximum number of connections to allow above pool_size. Default: 10.
        naming_convention (Dict[str, str]):
            SQLAlchemy naming convention for constraints and indexes.
            Ensures consistent schema generation and migrations.

            Default mapping:
                - Index: ix_%(column_0_label)s
                - Unique constraint: uq_%(table_name)s_%(column_0_name)s
                - Check constraint: ck_%(table_name)s_%(constraint_name)s
                - Foreign key: fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
                - Primary key: pk_%(table_name)s
    """
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10
    naming_convention: Dict[str, str] = Field(default_factory=lambda: {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })


class JWTConfig(BaseModel):
    secret_key: str
    algorithm: str
    access_expire_min: int
    refresh_expire_days: int


class RedisConfig(BaseModel):
    url: str | None = None
    port: int | None = None


class AppConfig(BaseModel):
    base_user_role_name: str
    default_role_id: int

    log_level: str = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v):
        return v.upper()

    static_folder: str = "/usr/share/nginx/static"

    @property
    def images_folder(self) -> str:
        return os.path.join(self.static_folder, "images")

    allowed_extensions: set[str] = {"png", "jpg", "jpeg", "gif"}


class Settings(BaseSettings):
    """
    Application settings model.

    Config:
        - Reads environment variables from `.env` and `.test.env` files in `src/`.
        - Case insensitive.
        - Supports nested environment variables using "__" as a delimiter.
        - All environment variables must be prefixed with "APP_CONFIG__".

    Attributes:
        db (DatabaseConfig):
            Database configuration settings object.
    """
    model_config = SettingsConfigDict(
        env_file=("src/.env", "src/.test.env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__"
    )
    db: DatabaseConfig
    redis: RedisConfig = RedisConfig()
    jwt: JWTConfig
    app: AppConfig


try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Invalid configuration: {e}")
