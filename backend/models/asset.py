"""
Модели активов из UML диаграммы
Asset, Object3D (реализует IInteractiveObject), AssetLibrary
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid
import os

from backend.database import Base
from backend.models.enums import AssetType

# Таблица для связи AssetLibrary - Asset
asset_library_items = Table(
    'asset_library_items',
    Base.metadata,
    Column('library_id', String(36), ForeignKey('asset_libraries.id'), primary_key=True),
    Column('asset_id', String(36), ForeignKey('assets.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    Column('tags', JSON, default=list)
)


class Asset(Base):
    """Класс Актив из UML"""
    __tablename__ = "assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    asset_type = Column(String(50))  # ТипАктива из UML
    file_path = Column(String(500))  # ПутьКФайлу из UML
    uploaded_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Метаданные из UML (Map<String,String>) - ПЕРЕИМЕНОВАНО!
    asset_metadata = Column("asset_metadata", JSON, default=dict)
    
    # Дополнительные поля
    file_size = Column(Integer, default=0)  # Размер файла в байтах
    file_hash = Column(String(64))  # Хеш файла для проверки целостности
    is_public = Column(Boolean, default=True)
    tags = Column(JSON, default=list)
    preview_url = Column(String(500))  # URL превью
    thumbnail_url = Column(String(500))  # URL миниатюры
    
    # Связи из UML диаграммы
    # Designer "1" o-- "0..*" Asset : управляет
    uploaded_by_user = relationship("User", back_populates="uploaded_assets")  # Исправлено имя связи!
    
    # Object3D "1" *-- "1" Asset : ссылается на
    object_3d = relationship("Object3D", back_populates="asset", uselist=False,
                           cascade="all, delete-orphan")
    
    # AssetLibrary "1" *-- "0..*" Asset : хранит
    libraries = relationship("AssetLibrary", secondary=asset_library_items,
                           back_populates="assets")
    
    # Проекты, использующие этот актив
    projects = relationship("Project", secondary="project_assets",
                          back_populates="assets")
    
    # Сценарии, использующие этот актив
    scenarios = relationship("Scenario", secondary="scenario_assets",
                           back_populates="assets_used")
    
    def __repr__(self):
        return f"<Asset {self.name} ({self.asset_type})>"
    
    def load(self):
        """Загрузить актив (метод из UML)"""
        print(f"Актив '{self.name}' загружен из {self.file_path}")
        
        # Проверяем существование файла
        if os.path.exists(self.file_path):
            self.file_size = os.path.getsize(self.file_path)
            return True
        return False
    
    def unload(self):
        """Выгрузить актив (метод из UML)"""
        print(f"Актив '{self.name}' выгружен")
        return True
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.asset_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.asset_metadata,  # Используем переименованное поле
            "tags": self.tags,
            "is_public": self.is_public,
            "preview_url": self.preview_url,
            "libraries_count": len(self.libraries),
            "projects_count": len(self.projects)
        }
    
    def add_metadata(self, key, value):
        """Добавить метаданные (метод из UML)"""
        self.asset_metadata[key] = value
        return True
    
    def get_file_info(self):
        """Получить информацию о файле"""
        import os
        from pathlib import Path
        
        if not self.file_path or not os.path.exists(self.file_path):
            return None
        
        path = Path(self.file_path)
        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size": os.path.getsize(self.file_path),
            "modified": os.path.getmtime(self.file_path),
            "path": str(path.absolute())
        }
    
    def is_3d_model(self):
        """Проверить, является ли актив 3D моделью"""
        return self.asset_type == AssetType.MODEL_3D.value
    
    @validates('asset_type')
    def validate_asset_type(self, key, asset_type):
        """Валидация типа актива"""
        valid_types = [t.value for t in AssetType]
        if asset_type not in valid_types:
            raise ValueError(f"Invalid asset type. Must be one of: {valid_types}")
        return asset_type


class Object3D(Base):
    """Класс Объект3D из UML (реализует IInteractiveObject)"""
    __tablename__ = "objects_3d"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    
    # Позиция из UML (Vector3)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    position_z = Column(Float, default=0.0)
    
    # Вращение из UML (Quaternion)
    rotation_x = Column(Float, default=0.0)
    rotation_y = Column(Float, default=0.0)
    rotation_z = Column(Float, default=0.0)
    rotation_w = Column(Float, default=1.0)
    
    # Масштаб из UML (Vector3)
    scale_x = Column(Float, default=1.0)
    scale_y = Column(Float, default=1.0)
    scale_z = Column(Float, default=1.0)
    
    # Ссылки
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"))
    current_state_id = Column(String(36), ForeignKey("states.id"))
    
    # Дополнительные поля
    is_interactive = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    is_collidable = Column(Boolean, default=True)
    properties = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # Связи из UML диаграммы
    # Object3D "1" *-- "1" Asset : ссылается на
    asset = relationship("Asset", back_populates="object_3d")
    
    # Scenario "1" o-- "0..*" Object3D : использует
    scenario = relationship("Scenario", back_populates="objects_3d")
    
    # Текущее состояние объекта
    current_state = relationship("State", back_populates="objects")
    
    def __repr__(self):
        return f"<Object3D {self.name}>"
    
    # Реализация интерфейса IInteractiveObject
    def interact(self):
        """Взаимодействовать с объектом (метод из UML)"""
        print(f"Взаимодействие с объектом '{self.name}'")
        
        if not self.is_interactive:
            print(f"Объект '{self.name}' не является интерактивным")
            return False
        
        # Логика взаимодействия
        if self.current_state:
            print(f"Объект в состоянии: {self.current_state.name}")
        
        # Активируем события взаимодействия
        if "on_interact" in self.properties:
            print(f"Активировано событие: {self.properties['on_interact']}")
        
        return True
    
    def get_state(self):
        """Получить состояние объекта (метод из UML)"""
        state_info = {
            "name": self.name,
            "position": {"x": self.position_x, "y": self.position_y, "z": self.position_z},
            "rotation": {"x": self.rotation_x, "y": self.rotation_y, 
                        "z": self.rotation_z, "w": self.rotation_w},
            "scale": {"x": self.scale_x, "y": self.scale_y, "z": self.scale_z},
            "is_interactive": self.is_interactive,
            "is_visible": self.is_visible,
            "is_collidable": self.is_collidable,
            "current_state": self.current_state.name if self.current_state else None,
            "asset": self.asset.name if self.asset else None
        }
        return state_info
    
    def move(self, new_position):
        """Переместить объект (метод из UML)"""
        self.position_x = new_position[0]
        self.position_y = new_position[1]
        self.position_z = new_position[2]
        print(f"Объект '{self.name}' перемещен")
        return True
    
    def rotate(self, new_rotation):
        """Повернуть объект (метод из UML)"""
        self.rotation_x = new_rotation[0]
        self.rotation_y = new_rotation[1]
        self.rotation_z = new_rotation[2]
        self.rotation_w = new_rotation[3] if len(new_rotation) > 3 else 1.0
        print(f"Объект '{self.name}' повернут")
        return True
    
    def scale(self, new_scale):
        """Масштабировать объект (метод из UML)"""
        self.scale_x = new_scale[0]
        self.scale_y = new_scale[1]
        self.scale_z = new_scale[2]
        print(f"Объект '{self.name}' масштабирован")
        return True
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "asset_id": self.asset_id,
            "scenario_id": self.scenario_id,
            "current_state_id": self.current_state_id,
            "position": {"x": self.position_x, "y": self.position_y, "z": self.position_z},
            "rotation": {"x": self.rotation_x, "y": self.rotation_y, 
                        "z": self.rotation_z, "w": self.rotation_w},
            "scale": {"x": self.scale_x, "y": self.scale_y, "z": self.scale_z},
            "is_interactive": self.is_interactive,
            "is_visible": self.is_visible,
            "is_collidable": self.is_collidable,
            "properties": self.properties,
            "tags": self.tags
        }
    
    def set_property(self, key, value):
        """Установить свойство объекта"""
        self.properties[key] = value
        return True
    
    def add_tag(self, tag):
        """Добавить тег объекту"""
        if tag not in self.tags:
            self.tags.append(tag)
        return True


class AssetLibrary(Base):
    """Класс БиблиотекаАктивов из UML"""
    __tablename__ = "asset_libraries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительные поля
    is_public = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Системная библиотека
    category = Column(String(50))  # Категория библиотеки
    tags = Column(JSON, default=list)
    settings = Column(JSON, default=dict)  # Настройки библиотеки
    
    # Связи из UML диаграммы
    # AssetLibrary "1" *-- "0..*" Asset : хранит (композиция)
    assets = relationship("Asset", secondary=asset_library_items,
                        back_populates="libraries")
    
    # Создатель библиотеки
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<AssetLibrary {self.name} ({len(self.assets)} assets)>"
    
    def add_asset(self, asset):
        """Добавить актив (метод из UML)"""
        if asset not in self.assets:
            self.assets.append(asset)
            print(f"Актив '{asset.name}' добавлен в библиотеку '{self.name}'")
            return True
        return False
    
    def remove_asset(self, asset_id):
        """Удалить актив (метод из UML)"""
        asset_to_remove = None
        for asset in self.assets:
            if asset.id == asset_id:
                asset_to_remove = asset
                break
        
        if asset_to_remove:
            self.assets.remove(asset_to_remove)
            print(f"Актив '{asset_to_remove.name}' удален из библиотеки")
            return True
        return False
    
    def find_asset(self, query):
        """Найти актив (метод из UML)"""
        results = []
        query_lower = query.lower()
        
        for asset in self.assets:
            if (query_lower in asset.name.lower() or 
                query_lower in asset.asset_type.lower() or
                any(query_lower in tag.lower() for tag in asset.tags)):
                results.append(asset)
        
        return results
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_public": self.is_public,
            "is_system": self.is_system,
            "category": self.category,
            "assets_count": len(self.assets),
            "tags": self.tags
        }
    
    def get_assets_by_type(self, asset_type):
        """Получить активы по типу"""
        return [asset for asset in self.assets if asset.asset_type == asset_type]
    
    def get_categories(self):
        """Получить категории активов в библиотеке"""
        categories = {}
        for asset in self.assets:
            if asset.asset_type not in categories:
                categories[asset.asset_type] = 0
            categories[asset.asset_type] += 1
        return categories