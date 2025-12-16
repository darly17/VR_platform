"""
Сервис проектов (ProjectController)
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import logging

from backend.models.project import Project, project_managers, project_assets
from backend.models.scenario import Scenario
from backend.models.asset import Asset
from backend.models.user import User
from backend.models.enums import UserRole

logger = logging.getLogger(__name__)

class ProjectService:
    """ProjectController из UML - управление проектами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(self, name: str, description: str, created_by: str, 
                      target_platform: str = None, engine: str = None, 
                      tags: List[str] = None) -> Project:
        """
        Создать новый проект
        Соответствует методу create_scenario() из UML
        """
        try:
            project = Project(
                name=name,
                description=description,
                created_by=created_by,
                target_platform=target_platform,
                engine=engine,
                tags=tags or []
            )
            
            self.db.add(project)
            self.db.flush()
            
            # Автоматически добавляем создателя как менеджера
            self.add_manager(project.id, created_by)
            
            logger.info(f"Проект создан: {name} (ID: {project.id})")
            return project
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания проекта: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Получить проект по ID"""
        return self.db.query(Project).options(
            joinedload(Project.creator),
            joinedload(Project.managers),
            joinedload(Project.scenarios),
            joinedload(Project.assets)
        ).filter(Project.id == project_id).first()
    
    def get_user_projects(self, user_id: str, role: str = None) -> List[Project]:
        """Получить проекты пользователя"""
        query = self.db.query(Project).options(
            joinedload(Project.creator),
            joinedload(Project.managers)
        )
        
        if role == UserRole.MANAGER.value:
            # Проекты, которыми управляет пользователь
            query = query.join(Project.managers).filter(User.id == user_id)
        elif role == UserRole.DEVELOPER.value:
            # Проекты, созданные пользователем
            query = query.filter(Project.created_by == user_id)
        else:
            # Все проекты, где пользователь является участником
            query = query.filter(
                or_(
                    Project.created_by == user_id,
                    Project.managers.any(User.id == user_id)
                )
            )
        
        return query.all()
    
    def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """Обновить проект"""
        project = self.get_project(project_id)
        if not project:
            return None
        
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Проект обновлен: {project_id}")
            return project
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления проекта: {e}")
            raise
    
    def delete_project(self, project_id: str) -> bool:
        """Удалить проект"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        try:
            self.db.delete(project)
            self.db.commit()
            logger.info(f"Проект удален: {project_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления проекта: {e}")
            return False
    
    def add_manager(self, project_id: str, user_id: str) -> bool:
        """Добавить менеджера проекта"""
        project = self.get_project(project_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not project or not user:
            return False
        
        if user not in project.managers:
            project.managers.append(user)
            try:
                self.db.commit()
                logger.info(f"Менеджер добавлен к проекту: {user_id} -> {project_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка добавления менеджера: {e}")
                return False
        return True
    
    def remove_manager(self, project_id: str, user_id: str) -> bool:
        """Удалить менеджера проекта"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        manager_to_remove = None
        for manager in project.managers:
            if manager.id == user_id:
                manager_to_remove = manager
                break
        
        if manager_to_remove:
            project.managers.remove(manager_to_remove)
            try:
                self.db.commit()
                logger.info(f"Менеджер удален из проекта: {user_id} -> {project_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка удаления менеджера: {e}")
                return False
        return False
    
    def add_asset(self, project_id: str, asset_id: str) -> bool:
        """Добавить актив в проект"""
        project = self.get_project(project_id)
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        
        if not project or not asset:
            return False
        
        if asset not in project.assets:
            project.assets.append(asset)
            try:
                self.db.commit()
                logger.info(f"Актив добавлен в проект: {asset_id} -> {project_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка добавления актива: {e}")
                return False
        return True
    
    def remove_asset(self, project_id: str, asset_id: str) -> bool:
        """Удалить актив из проекта"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        asset_to_remove = None
        for asset in project.assets:
            if asset.id == asset_id:
                asset_to_remove = asset
                break
        
        if asset_to_remove:
            project.assets.remove(asset_to_remove)
            try:
                self.db.commit()
                logger.info(f"Актив удален из проекта: {asset_id} -> {project_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка удаления актива: {e}")
                return False
        return False
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Получить статистику проекта"""
        project = self.get_project(project_id)
        if not project:
            return {}
        
        return {
            "scenarios": len(project.scenarios),
            "assets": len(project.assets),
            "managers": len(project.managers),
            "active_scenarios": len([s for s in project.scenarios if s.is_active]),
            "test_runs": len(project.test_runs) if hasattr(project, 'test_runs') else 0
        }
    
    def archive_project(self, project_id: str) -> bool:
        """Архивировать проект"""
        return self.update_project(project_id, status="archived")
    
    def search_projects(self, query: str, user_id: str = None) -> List[Project]:
        """Поиск проектов"""
        search_query = f"%{query}%"
        db_query = self.db.query(Project).options(
            joinedload(Project.creator),
            joinedload(Project.managers)
        ).filter(
            or_(
                Project.name.ilike(search_query),
                Project.description.ilike(search_query)
            )
        )
        
        if user_id:
            db_query = db_query.filter(
                or_(
                    Project.created_by == user_id,
                    Project.managers.any(User.id == user_id)
                )
            )
        
        return db_query.all()