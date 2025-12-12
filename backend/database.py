"""
Настройки базы данных SQLite с SQLAlchemy
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

# Создаем директорию data если её нет
Path("data").mkdir(exist_ok=True)

# URL подключения к SQLite базе данных
DATABASE_URL = "sqlite:///./data/database.db"

# Создаем движок базы данных
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Показывает SQL запросы в консоли
    connect_args={"check_same_thread": False}  # Для SQLite
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# Метаданные для миграций
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии базы данных.
    Используется в FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Инициализация базы данных - создание всех таблиц
    Вызывается при запуске приложения
    """
    print("🗄️  Инициализация базы данных SQLite...")
    
    # Импортируем все модели, чтобы SQLAlchemy их зарегистрировал
    from backend.models.user import User
    from backend.models.project import Project, project_managers, project_assets
    from backend.models.scenario import Scenario, State, Transition, scenario_approvals, scenario_assets
    from backend.models.asset import Asset, Object3D, AssetLibrary, asset_library_items
    from backend.models.visual_script import VisualScript, Node, Connection
    from backend.models.testing import TestRun, TestResult, Device, BugReport, test_run_devices
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")
    
    # Создание начальных данных
    create_initial_data()

def check_db_connection():
    """
    Проверка подключения к базе данных
    Возвращает (success, message)
    """
    try:
        with engine.connect() as conn:
            # Исправленный запрос для SQLite
            result = conn.execute(text("SELECT 1"))
            return True, "✅ Подключение к базе данных успешно"
    except Exception as e:
        return False, f"❌ Ошибка подключения: {e}"

def create_initial_data():
    """Создание начальных тестовых данных"""
    from backend.models.user import User
    from backend.models.enums import UserRole, AssetType
    
    # Простая функция хеширования
    def hash_password(password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже пользователи
        user_count = db.query(User).count()
        
        if user_count == 0:
            print("👥 Создание тестовых пользователей...")
            
            # Создаем пользователей для каждой роли
            users = [
                User(
                    username="admin",
                    email="admin@vrar.local",
                    full_name="Администратор Системы",
                    role=UserRole.MANAGER,
                    hashed_password=hash_password("admin123")
                ),
                User(
                    username="dev_user",
                    email="developer@vrar.local",
                    full_name="Иван Разработчик",
                    role=UserRole.DEVELOPER,
                    hashed_password=hash_password("dev123")
                ),
                User(
                    username="design_user",
                    email="designer@vrar.local",
                    full_name="Анна Дизайнер",
                    role=UserRole.DESIGNER,
                    hashed_password=hash_password("design123")
                ),
                User(
                    username="test_user",
                    email="tester@vrar.local",
                    full_name="Петр Тестировщик",
                    role=UserRole.TESTER,
                    hashed_password=hash_password("test123")
                ),
            ]
            
            db.add_all(users)
            db.commit()
            db.refresh(users[0])
            db.refresh(users[1])
            db.refresh(users[2])
            db.refresh(users[3])
            print(f"✅ Создано {len(users)} тестовых пользователя")
            
            # Создаем тестовый проект
            from backend.models.project import Project as ProjectModel
            from backend.models.scenario import Scenario as ScenarioModel, State, Transition
            from backend.models.asset import Asset as AssetModel, Object3D, AssetLibrary
            from backend.models.visual_script import VisualScript, Node, Connection
            from backend.models.testing import TestRun, TestResult, Device, BugReport
            
            print("📁 Создание тестового проекта...")
            
            # Проект
            project = ProjectModel(
                name="Демонстрационный проект VR",
                description="Пример проекта для обучения работе с платформой",
                version="1.0.0",
                created_by=users[1].id  # Разработчик
            )
            db.add(project)
            db.flush()
            
            # Добавляем менеджера в проект
            project.managers.append(users[0])
            
            # Сценарий
            scenario = ScenarioModel(
                name="Взаимодействие с объектом",
                description="Базовый сценарий взаимодействия с 3D объектом",
                project_id=project.id,
                created_by=users[1].id
            )
            db.add(scenario)
            db.flush()
            
            # Состояния сценария
            states = [
                State(
                    name="Начальное состояние",
                    state_type="start",
                    position_x=0,
                    position_y=0,
                    position_z=0,
                    scenario_id=scenario.id
                ),
                State(
                    name="Взаимодействие",
                    state_type="interaction",
                    position_x=100,
                    position_y=0,
                    position_z=0,
                    scenario_id=scenario.id
                ),
                State(
                    name="Завершение",
                    state_type="end",
                    position_x=200,
                    position_y=0,
                    position_z=0,
                    scenario_id=scenario.id
                ),
            ]
            db.add_all(states)
            db.flush()
            
            # Переходы между состояниями
            transitions = [
                Transition(
                    source_state_id=states[0].id,
                    target_state_id=states[1].id,
                    condition="user_interaction == True",
                    priority=1,
                    scenario_id=scenario.id
                ),
                Transition(
                    source_state_id=states[1].id,
                    target_state_id=states[2].id,
                    condition="interaction_completed == True",
                    priority=1,
                    scenario_id=scenario.id
                ),
            ]
            db.add_all(transitions)
            
            # Тестовый актив
            asset = AssetModel(
                name="Коробка",
                asset_type=AssetType.MODEL_3D.value,
                file_path="/uploads/models/box.fbx",
                metadata={"author": "Система", "polygons": "1200", "format": "FBX"},
                uploaded_by=users[2].id
            )
            db.add(asset)
            db.flush()
            
            # 3D объект
            object_3d = Object3D(
                name="Интерактивная коробка",
                position_x=50,
                position_y=20,
                position_z=10,
                asset_id=asset.id,
                scenario_id=scenario.id,
                current_state_id=states[1].id
            )
            db.add(object_3d)
            
            # Библиотека активов
            library = AssetLibrary(
                name="Основная библиотека",
                description="Библиотека по умолчанию",
                created_by=users[2].id,
                is_system=True
            )
            db.add(library)
            library.assets.append(asset)
            
            # Визуальный скрипт
            visual_script = VisualScript(
                name="Скрипт взаимодействия",
                scenario_id=scenario.id,
                created_by=users[1].id
            )
            db.add(visual_script)
            db.flush()
            
            # Узлы визуального скрипта
            nodes = [
                Node(
                    name="Событие взаимодействия",
                    node_type="event",
                    position_x=100,
                    position_y=100,
                    visual_script_id=visual_script.id,
                    properties={"event_name": "on_interact"}
                ),
                Node(
                    name="Проверка условия",
                    node_type="condition",
                    position_x=300,
                    position_y=100,
                    visual_script_id=visual_script.id,
                    properties={"condition": "object_interactable == true"}
                ),
                Node(
                    name="Активация анимации",
                    node_type="action",
                    position_x=500,
                    position_y=100,
                    visual_script_id=visual_script.id,
                    properties={"action": "play_animation", "animation_name": "open_box"}
                ),
            ]
            db.add_all(nodes)
            db.flush()
            
            # Соединения визуального скрипта
            connections = [
                Connection(
                    source_node_id=nodes[0].id,
                    target_node_id=nodes[1].id,
                    connection_type="execution",
                    visual_script_id=visual_script.id
                ),
                Connection(
                    source_node_id=nodes[1].id,
                    target_node_id=nodes[2].id,
                    connection_type="execution",
                    visual_script_id=visual_script.id
                ),
            ]
            db.add_all(connections)
            
            # Устройство для тестирования
            device = Device(
                name="VR Шлем Oculus Quest 2",
                device_type="vr_headset",
                manufacturer="Meta",
                model="Quest 2",
                serial_number="OCULUS-001",
                capabilities=["vr_tracking", "hand_tracking", "room_scale"],
                is_available=True
            )
            db.add(device)
            
            # Тестовый прогон
            test_run = TestRun(
                name="Первый тест сценария",
                scenario_id=scenario.id,
                project_id=project.id,
                tester_id=users[3].id,
                is_automated=True
            )
            db.add(test_run)
            test_run.devices.append(device)
            
            # Утверждение сценария менеджером
            scenario.approvers.append(users[0])  # Менеджер
            
            db.commit()
            print("✅ Тестовые данные созданы")
            
    except Exception as e:
        db.rollback()
        print(f"⚠️  Ошибка при создании начальных данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def get_database_info() -> dict:
    """Получение информации о базе данных"""
    db = SessionLocal()
    try:
        from backend.models.user import User
        from backend.models.project import Project
        from backend.models.scenario import Scenario
        from backend.models.asset import Asset
        from backend.models.visual_script import VisualScript
        from backend.models.testing import TestRun, Device
        
        return {
            "database": "SQLite",
            "path": DATABASE_URL.replace("sqlite:///", ""),
            "tables": {
                "users": db.query(User).count(),
                "projects": db.query(Project).count(),
                "scenarios": db.query(Scenario).count(),
                "states": db.query(State).count(),
                "transitions": db.query(Transition).count(),
                "assets": db.query(Asset).count(),
                "objects_3d": db.query(Object3D).count(),
                "visual_scripts": db.query(VisualScript).count(),
                "test_runs": db.query(TestRun).count(),
                "devices": db.query(Device).count(),
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()