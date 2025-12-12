"""
Инициализация API модулей
"""

from .auth import router as auth_router
from .projects import router as projects_router
from .scenarios import router as scenarios_router
from .assets import router as assets_router
from .testing import router as testing_router
from .codegen import router as codegen_router

__all__ = [
    'auth_router',
    'projects_router',
    'scenarios_router',
    'assets_router',
    'testing_router',
    'codegen_router'
]