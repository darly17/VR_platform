"""
Модели визуального скрипта из UML диаграммы
VisualScript, Node, Connection
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from backend.database import Base
from backend.models.enums import NodeType, ConnectionType


class VisualScript(Base):
    """Класс ВизуальныйСкрипт из UML"""
    __tablename__ = "visual_scripts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительные поля
    description = Column(Text)
    version = Column(String(20), default="1.0.0")
    is_template = Column(Boolean, default=False)
    settings = Column(JSON, default=dict)
    script_metadata = Column("script_metadata", JSON, default=dict)  # Переименовано!
    
    # Связи из UML диаграммы
    # Scenario "1" *-- "0..1" VisualScript : описывается
    scenario = relationship("Scenario", back_populates="visual_script")
    
    # Создатель скрипта
    creator = relationship("User", foreign_keys=[created_by])
    
    # VisualScript "1" *-- "1..*" Node : содержит (композиция)
    nodes = relationship("Node", back_populates="visual_script",
                       cascade="all, delete-orphan")
    
    # VisualScript "1" *-- "0..*" Connection : содержит (композиция)
    connections = relationship("Connection", back_populates="visual_script",
                            cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VisualScript {self.name} ({len(self.nodes)} nodes)>"
    
    def add_node(self, node_type, position, name=""):
        """Добавить узел (метод из UML)"""
        node = Node(
            name=name or f"Node_{node_type}",
            node_type=node_type,
            position_x=position[0],
            position_y=position[1],
            visual_script_id=self.id
        )
        self.nodes.append(node)
        print(f"Узел '{node.name}' добавлен в визуальный скрипт")
        return node
    
    def connect_nodes(self, source_node, target_node, connection_type="execution"):
        """Соединить узлы (метод из UML)"""
        connection = Connection(
            source_node_id=source_node.id if hasattr(source_node, 'id') else source_node,
            target_node_id=target_node.id if hasattr(target_node, 'id') else target_node,
            connection_type=connection_type,
            visual_script_id=self.id
        )
        self.connections.append(connection)
        print(f"Узлы соединены: {source_node.name} -> {target_node.name}")
        return connection
    
    def export_to_code(self, language="python"):
        """Экспортировать в код (метод из UML)"""
        print(f"Экспорт визуального скрипта '{self.name}' в {language}")
        
        # Простая реализация экспорта
        code_lines = []
        code_lines.append(f"# Генерация из визуального скрипта: {self.name}")
        code_lines.append(f"# Язык: {language}")
        code_lines.append("")
        
        # Экспорт узлов
        code_lines.append("# Узлы:")
        for node in self.nodes:
            code_lines.append(f"# - {node.name} ({node.node_type})")
        
        # Экспорт соединений
        code_lines.append("\n# Соединения:")
        for connection in self.connections:
            source_name = next((n.name for n in self.nodes if n.id == connection.source_node_id), "Unknown")
            target_name = next((n.name for n in self.nodes if n.id == connection.target_node_id), "Unknown")
            code_lines.append(f"# {source_name} -> {target_name} ({connection.connection_type})")
        
        code_lines.append("\n# Логика выполнения:")
        code_lines.append("def execute_visual_script():")
        code_lines.append("    # Сгенерированная логика")
        code_lines.append("    pass")
        
        return "\n".join(code_lines)
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "scenario_id": self.scenario_id,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "nodes_count": len(self.nodes),
            "connections_count": len(self.connections),
            "is_template": self.is_template,
            "metadata": self.script_metadata  # Используем переименованное поле
        }
    
    def get_graph_data(self):
        """Получить данные графа для визуализации"""
        nodes_data = []
        edges_data = []
        
        for node in self.nodes:
            nodes_data.append({
                "id": node.id,
                "name": node.name,
                "type": node.node_type,
                "position": {"x": node.position_x, "y": node.position_y},
                "properties": node.properties
            })
        
        for connection in self.connections:
            edges_data.append({
                "id": connection.id,
                "source": connection.source_node_id,
                "target": connection.target_node_id,
                "type": connection.connection_type,
                "data": connection.data
            })
        
        return {"nodes": nodes_data, "edges": edges_data}


class Node(Base):
    """Класс Узел из UML"""
    __tablename__ = "nodes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    node_type = Column(String(50), nullable=False)  # ТипУзла из UML
    position_x = Column(Float, default=0.0)  # Point из UML
    position_y = Column(Float, default=0.0)
    visual_script_id = Column(String(36), ForeignKey("visual_scripts.id"), nullable=False)
    
    # Дополнительные поля
    description = Column(Text)
    properties = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    node_metadata = Column("node_metadata", JSON, default=dict)  # Переименовано!
    
    # Связи из UML диаграммы
    # VisualScript "1" *-- "1..*" Node : содержит
    visual_script = relationship("VisualScript", back_populates="nodes")
    
    # Node "1" o-- "0..*" Connection : исходный узел
    source_connections = relationship("Connection", 
                                    foreign_keys="[Connection.source_node_id]",
                                    back_populates="source_node")
    
    # Node "1" *-- "0..*" Connection : целевой узел
    target_connections = relationship("Connection",
                                    foreign_keys="[Connection.target_node_id]",
                                    back_populates="target_node")
    
    def __repr__(self):
        return f"<Node {self.name} ({self.node_type})>"
    
    def execute(self):
        """Выполнить узел (метод из UML)"""
        print(f"Выполнение узла '{self.name}' ({self.node_type})")
        
        # Логика выполнения в зависимости от типа узла
        if self.node_type == NodeType.EVENT.value:
            print(f"  Событие: {self.properties.get('event_name', 'unnamed')}")
            return True
        
        elif self.node_type == NodeType.ACTION.value:
            print(f"  Действие: {self.properties.get('action', 'none')}")
            return True
        
        elif self.node_type == NodeType.CONDITION.value:
            condition = self.properties.get("condition", "true")
            result = eval(condition, {"__builtins__": {}})
            print(f"  Условие: {condition} = {result}")
            return result
        
        elif self.node_type == NodeType.VARIABLE.value:
            var_name = self.properties.get("name", "unnamed")
            var_value = self.properties.get("value", None)
            print(f"  Переменная: {var_name} = {var_value}")
            return var_value
        
        return False
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
            "position": {"x": self.position_x, "y": self.position_y},
            "visual_script_id": self.visual_script_id,
            "description": self.description,
            "properties": self.properties,
            "source_connections_count": len(self.source_connections),
            "target_connections_count": len(self.target_connections),
            "metadata": self.node_metadata  # Используем переименованное поле
        }
    
    def move(self, new_position):
        """Переместить узел"""
        self.position_x = new_position[0]
        self.position_y = new_position[1]
        return True
    
    def set_property(self, key, value):
        """Установить свойство узла"""
        self.properties[key] = value
        return True


class Connection(Base):
    """Класс Соединение из UML"""
    __tablename__ = "connections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_node_id = Column(String(36), ForeignKey("nodes.id"), nullable=False)
    target_node_id = Column(String(36), ForeignKey("nodes.id"), nullable=False)
    connection_type = Column(String(50), default="execution")  # ТипСоединения из UML
    visual_script_id = Column(String(36), ForeignKey("visual_scripts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Дополнительные поля
    data = Column(JSON, default=dict)  # Данные, передаваемые по соединению
    priority = Column(Integer, default=1)
    is_enabled = Column(Boolean, default=True)
    
    # Связи из UML диаграммы
    visual_script = relationship("VisualScript", back_populates="connections")
    source_node = relationship("Node", foreign_keys=[source_node_id], 
                             back_populates="source_connections")
    target_node = relationship("Node", foreign_keys=[target_node_id],
                             back_populates="target_connections")
    
    def __repr__(self):
        return f"<Connection {self.source_node.name if self.source_node else '?'} -> {self.target_node.name if self.target_node else '?'}>"
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "connection_type": self.connection_type,
            "visual_script_id": self.visual_script_id,
            "data": self.data,
            "priority": self.priority,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def execute(self):
        """Выполнить передачу данных по соединению"""
        if not self.is_enabled:
            return None
        
        print(f"Соединение {self.id}: передача данных от {self.source_node.name} к {self.target_node.name}")
        
        # Если есть данные для передачи
        if self.data:
            return self.data
        
        # Иначе получаем данные из исходного узла
        if self.source_node:
            result = self.source_node.execute()
            return {"value": result}
        
        return None