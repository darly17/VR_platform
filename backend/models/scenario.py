"""
Модели сценария из UML диаграммы
Scenario (реализует IScenario), State, Transition
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from backend.database import Base
from backend.models.enums import StateType

# Таблица для утверждения сценариев менеджерами
scenario_approvals = Table(
    'scenario_approvals',
    Base.metadata,
    Column('scenario_id', String(36), ForeignKey('scenarios.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('approved_at', DateTime(timezone=True), server_default=func.now()),
    Column('comments', Text)
)

# Таблица для связи Scenario - Asset
scenario_assets = Table(
    'scenario_assets',
    Base.metadata,
    Column('scenario_id', String(36), ForeignKey('scenarios.id'), primary_key=True),
    Column('asset_id', String(36), ForeignKey('assets.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)


class Scenario(Base):
    """Класс Сценарий из UML (реализует IScenarioProtocol)"""
    __tablename__ = "scenarios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Статус и флаги
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    version = Column(String(20), default="1.0.0")
    
    # Дополнительные поля
    execution_order = Column(JSON, default=list)  # Порядок выполнения
    variables = Column(JSON, default=dict)        # Переменные сценария
    scenario_metadata = Column("scenario_metadata", JSON, default=dict)  # Переименовано!
    
    # Связи из UML диаграммы
    # Project "1" *-- "1..*" Scenario : содержит
    project = relationship("Project", back_populates="scenarios")
    
    # Создатель сценария
    creator = relationship("User", foreign_keys=[created_by])
    
    # Scenario "1" *-- "1..*" State : включает (композиция)
    states = relationship("State", back_populates="scenario", 
                         cascade="all, delete-orphan")
    
    # Scenario "1" *-- "0..*" Transition : содержит (композиция)
    transitions = relationship("Transition", back_populates="scenario",
                             cascade="all, delete-orphan")
    
    # Scenario "1" o-- "0..*" Object3D : использует
    objects_3d = relationship("Object3D", back_populates="scenario",
                            cascade="all, delete-orphan")
    
    # Scenario "1" *-- "0..1" VisualScript : описывается
    visual_script = relationship("VisualScript", back_populates="scenario",
                               uselist=False, cascade="all, delete-orphan")
    
    # Менеджеры, утвердившие сценарий
    approvers = relationship("User", secondary=scenario_approvals, 
                           back_populates="approved_scenarios")
    
    # Тестовые прогоны этого сценария
    test_runs = relationship("TestRun", back_populates="scenario")
    
    # Активы, используемые в сценарии
    assets_used = relationship("Asset", secondary=scenario_assets,
                             back_populates="scenarios")
    
    def __repr__(self):
        return f"<Scenario {self.name} ({len(self.states)} states)>"
    
    # Реализация методов интерфейса IScenario (из UML)
    def execute(self):
        """Выполнить сценарий (метод из UML)"""
        print(f"Выполнение сценария '{self.name}'...")
        
        if not self.states:
            print("Ошибка: сценарий не содержит состояний")
            return False
        
        # Находим начальное состояние
        start_state = next((s for s in self.states if s.state_type == "start"), None)
        if not start_state:
            start_state = self.states[0]
        
        # Активируем начальное состояние
        start_state.activate()
        
        # Логика выполнения переходов
        current_state = start_state
        execution_path = [current_state.name]
        
        for _ in range(len(self.transitions) * 2):  # Ограничение циклов
            # Находим переходы из текущего состояния
            possible_transitions = [t for t in self.transitions 
                                  if t.source_state_id == current_state.id]
            
            if not possible_transitions:
                break
            
            # Проверяем условия переходов
            executed = False
            for transition in sorted(possible_transitions, key=lambda x: x.priority, reverse=True):
                if transition.check_condition():
                    transition.execute()
                    # Находим целевое состояние
                    target_state = next((s for s in self.states 
                                       if s.id == transition.target_state_id), None)
                    if target_state:
                        current_state.deactivate()
                        target_state.activate()
                        current_state = target_state
                        execution_path.append(current_state.name)
                        executed = True
                        break
            
            if not executed:
                break
        
        print(f"Сценарий '{self.name}' выполнен. Путь: {' -> '.join(execution_path)}")
        return True
    
    def validate(self):
        """Валидировать сценарий (метод из UML)"""
        print(f"Валидация сценария '{self.name}'...")
        
        errors = []
        
        # 1. Проверка наличия состояний
        if not self.states:
            errors.append("Сценарий не содержит состояний")
        
        # 2. Проверка переходов
        for transition in self.transitions:
            # Проверяем, что состояния перехода существуют
            source_exists = any(s.id == transition.source_state_id for s in self.states)
            target_exists = any(s.id == transition.target_state_id for s in self.states)
            
            if not source_exists:
                errors.append(f"Переход {transition.id} ссылается на несуществующее исходное состояние")
            if not target_exists:
                errors.append(f"Переход {transition.id} ссылается на несуществующее целевое состояние")
            
            # Проверка циклических переходов
            if transition.source_state_id == transition.target_state_id:
                errors.append(f"Переход {transition.id} ссылается на само состояние")
        
        # 3. Проверка наличия начального и конечного состояний
        has_start = any(s.state_type == "start" for s in self.states)
        has_end = any(s.state_type == "end" for s in self.states)
        
        if not has_start:
            errors.append("Отсутствует начальное состояние")
        if not has_end:
            errors.append("Отсутствует конечное состояние")
        
        self.is_validated = len(errors) == 0
        
        if errors:
            print(f"Ошибки валидации: {errors}")
            return False
        
        print(f"Сценарий '{self.name}' валиден")
        return True
    
    def add_state(self, name, state_type="idle", position=None):
        """Добавить состояние (метод из UML)"""
        state = State(
            name=name,
            state_type=state_type,
            scenario_id=self.id,
            position_x=position[0] if position else 0,
            position_y=position[1] if position else 0,
            position_z=position[2] if position else 0
        )
        self.states.append(state)
        print(f"Состояние '{name}' добавлено в сценарий")
        return state
    
    def add_transition(self, source_state, target_state, condition="", priority=1):
        """Добавить переход (метод из UML)"""
        transition = Transition(
            source_state_id=source_state.id if hasattr(source_state, 'id') else source_state,
            target_state_id=target_state.id if hasattr(target_state, 'id') else target_state,
            condition=condition,
            priority=priority,
            scenario_id=self.id
        )
        self.transitions.append(transition)
        print(f"Переход добавлен в сценарий")
        return transition
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "is_active": self.is_active,
            "is_validated": self.is_validated,
            "is_approved": self.is_approved,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "states_count": len(self.states),
            "transitions_count": len(self.transitions),
            "objects_count": len(self.objects_3d),
            "has_visual_script": self.visual_script is not None,
            "metadata": self.scenario_metadata  # Используем переименованное поле
        }
    
    def get_state_graph(self):
        """Получить граф состояний для визуализации"""
        nodes = []
        edges = []
        
        for state in self.states:
            nodes.append({
                "id": state.id,
                "name": state.name,
                "type": state.state_type,
                "position": {"x": state.position_x, "y": state.position_y, "z": state.position_z}
            })
        
        for transition in self.transitions:
            edges.append({
                "id": transition.id,
                "source": transition.source_state_id,
                "target": transition.target_state_id,
                "condition": transition.condition,
                "priority": transition.priority
            })
        
        return {"nodes": nodes, "edges": edges}


class State(Base):
    """Класс Состояние из UML"""
    __tablename__ = "states"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    state_type = Column(String(50), default="idle")  # ТипСостояния из UML
    position_x = Column(Float, default=0.0)  # Vector3 из UML
    position_y = Column(Float, default=0.0)
    position_z = Column(Float, default=0.0)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False)
    
    # Дополнительные поля
    description = Column(Text)
    color = Column(String(20), default="#3498db")  # Цвет для визуализации
    size = Column(Float, default=1.0)  # Размер для визуализации
    properties = Column(JSON, default=dict)  # Свойства состояния
    
    # Связи из UML диаграммы
    # Scenario "1" *-- "1..*" State : включает
    scenario = relationship("Scenario", back_populates="states")
    
    # State "1" o-- "0..*" Transition : исходное (агрегация)
    source_transitions = relationship("Transition", 
                                    foreign_keys="[Transition.source_state_id]",
                                    back_populates="source_state")
    
    # State "1" *-- "0..*" Transition : целевое (композиция)
    target_transitions = relationship("Transition",
                                    foreign_keys="[Transition.target_state_id]",
                                    back_populates="target_state")
    
    # Объекты в этом состоянии
    objects = relationship("Object3D", back_populates="current_state")
    
    def __repr__(self):
        return f"<State {self.name} ({self.state_type})>"
    
    def activate(self):
        """Активировать состояние (метод из UML)"""
        print(f"Состояние '{self.name}' активировано")
        return True
    
    def deactivate(self):
        """Деактивировать состояние (метод из UML)"""
        print(f"Состояние '{self.name}' деактивировано")
        return True
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.state_type,
            "position": {"x": self.position_x, "y": self.position_y, "z": self.position_z},
            "scenario_id": self.scenario_id,
            "description": self.description,
            "source_transitions_count": len(self.source_transitions),
            "target_transitions_count": len(self.target_transitions),
            "objects_count": len(self.objects)
        }
    
    def move(self, new_position):
        """Переместить состояние"""
        self.position_x = new_position[0]
        self.position_y = new_position[1]
        self.position_z = new_position[2]
        return True


class Transition(Base):
    """Класс Переход из UML"""
    __tablename__ = "transitions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), default="")
    condition = Column(Text)  # Условие из UML
    priority = Column(Integer, default=1)  # Приоритет из UML
    source_state_id = Column(String(36), ForeignKey("states.id"), nullable=False)
    target_state_id = Column(String(36), ForeignKey("states.id"), nullable=False)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Дополнительные поля
    trigger_type = Column(String(50), default="auto")  # auto, manual, event
    delay_ms = Column(Integer, default=0)  # Задержка перед выполнением
    actions = Column(JSON, default=list)  # Действия при переходе
    
    # Связи из UML диаграммы
    scenario = relationship("Scenario", back_populates="transitions")
    source_state = relationship("State", foreign_keys=[source_state_id], 
                              back_populates="source_transitions")
    target_state = relationship("State", foreign_keys=[target_state_id],
                              back_populates="target_transitions")
    
    def __repr__(self):
        return f"<Transition {self.name or self.id}>"
    
    def check_condition(self):
        """Проверить условие (метод из UML)"""
        if not self.condition:
            return True
        
        # Простая реализация проверки условия
        # В реальной системе здесь была бы полноценная логика
        try:
            # Пример: "variable > 10"
            return eval(self.condition, {"__builtins__": {}})
        except:
            return False
    
    def execute(self):
        """Выполнить переход (метод из UML)"""
        if self.check_condition():
            print(f"Переход {self.id} выполнен: {self.source_state.name} -> {self.target_state.name}")
            
            # Выполняем дополнительные действия
            for action in self.actions:
                print(f"  Выполнение действия: {action}")
            
            return True
        return False
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "condition": self.condition,
            "priority": self.priority,
            "source_state_id": self.source_state_id,
            "target_state_id": self.target_state_id,
            "scenario_id": self.scenario_id,
            "trigger_type": self.trigger_type,
            "delay_ms": self.delay_ms,
            "actions_count": len(self.actions)
        }
    
    def set_condition(self, condition):
        """Установить условие перехода"""
        self.condition = condition
        return True
    
    def add_action(self, action_type, action_data):
        """Добавить действие при переходе"""
        self.actions.append({
            "type": action_type,
            "data": action_data,
            "timestamp": func.now()
        })
        return True