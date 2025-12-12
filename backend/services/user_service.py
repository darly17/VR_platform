"""
Сервис пользователей (UserController)
Соответствует UML диаграмме классов модели
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import logging
import hashlib

from backend.models.user import User, Developer, Designer, Tester, Manager
from backend.models.project import Project
from backend.models.scenario import Scenario
from backend.models.testing import TestRun, BugReport
from backend.models.enums import UserRole

logger = logging.getLogger(__name__)

class UserService:
    """UserController из UML - управление пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, username: str, email: str, password: str, 
                   role: str, full_name: str = None, 
                   department: str = None, **kwargs) -> Optional[User]:
        """Создать нового пользователя"""
        try:
            # Проверяем уникальность username и email
            if self.get_user_by_username(username):
                raise ValueError(f"Пользователь с именем '{username}' уже существует")
            
            if self.get_user_by_email(email):
                raise ValueError(f"Пользователь с email '{email}' уже существует")
            
            # Создаем пользователя в зависимости от роли
            user_class = self._get_user_class_by_role(role)
            
            user = user_class(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                department=department
            )
            
            user.set_password(password)
            
            # Устанавливаем дополнительные поля
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Пользователь создан: {username} (ID: {user.id}, Роль: {role})")
            return user
            
        except ValueError as e:
            self.db.rollback()
            logger.warning(f"Ошибка создания пользователя: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Получить пользователя по ID"""
        return self.db.query(User).options(
            joinedload(User.created_projects),
            joinedload(User.managed_projects),
            joinedload(User.uploaded_assets),
            joinedload(User.test_runs),
            joinedload(User.reported_bugs),
            joinedload(User.approved_scenarios)
        ).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по имени"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя (метод из UML User)"""
        user = self.get_user_by_username(username)
        
        if not user:
            # Пробуем найти по email
            user = self.get_user_by_email(username)
        
        if not user or not user.check_password(password):
            return None
        
        if not user.is_active:
            return None
        
        try:
            user.login()
            self.db.commit()
            logger.info(f"Пользователь аутентифицирован: {username}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка аутентификации: {e}")
            return None
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Обновить данные пользователя"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        # Нельзя менять username и email без специальной проверки
        if 'username' in kwargs and kwargs['username'] != user.username:
            if self.get_user_by_username(kwargs['username']):
                raise ValueError(f"Пользователь с именем '{kwargs['username']}' уже существует")
        
        if 'email' in kwargs and kwargs['email'] != user.email:
            if self.get_user_by_email(kwargs['email']):
                raise ValueError(f"Пользователь с email '{kwargs['email']}' уже существует")
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                if key == 'password':
                    user.set_password(value)
                else:
                    setattr(user, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Пользователь обновлен: {user_id}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления пользователя: {e}")
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """Удалить пользователя"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Проверяем, не является ли пользователь создателем проектов
        if user.created_projects:
            # Можно заменить на soft delete или архивацию
            return False
        
        try:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Пользователь удален: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> bool:
        """Изменить пароль пользователя"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        if not user.check_password(old_password):
            return False
        
        try:
            user.set_password(new_password)
            self.db.commit()
            logger.info(f"Пароль изменен для пользователя: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка изменения пароля: {e}")
            return False
    
    def get_user_capabilities(self, user_id: str) -> Dict[str, bool]:
        """Получить возможности пользователя (соответствует UML)"""
        user = self.get_user(user_id)
        if not user:
            return {}
        
        return user.get_capabilities()
    
    def search_users(self, query: str = None, role: str = None,
                    department: str = None, is_active: bool = None,
                    limit: int = 50, offset: int = 0) -> List[User]:
        """Поиск пользователей"""
        db_query = self.db.query(User)
        
        filters = []
        
        if query:
            search_query = f"%{query}%"
            filters.append(
                or_(
                    User.username.ilike(search_query),
                    User.email.ilike(search_query),
                    User.full_name.ilike(search_query)
                )
            )
        
        if role:
            filters.append(User.role == role)
        
        if department:
            filters.append(User.department == department)
        
        if is_active is not None:
            filters.append(User.is_active == is_active)
        
        if filters:
            db_query = db_query.filter(and_(*filters))
        
        return db_query.limit(limit).offset(offset).all()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        user = self.get_user(user_id)
        if not user:
            return {}
        
        stats = {
            "projects_created": len(user.created_projects),
            "projects_managed": len(user.managed_projects),
            "assets_uploaded": len(user.uploaded_assets),
            "test_runs_performed": len(user.test_runs),
            "bugs_reported": len(user.reported_bugs),
            "scenarios_approved": len(user.approved_scenarios)
        }
        
        # Для разработчика
        if user.role == UserRole.DEVELOPER.value:
            # Получаем все сценарии, созданные пользователем
            developer_scenarios = self.db.query(Scenario).filter(
                Scenario.created_by == user_id
            ).count()
            stats["scenarios_created"] = developer_scenarios
        
        # Для тестировщика
        if user.role == UserRole.TESTER.value:
            # Получаем статистику тестов
            passed_tests = self.db.query(TestRun).filter(
                TestRun.tester_id == user_id,
                TestRun.status == 'passed'
            ).count()
            
            failed_tests = self.db.query(TestRun).filter(
                TestRun.tester_id == user_id,
                TestRun.status == 'failed'
            ).count()
            
            stats.update({
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "success_rate": round(passed_tests / max(passed_tests + failed_tests, 1) * 100, 2)
            })
        
        return stats
    
    def deactivate_user(self, user_id: str) -> bool:
        """Деактивировать пользователя"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            user.is_active = False
            self.db.commit()
            logger.info(f"Пользователь деактивирован: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка деактивации пользователя: {e}")
            return False
    
    def activate_user(self, user_id: str) -> bool:
        """Активировать пользователя"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            user.is_active = True
            self.db.commit()
            logger.info(f"Пользователь активирован: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка активации пользователя: {e}")
            return False
    
    def get_users_by_role(self, role: str) -> List[User]:
        """Получить всех пользователей определенной роли"""
        return self.db.query(User).filter(User.role == role).all()
    
    def _get_user_class_by_role(self, role: str):
        """Получить класс пользователя по роли"""
        role_classes = {
            UserRole.DEVELOPER.value: Developer,
            UserRole.DESIGNER.value: Designer,
            UserRole.TESTER.value: Tester,
            UserRole.MANAGER.value: Manager
        }
        return role_classes.get(role, User)