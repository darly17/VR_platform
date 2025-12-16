"""
Сервис сценариев (ScenarioController + StateController + TransitionController)
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import logging

from backend.models.scenario import Scenario, State, Transition, scenario_approvals
from backend.models.project import Project
from backend.models.user import User
from backend.models.enums import UserRole, StateType
from backend.models.visual_script import VisualScript
from backend.models.asset import Object3D

logger = logging.getLogger(__name__)

class ScenarioService:
    """
    ScenarioController из UML - управление сценариями
    Включает StateController и TransitionController
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_scenario(self, name: str, project_id: str, created_by: str,
                       description: str = None) -> Scenario:
        """
        Создать новый сценарий
        Соответствует методу create_scenario() из UML для Developer
        """
        try:
            scenario = Scenario(
                name=name,
                description=description,
                project_id=project_id,
                created_by=created_by
            )
            
            self.db.add(scenario)
            self.db.flush()
            
            # Создаем начальное и конечное состояния по умолчанию
            start_state = self.create_state(
                scenario_id=scenario.id,
                name="Начало",
                state_type=StateType.START.value,
                position=[0, 0, 0]
            )
            
            end_state = self.create_state(
                scenario_id=scenario.id,
                name="Конец",
                state_type=StateType.END.value,
                position=[200, 0, 0]
            )
            
            logger.info(f"Сценарий создан: {name} (ID: {scenario.id})")
            return scenario
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания сценария: {e}")
            raise
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Получить сценарий по ID"""
        return self.db.query(Scenario).options(
            joinedload(Scenario.project),
            joinedload(Scenario.creator),
            joinedload(Scenario.states),
            joinedload(Scenario.transitions),
            joinedload(Scenario.approvers),
            joinedload(Scenario.objects_3d),
            joinedload(Scenario.visual_script)
        ).filter(Scenario.id == scenario_id).first()
    
    def get_project_scenarios(self, project_id: str, 
                             only_active: bool = False) -> List[Scenario]:
        """Получить все сценарии проекта"""
        query = self.db.query(Scenario).options(
            joinedload(Scenario.creator),
            joinedload(Scenario.states)
        ).filter(Scenario.project_id == project_id)
        
        if only_active:
            query = query.filter(Scenario.is_active == True)
        
        return query.all()
    
    def update_scenario(self, scenario_id: str, **kwargs) -> Optional[Scenario]:
        """Обновить сценарий"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scenario, key) and value is not None:
                setattr(scenario, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(scenario)
            logger.info(f"Сценарий обновлен: {scenario_id}")
            return scenario
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления сценария: {e}")
            raise
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """Удалить сценарий"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        try:
            self.db.delete(scenario)
            self.db.commit()
            logger.info(f"Сценарий удален: {scenario_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления сценария: {e}")
            return False
    
    def execute_scenario(self, scenario_id: str) -> Tuple[bool, str]:
        """Выполнить сценарий (метод из UML IScenario)"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False, "Сценарий не найден"
        
        try:
            result = scenario.execute()
            self.db.commit()
            return result, "Сценарий выполнен успешно"
        except Exception as e:
            logger.error(f"Ошибка выполнения сценария: {e}")
            return False, str(e)
    
    def validate_scenario(self, scenario_id: str) -> Tuple[bool, List[str]]:
        """Валидировать сценарий (метод из UML IScenario)"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False, ["Сценарий не найден"]
        
        try:
            result = scenario.validate()
            self.db.commit()
            return result, []
        except Exception as e:
            logger.error(f"Ошибка валидации сценария: {e}")
            return False, [str(e)]
    
    def approve_scenario(self, scenario_id: str, user_id: str, 
                        comments: str = None) -> bool:
        """Утвердить сценарий менеджером (метод из UML Manager)"""
        scenario = self.get_scenario(scenario_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not scenario or not user:
            return False
        
        if user.role != UserRole.MANAGER:
            return False
        
        # Проверяем, утвердил ли уже этот менеджер
        if user not in scenario.approvers:
            scenario.approvers.append(user)
            scenario.is_approved = True
            
            try:
                self.db.commit()
                logger.info(f"Сценарий утвержден: {scenario_id} -> {user_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка утверждения сценария: {e}")
                return False
        return True
    
    def create_state(self, scenario_id: str, name: str, 
                    state_type: str = StateType.IDLE.value,
                    position: List[float] = None) -> Optional[State]:
        """Создать состояние в сценарии"""
        try:
            state = State(
                name=name,
                state_type=state_type,
                scenario_id=scenario_id,
                position_x=position[0] if position else 0.0,
                position_y=position[1] if position else 0.0,
                position_z=position[2] if position else 0.0
            )
            
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
            logger.info(f"Состояние создано: {name} (ID: {state.id})")
            return state
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания состояния: {e}")
            return None
    
    def create_transition(self, source_state_id: str, target_state_id: str,
                         scenario_id: str, condition: str = "",
                         priority: int = 1, name: str = "") -> Optional[Transition]:
        """Создать переход между состояниями"""
        try:
            transition = Transition(
                name=name,
                condition=condition,
                priority=priority,
                source_state_id=source_state_id,
                target_state_id=target_state_id,
                scenario_id=scenario_id
            )
            
            self.db.add(transition)
            self.db.commit()
            self.db.refresh(transition)
            logger.info(f"Переход создан: {source_state_id} -> {target_state_id}")
            return transition
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания перехода: {e}")
            return None
    
    def get_state_graph(self, scenario_id: str) -> Dict[str, Any]:
        """Получить граф состояний сценария для визуализации"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"nodes": [], "edges": []}
        
        return scenario.get_state_graph()
    
    def add_object_3d(self, scenario_id: str, object_3d_id: str) -> bool:
        """Добавить 3D объект в сценарий"""
        scenario = self.get_scenario(scenario_id)
        object_3d = self.db.query(Object3D).filter(Object3D.id == object_3d_id).first()
        
        if not scenario or not object_3d:
            return False
        
        if object_3d not in scenario.objects_3d:
            scenario.objects_3d.append(object_3d)
            try:
                self.db.commit()
                logger.info(f"3D объект добавлен в сценарий: {object_3d_id} -> {scenario_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка добавления 3D объекта: {e}")
                return False
        return True
    
    def create_visual_script(self, scenario_id: str, name: str, 
                           created_by: str) -> Optional[VisualScript]:
        """Создать визуальный скрипт для сценария"""
        try:
            visual_script = VisualScript(
                name=name,
                scenario_id=scenario_id,
                created_by=created_by
            )
            
            self.db.add(visual_script)
            self.db.commit()
            self.db.refresh(visual_script)
            logger.info(f"Визуальный скрипт создан: {name}")
            return visual_script
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания визуального скрипта: {e}")
            return None
    
    def get_scenario_stats(self, scenario_id: str) -> Dict[str, Any]:
        """Получить статистику сценария"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {}
        
        return {
            "states": len(scenario.states),
            "transitions": len(scenario.transitions),
            "objects_3d": len(scenario.objects_3d),
            "is_validated": scenario.is_validated,
            "is_approved": scenario.is_approved,
            "approvers_count": len(scenario.approvers),
            "has_visual_script": scenario.visual_script is not None,
            "test_runs_count": len(scenario.test_runs) if hasattr(scenario, 'test_runs') else 0
        }