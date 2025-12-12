"""
Главный модуль FastAPI приложения VR/AR платформы
Объединяет все компоненты системы
"""
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from backend.config import settings
from backend.database import get_db, get_database_info
from backend.api import (
    auth, projects, scenarios, 
    assets, testing, codegen, users
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла приложения
    Выполняется при запуске и остановке
    """
    # Запуск
    logger.info("🚀 Запуск VR/AR платформы...")
    yield
    # Остановка
    logger.info("🛑 Остановка VR/AR платформы...")

# Создание экземпляра FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    description="Платформа для разработки сценариев VR/AR",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Обработка ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type"),
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Ошибка валидации",
            "details": errors,
        },
    )

# Подключение статических файлов фронтенда
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    # Статические файлы (CSS, JS, изображения)
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Обслуживание HTML страниц
    @app.get("/")
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        html_path = frontend_path / f"{path}.html"
        if html_path.exists():
            return FileResponse(str(html_path))
        
        return FileResponse(str(frontend_path / "index.html"))

# Основные API endpoints
@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "success": True,
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/api/status")
async def system_status(db=Depends(get_db)):
    """Полный статус системы"""
    try:
        db_info = get_database_info()
        
        return {
            "success": True,
            "system": settings.APP_NAME,
            "environment": settings.ENVIRONMENT.value,
            "database": db_info,
            "endpoints": [
                {"path": "/api/auth", "description": "Аутентификация"},
                {"path": "/api/projects", "description": "Проекты"},
                {"path": "/api/scenarios", "description": "Сценарии"},
                {"path": "/api/assets", "description": "Активы"},
                {"path": "/api/testing", "description": "Тестирование"},
                {"path": "/api/codegen", "description": "Генерация кода"},
            ]
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/config")
async def client_config():
    """Конфигурация для фронтенда"""
    return {
        "success": True,
        "config": {
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "api_url": f"http://{settings.HOST}:{settings.PORT}/api",
            "upload_max_size": settings.MAX_UPLOAD_SIZE,
            "debug": settings.DEBUG,
            "features": {
                "visual_editor": True,
                "asset_management": True,
                "code_generation": True,
                "testing": True,
                "user_roles": True,
            }
        }
    }

# Подключение API роутеров
api_prefix = "/api"
app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Аутентификация"])
# app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["Пользователи"])
app.include_router(projects.router, prefix=f"{api_prefix}/projects", tags=["Проекты"])
app.include_router(scenarios.router, prefix=f"{api_prefix}/scenarios", tags=["Сценарии"])
app.include_router(assets.router, prefix=f"{api_prefix}/assets", tags=["Активы"])
app.include_router(testing.router, prefix=f"{api_prefix}/testing", tags=["Тестирование"])
app.include_router(codegen.router, prefix=f"{api_prefix}/codegen", tags=["Генерация кода"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )