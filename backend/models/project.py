"""
Модель проекта из UML диаграммы
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from backend.database import Base

# Таблица для связи многие-ко-многим Project - User (менеджеры)
project_managers = Table(
    'project_managers',
    Base.metadata,
    Column('project_id', String(36), ForeignKey('projects.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)

# Таблица для связи Project - Asset (активы проекта)
project_assets = Table(
    'project_assets',
    Base.metadata,
    Column('project_id', String(36), ForeignKey('projects.id'), primary_key=True),
    Column('asset_id', String(36), ForeignKey('assets.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)

class Project(Base):
    """Класс Проект из UML"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    version = Column(String(20), default="1.0.0")
    status = Column(String(20), default="active")  # active, archived, deleted
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительные поля
    target_platform = Column(String(50))  # VR, AR, Mixed
    engine = Column(String(50))  # Unity, Unreal, Custom
    tags = Column(JSON, default=list)
    settings = Column(JSON, default=dict)  # Настройки проекта
    
    # Связи из UML диаграммы
    # Developer "1" o-- "0..*" Project : создаёт
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    
    # Manager "1" o-- "0..*" Project : управляет
    managers = relationship("User", secondary=project_managers, back_populates="managed_projects")
    
    # Project "1" *-- "1..*" Scenario : содержит (композиция)
    scenarios = relationship("Scenario", back_populates="project", 
                           cascade="all, delete-orphan")
    
    # Активы проекта
    assets = relationship("Asset", secondary=project_assets, back_populates="projects")
    
    # Тестовые прогоны проекта
    test_runs = relationship("TestRun", back_populates="project")
    
    def __repr__(self):
        return f"<Project {self.name} v{self.version}>"
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "target_platform": self.target_platform,
            "engine": self.engine,
            "scenarios_count": len(self.scenarios),
            "assets_count": len(self.assets)
        }
    
    def create_scenario(self, name, description=""):
        """Создать сценарий (метод из UML)"""
        from backend.models.scenario import Scenario
        scenario = Scenario(
            name=name,
            description=description,
            project_id=self.id
        )
        return scenario
    
    def save(self):
        """Сохранить проект (метод из UML)"""
        print(f"Проект '{self.name}' сохранен")
        return True
    
    @validates('version')
    def validate_version(self, key, version):
        """Валидация версии"""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ValueError("Version must be in format X.Y.Z")
        return version
    
    def increment_version(self):
        """Увеличить версию проекта"""
        parts = self.version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        self.version = '.'.join(parts)
        return self.version
    
    def get_stats(self):
        """Получить статистику проекта"""
        return {
            "scenarios": len(self.scenarios),
            "assets": len(self.assets),
            "test_runs": len(self.test_runs),
            "active_scenarios": len([s for s in self.scenarios if s.is_active]),
            "last_updated": self.updated_at
        }