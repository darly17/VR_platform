"""
Модели пользователей из UML диаграммы
User (абстрактный) ← Developer, Designer, Tester, Manager
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
import uuid
import hashlib

from backend.database import Base
from backend.models.enums import UserRole

class User(Base):
    """Абстрактный класс Пользователь из UML"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Дополнительные поля для всех пользователей
    avatar_url = Column(String(500))
    phone = Column(String(20))
    department = Column(String(100))
    preferences = Column(JSON, default=dict)  # Настройки пользователя
    
    # Связи из UML диаграммы
    # Developer "1" o-- "0..*" Project : создаёт
    created_projects = relationship("Project", back_populates="creator", 
                                   foreign_keys="Project.created_by")
    
    # Designer "1" o-- "0..*" Asset : управляет
    uploaded_assets = relationship("Asset", back_populates="uploaded_by")
    
    # Tester "1" o-- "0..*" TestRun : выполняет
    test_runs = relationship("TestRun", back_populates="tester")
    
    # Manager "1" o-- "0..*" Project : управляет (через таблицу)
    managed_projects = relationship("Project", secondary="project_managers", 
                                   back_populates="managers")
    
    # Сообщения об ошибках от тестировщика
    reported_bugs = relationship("BugReport", back_populates="reporter")
    
    # Утвержденные сценарии менеджером
    approved_scenarios = relationship("Scenario", secondary="scenario_approvals",
                                     back_populates="approvers")
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.username} ({self.role.value})>"
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "department": self.department,
            "capabilities": self.get_capabilities()
        }
    
    def get_capabilities(self):
        """Возвращает возможности пользователя согласно UML и описанию"""
        base_capabilities = {
            "login": True,
            "logout": True,
            "view_dashboard": True,
            "edit_profile": True
        }
        
        role_capabilities = {
            UserRole.DEVELOPER: {
                "create_scenario": True,
                "edit_logic": True,
                "generate_code": True,
                "manage_visual_scripts": True,
                "test_scenarios": True,
                "export_scenarios": True,
                "manage_project_logic": True,
                "integrate_with_main_project": True
            },
            UserRole.DESIGNER: {
                "upload_asset": True,
                "assign_asset": True,
                "manage_assets": True,
                "preview_3d": True,
                "edit_metadata": True,
                "organize_assets": True,
                "check_visual_correctness": True,
                "manage_asset_library": True
            },
            UserRole.TESTER: {
                "run_test": True,
                "report_bug": True,
                "analyze_results": True,
                "manage_devices": True,
                "generate_reports": True,
                "functional_testing": True,
                "log_actions": True,
                "validate_scenarios": True,
                "assign_bugs_to_developer": True
            },
            UserRole.MANAGER: {
                "approve_scenario": True,
                "manage_versions": True,
                "manage_projects": True,
                "coordinate_team": True,
                "export_projects": True,
                "track_progress": True,
                "finalize_builds": True,
                "manage_project_versions": True,
                "publish_releases": True
            }
        }
        
        return {**base_capabilities, **role_capabilities.get(self.role, {})}
    
    @validates('email')
    def validate_email(self, key, email):
        """Валидация email"""
        if '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower()
    
    def set_password(self, password):
        """Установка хешированного пароля"""
        self.hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Проверка пароля"""
        return self.hashed_password == hashlib.sha256(password.encode()).hexdigest()
    
    def login(self):
        """Метод входа из UML"""
        self.last_login = func.now()
        return True
    
    def logout(self):
        """Метод выхода из UML"""
        return True


# Конкретные классы пользователей (можно использовать как фабрику)
class Developer(User):
    """Разработчик сценариев VR/AR из UML"""
    __mapper_args__ = {'polymorphic_identity': UserRole.DEVELOPER}
    
    def create_scenario(self):
        """Создать сценарий (метод из UML)"""
        from backend.models.scenario import Scenario
        return Scenario(created_by=self.id)
    
    def edit_logic(self):
        """Редактировать логику (метод из UML)"""
        print(f"Разработчик {self.username} редактирует логику сценария")
        return True


class Designer(User):
    """Дизайнер из UML"""
    __mapper_args__ = {'polymorphic_identity': UserRole.DESIGNER}
    
    def upload_asset(self, file_path, asset_type, metadata=None):
        """Загрузить актив (метод из UML)"""
        from backend.models.asset import Asset
        asset = Asset(
            name=file_path.split('/')[-1],
            asset_type=asset_type,
            file_path=file_path,
            metadata=metadata or {},
            uploaded_by=self.id
        )
        return asset
    
    def assign_asset(self, asset_id, object_id):
        """Назначить актив объекту (метод из UML)"""
        print(f"Дизайнер {self.username} назначает актив {asset_id} объекту {object_id}")
        return True


class Tester(User):
    """Тестировщик из UML"""
    __mapper_args__ = {'polymorphic_identity': UserRole.TESTER}
    
    def run_test(self, scenario_id, device_id=None):
        """Запустить тест (метод из UML)"""
        from backend.models.testing import TestRun
        test_run = TestRun(
            scenario_id=scenario_id,
            device_id=device_id,
            tester_id=self.id,
            status="pending"
        )
        return test_run
    
    def report_bug(self, description, scenario_id=None, severity="medium"):
        """Сообщить об ошибке (метод из UML)"""
        from backend.models.testing import BugReport
        bug = BugReport(
            description=description,
            scenario_id=scenario_id,
            severity=severity,
            reporter_id=self.id,
            status="open"
        )
        return bug


class Manager(User):
    """Менеджер проекта из UML"""
    __mapper_args__ = {'polymorphic_identity': UserRole.MANAGER}
    
    def approve_scenario(self, scenario_id):
        """Утвердить сценарий (метод из UML)"""
        print(f"Менеджер {self.username} утверждает сценарий {scenario_id}")
        return True
    
    def manage_versions(self, project_id):
        """Управлять версиями (метод из UML)"""
        print(f"Менеджер {self.username} управляет версиями проекта {project_id}")
        return True