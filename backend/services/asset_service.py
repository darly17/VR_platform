"""
Сервис активов (AssetController + ObjectController)
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
import logging
import os
import hashlib
from pathlib import Path

from backend.models.asset import Asset, Object3D, AssetLibrary, asset_library_items
from backend.models.user import User
from backend.models.scenario import Scenario
from backend.models.project import Project
from backend.models.enums import AssetType, UserRole

logger = logging.getLogger(__name__)

class AssetService:
    """
    AssetController из UML - управление активами
    Включает ObjectController для управления 3D объектами
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== AssetController методы ==========
    
    def upload_asset(self, name: str, asset_type: str, uploaded_by: str,
                    file_data: bytes = None, file_path: str = None,
                    metadata: Dict = None, tags: List[str] = None,
                    is_public: bool = True) -> Optional[Asset]:
        """
        Загрузить актив (метод из UML Designer)
        """
        try:
            # Генерируем уникальное имя файла
            if file_data:
                file_hash = hashlib.sha256(file_data).hexdigest()[:16]
                filename = f"{file_hash}_{name}"
                save_path = self.upload_dir / filename
                
                with open(save_path, 'wb') as f:
                    f.write(file_data)
                
                file_path = str(save_path)
                file_size = len(file_data)
            elif file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            else:
                file_size = 0
            
            asset = Asset(
                name=name,
                asset_type=asset_type,
                file_path=file_path,
                uploaded_by=uploaded_by,
                file_size=file_size,
                metadata=metadata or {},
                tags=tags or [],
                is_public=is_public
            )
            
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)
            
            logger.info(f"Актив загружен: {name} (ID: {asset.id})")
            return asset
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка загрузки актива: {e}")
            return None
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Получить актив по ID"""
        return self.db.query(Asset).options(
            joinedload(Asset.uploaded_by_user),
            joinedload(Asset.libraries),
            joinedload(Asset.projects),
            joinedload(Asset.scenarios)
        ).filter(Asset.id == asset_id).first()
    
    def search_assets(self, query: str = None, asset_type: str = None,
                     tags: List[str] = None, uploaded_by: str = None,
                     limit: int = 50, offset: int = 0) -> List[Asset]:
        """Поиск активов"""
        db_query = self.db.query(Asset).options(
            joinedload(Asset.uploaded_by_user)
        )
        
        filters = []
        
        if query:
            search_query = f"%{query}%"
            filters.append(
                or_(
                    Asset.name.ilike(search_query),
                    Asset.metadata.ilike(search_query) if hasattr(Asset.metadata, 'ilike') else None
                )
            )
        
        if asset_type:
            filters.append(Asset.asset_type == asset_type)
        
        if tags:
            for tag in tags:
                filters.append(Asset.tags.contains([tag]))
        
        if uploaded_by:
            filters.append(Asset.uploaded_by == uploaded_by)
        
        if filters:
            db_query = db_query.filter(and_(*filters))
        
        return db_query.order_by(desc(Asset.created_at)).limit(limit).offset(offset).all()
    
    def update_asset(self, asset_id: str, **kwargs) -> Optional[Asset]:
        """Обновить актив"""
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        
        for key, value in kwargs.items():
            if hasattr(asset, key) and value is not None:
                setattr(asset, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(asset)
            logger.info(f"Актив обновлен: {asset_id}")
            return asset
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления актива: {e}")
            raise
    
    def delete_asset(self, asset_id: str) -> bool:
        """Удалить актив"""
        asset = self.get_asset(asset_id)
        if not asset:
            return False
        
        # Удаляем файл, если он существует
        if asset.file_path and os.path.exists(asset.file_path):
            try:
                os.remove(asset.file_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить файл: {e}")
        
        try:
            self.db.delete(asset)
            self.db.commit()
            logger.info(f"Актив удален: {asset_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления актива: {e}")
            return False
    
    def load_asset(self, asset_id: str) -> Tuple[bool, str]:
        """Загрузить актив (метод из UML Asset)"""
        asset = self.get_asset(asset_id)
        if not asset:
            return False, "Актив не найден"
        
        try:
            result = asset.load()
            self.db.commit()
            return result, "Актив загружен" if result else "Ошибка загрузки"
        except Exception as e:
            logger.error(f"Ошибка загрузки актива: {e}")
            return False, str(e)
    
    def add_asset_to_library(self, asset_id: str, library_id: str, 
                            tags: List[str] = None) -> bool:
        """Добавить актив в библиотеку"""
        asset = self.get_asset(asset_id)
        library = self.db.query(AssetLibrary).filter(AssetLibrary.id == library_id).first()
        
        if not asset or not library:
            return False
        
        if asset not in library.assets:
            library.assets.append(asset)
            if tags:
                # Обновляем теги актива для этой библиотеки
                pass  # Реализация зависит от структуры связи
            
            try:
                self.db.commit()
                logger.info(f"Актив добавлен в библиотеку: {asset_id} -> {library_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка добавления актива в библиотеку: {e}")
                return False
        return True
    
    def get_asset_file_info(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о файле актива"""
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        
        return asset.get_file_info()
    
    # ========== ObjectController методы ==========
    
    def create_object_3d(self, name: str, asset_id: str, 
                        position: List[float] = None,
                        rotation: List[float] = None,
                        scale: List[float] = None,
                        scenario_id: str = None,
                        current_state_id: str = None) -> Optional[Object3D]:
        """Создать 3D объект"""
        try:
            object_3d = Object3D(
                name=name,
                asset_id=asset_id,
                scenario_id=scenario_id,
                current_state_id=current_state_id,
                position_x=position[0] if position else 0.0,
                position_y=position[1] if position else 0.0,
                position_z=position[2] if position else 0.0,
                rotation_x=rotation[0] if rotation and len(rotation) > 0 else 0.0,
                rotation_y=rotation[1] if rotation and len(rotation) > 1 else 0.0,
                rotation_z=rotation[2] if rotation and len(rotation) > 2 else 0.0,
                rotation_w=rotation[3] if rotation and len(rotation) > 3 else 1.0,
                scale_x=scale[0] if scale else 1.0,
                scale_y=scale[1] if scale else 1.0,
                scale_z=scale[2] if scale else 1.0
            )
            
            self.db.add(object_3d)
            self.db.commit()
            self.db.refresh(object_3d)
            logger.info(f"3D объект создан: {name} (ID: {object_3d.id})")
            return object_3d
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания 3D объекта: {e}")
            return None
    
    def get_object_3d(self, object_id: str) -> Optional[Object3D]:
        """Получить 3D объект по ID"""
        return self.db.query(Object3D).options(
            joinedload(Object3D.asset),
            joinedload(Object3D.scenario),
            joinedload(Object3D.current_state)
        ).filter(Object3D.id == object_id).first()
    
    def update_object_3d(self, object_id: str, **kwargs) -> Optional[Object3D]:
        """Обновить 3D объект"""
        object_3d = self.get_object_3d(object_id)
        if not object_3d:
            return None
        
        for key, value in kwargs.items():
            if hasattr(object_3d, key) and value is not None:
                setattr(object_3d, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(object_3d)
            logger.info(f"3D объект обновлен: {object_id}")
            return object_3d
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления 3D объекта: {e}")
            raise
    
    def interact_with_object(self, object_id: str) -> Tuple[bool, str]:
        """Взаимодействовать с объектом (метод из UML IInteractiveObject)"""
        object_3d = self.get_object_3d(object_id)
        if not object_3d:
            return False, "Объект не найден"
        
        try:
            result = object_3d.interact()
            self.db.commit()
            return result, "Взаимодействие выполнено" if result else "Объект не интерактивный"
        except Exception as e:
            logger.error(f"Ошибка взаимодействия с объектом: {e}")
            return False, str(e)
    
    def move_object(self, object_id: str, new_position: List[float]) -> bool:
        """Переместить объект (метод из UML Object3D)"""
        object_3d = self.get_object_3d(object_id)
        if not object_3d:
            return False
        
        try:
            result = object_3d.move(new_position)
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка перемещения объекта: {e}")
            return False
    
    # ========== AssetLibrary методы ==========
    
    def create_asset_library(self, name: str, created_by: str,
                            description: str = None, is_public: bool = True,
                            category: str = None) -> Optional[AssetLibrary]:
        """Создать библиотеку активов"""
        try:
            library = AssetLibrary(
                name=name,
                description=description,
                created_by=created_by,
                is_public=is_public,
                category=category
            )
            
            self.db.add(library)
            self.db.commit()
            self.db.refresh(library)
            logger.info(f"Библиотека активов создана: {name} (ID: {library.id})")
            return library
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания библиотеки активов: {e}")
            return None
    
    def get_asset_library(self, library_id: str) -> Optional[AssetLibrary]:
        """Получить библиотеку активов"""
        return self.db.query(AssetLibrary).options(
            joinedload(AssetLibrary.creator),
            joinedload(AssetLibrary.assets)
        ).filter(AssetLibrary.id == library_id).first()
    
    def search_in_library(self, library_id: str, query: str) -> List[Asset]:
        """Найти активы в библиотеке (метод из UML AssetLibrary)"""
        library = self.get_asset_library(library_id)
        if not library:
            return []
        
        return library.find_asset(query)
    
    def get_assets_by_type(self, library_id: str, asset_type: str) -> List[Asset]:
        """Получить активы определенного типа из библиотеки"""
        library = self.get_asset_library(library_id)
        if not library:
            return []
        
        return library.get_assets_by_type(asset_type)
    
    def get_asset_stats(self) -> Dict[str, Any]:
        """Получить статистику по активам"""
        total_assets = self.db.query(func.count(Asset.id)).scalar()
        by_type = self.db.query(
            Asset.asset_type, 
            func.count(Asset.id)
        ).group_by(Asset.asset_type).all()
        
        total_size = self.db.query(func.sum(Asset.file_size)).scalar() or 0
        
        return {
            "total_assets": total_assets,
            "by_type": dict(by_type),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0
        }