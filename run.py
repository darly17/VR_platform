
import sys
import uvicorn
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def print_banner():

    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                VR/AR PLATFORM v1.0.0                     ║
    ║   Платформа разработки сценариев виртуальной реальности  ║
    ╚══════════════════════════════════════════════════════════╝
    
    📋 Возможности:
      • Визуальное моделирование логики
      • Управление 3D активами
      • Генерация кода (Python, C#, C++)
      • Тестирование сценариев
      • Ролевая система (Разработчик, Дизайнер, Тестировщик, Менеджер)
    
    🔧 Используемые технологии:
      • FastAPI (Python 3.8+)
      • SQLite + SQLAlchemy ORM
      • JWT аутентификация
      • HTML/CSS/JS фронтенд
    """
    print(banner)

def main():

    try:
        print_banner()
        
     
        from backend.database import init_db
        init_db()
        
       
        from backend.config import settings
        
        print(f"\n Запуск сервера...")
        print(f"   📍 Адрес: http://{settings.HOST}:{settings.PORT}")
        print(f"   База данных: {settings.DATABASE_URL}")
        print("\n" + "="*60 + "\n")
        
        # Запуск сервера Uvicorn
        uvicorn.run(
            "backend.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info",
            workers=1
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Приложение остановлено пользователем")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
