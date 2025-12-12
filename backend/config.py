"""
Конфигурация VR/AR платформы
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from enum import Enum
from pathlib import Path

class Environment(str, Enum):
    """Типы окружения"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class UserRole(str, Enum):
    """Роли пользователей из UML диаграммы"""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    MANAGER = "manager"

class AssetType(str, Enum):
    """Типы активов"""
    MODEL_3D = "3d_model"
    TEXTURE = "texture"
    AUDIO = "audio"
    VIDEO = "video"
    SCRIPT = "script"
    OTHER = "other"

class ProgrammingLanguage(str, Enum):
    """Языки программирования для генерации кода"""
    PYTHON = "python"
    CSHARP = "csharp"
    CPP = "cpp"

class Settings(BaseSettings):
    """
    Настройки приложения
    Значения можно переопределить через .env файл
    """
    
    # Основные настройки
    APP_NAME: str = "VR/AR Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # База данных
    DATABASE_URL: str = "sqlite:///./data/database.db"
    DATABASE_ECHO: bool = False
    
    # Безопасность
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]
    
    # Файлы
    UPLOAD_DIR: Path = Path("data/uploads")
    EXPORT_DIR: Path = Path("data/exports")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Пользователи по умолчанию
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_EMAIL: str = "admin@vrar.local"
    DEFAULT_ADMIN_ROLE: UserRole = UserRole.MANAGER
    
    # Генерация кода
    DEFAULT_PROGRAMMING_LANGUAGE: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Экспорт настроек
settings = Settings()

# Создание директорий при импорте
def create_directories():
    """Создание необходимых директорий"""
    directories = [
        Path("data"),
        settings.UPLOAD_DIR,
        settings.EXPORT_DIR,
        Path("logs"),
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Создана директория: {directory}")

create_directories()