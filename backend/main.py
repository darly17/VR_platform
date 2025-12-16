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
from backend.database import get_db, get_database_info, init_db
from backend.api import auth, projects, scenarios, assets, testing, codegen # Импорт всех api модулей

# Настройка логирования на DEBUG для видимости запросов в терминале
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла приложения
    Выполняется при запуске и остановке
    """
    # Запуск: Инициализируем DB
    logger.info("🚀 Запуск VR/AR платформы...")
    init_db()  # Создаёт таблицы и демо-пользователей (admin/admin123)
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
    allow_origins=["*"],  # Разрешаем все для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ===== ДОБАВЬ ЭТО: Регистрация API роутеров (перед статическими файлами и catch-all) =====
# Используем /api как базовый префикс для всех API
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(testing.router, prefix="/api")
app.include_router(codegen.router, prefix="/api")
# app.include_router(users.router, prefix="/api")
@app.on_event("startup")
async def startup():
    logger.info("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            logger.info(f"Path: {route.path}, Methods: {', '.join(route.methods)}")
# ===== КОНЕЦ ДОБАВЛЕНИЯ =====

# Путь к фронтенду
frontend_path = Path(__file__).parent.parent / "frontend"
frontend_path.mkdir(exist_ok=True)  # Создаём если нет

# Статические файлы: css, js, assets и т.д.
app.mount("/css", StaticFiles(directory=frontend_path / "css"), name="css")
app.mount("/js", StaticFiles(directory=frontend_path / "js"), name="js")
app.mount("/assets", StaticFiles(directory=frontend_path / "assets"), name="assets")

# Конкретные HTML-страницы (только GET)
@app.get("/")
async def root():
    return FileResponse(frontend_path / "index.html")

@app.get("/login.html")
async def login():
    return FileResponse(frontend_path / "login.html")

@app.get("/projects.html")
async def projects():
    return FileResponse(frontend_path / "projects.html")

@app.get("/dashboard.html")
async def dashboard():
    return FileResponse(frontend_path / "dashboard.html")

@app.get("/scenario_editor.html")
async def scenario_editor():
    return FileResponse(frontend_path / "scenario_editor.html")

@app.get("/assets.html")
async def assets_page():
    return FileResponse(frontend_path / "assets.html")

@app.get("/testing.html")
async def testing():
    return FileResponse(frontend_path / "testing.html")

@app.get("/codegen.html")
async def codegen():
    return FileResponse(frontend_path / "codegen.html")

# САМЫЙ ПОСЛЕДНИЙ — catch-all только для GET и только для неизвестных путей
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    possible_file = frontend_path / full_path
    if possible_file.is_file():
        return FileResponse(str(possible_file))
    return FileResponse(str(frontend_path / "index.html"))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug"  # Для детальных логов в терминале
    )