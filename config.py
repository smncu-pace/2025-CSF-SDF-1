# config.py
import os


class Config:
    """应用配置"""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    PORT = int(os.environ.get("PORT", 1145))

    # PostgreSQL 基础配置（按自己实际情况改）
    POSTGRES_USER = os.environ.get("PGUSER", "memory_app_user")
    POSTGRES_PASSWORD = os.environ.get("PGPASSWORD", "findyourself")
    POSTGRES_HOST = os.environ.get("PGHOST", "localhost")
    POSTGRES_PORT = os.environ.get("PGPORT", "1227")
    POSTGRES_DB = os.environ.get("PGDATABASE", "memory_app")

    # 注意：这里不再用 @property，而是直接生成一个字符串
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
