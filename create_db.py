
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

from backend.database import init_db, check_db_connection

def main():
 
    print("=" * 60)
    print("СОЗДАНИЕ БАЗЫ ДАННЫХ VR/AR ПЛАТФОРМЫ")
    print("=" * 60)
    
    # Проверяем подключение
    print("\n🔍 Проверка подключения к базе данных...")
    success, message = check_db_connection()
    print(message)
    
    if not success:
        print("Создание новой базы данных...")
    

    try:
        init_db()
        
        print("\n" + "=" * 60)
        print("🎉 БАЗА ДАННЫХ УСПЕШНО СОЗДАНА!")
        print("=" * 60)
        
        from backend.database import get_database_info
        db_info = get_database_info()
        
        print("\n📊 Созданные таблицы и записи:")
        for table, count in db_info.get("tables", {}).items():
            print(f"  • {table}: {count} записей")
        
        print("\n👤 Тестовые пользователи:")
        print("  • admin (Менеджер) - пароль: admin123")
        print("  • dev_user (Разработчик) - пароль: dev123")
        print("  • design_user (Дизайнер) - пароль: design123")
        print("  • test_user (Тестировщик) - пароль: test123")
        
        print(f"\n📁 Файл базы данных: {Path('data/database.db').absolute()}")
        print("\n✅ Готово к работе!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()