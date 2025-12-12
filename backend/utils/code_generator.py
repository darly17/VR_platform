"""
Утилиты для генерации кода на различных языках программирования
Соответствует UML диаграмме классов (CodeGenerator)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re
import json
from pathlib import Path
from datetime import datetime

from backend.models.visual_script import VisualScript, Node, Connection
from backend.models.scenario import Scenario, State, Transition
from backend.models.enums import NodeType, StateType, ConnectionType, ProgrammingLanguage


class CodeGenerator(ABC):
    """
    Абстрактный класс генератора кода из UML
    Соответствует классу ГенераторКода из UML диаграммы
    """
    
    def __init__(self, language: str):
        self.language = language
        self.templates: Dict[str, str] = {}
        self._load_templates()
    
    @abstractmethod
    def _load_templates(self):
        """Загрузка шаблонов для языка"""
        pass
    
    @abstractmethod
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация кода из визуального скрипта"""
        pass
    
    @abstractmethod
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация кода из сценария"""
        pass
    
    @abstractmethod
    def check_syntax(self, code: str) -> bool:
        """Проверка синтаксиса кода"""
        pass
    
    def generate_header(self, source_type: str, name: str, **kwargs) -> str:
        """Генерация заголовка файла"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.language == ProgrammingLanguage.PYTHON.value:
            return f'''"""
Генерация кода из {source_type}: {name}
Язык: {self.language}
Дата генерации: {timestamp}
"""
'''
        elif self.language == ProgrammingLanguage.CSHARP.value:
            return f'''// Генерация кода из {source_type}: {name}
// Язык: {self.language}
// Дата генерации: {timestamp}
'''
        elif self.language == ProgrammingLanguage.CPP.value:
            return f'''// Генерация кода из {source_type}: {name}
// Язык: {self.language}
// Дата генерации: {timestamp}
'''
        else:
            return f'# Генерация кода из {source_type}: {name}\n'
    
    def sanitize_name(self, name: str) -> str:
        """Санкция имени для использования в коде"""
        # Заменяем пробелы и специальные символы
        sanitized = re.sub(r'[^\w]', '_', name)
        # Удаляем множественные подчеркивания
        sanitized = re.sub(r'_+', '_', sanitized)
        # Удаляем подчеркивания в начале и конце
        sanitized = sanitized.strip('_')
        # Делаем первую букву заглавной для классов
        if sanitized:
            sanitized = sanitized[0].upper() + sanitized[1:]
        return sanitized if sanitized else 'GeneratedCode'
    
    def get_indentation(self, level: int = 1) -> str:
        """Получение отступа для языка"""
        if self.language == ProgrammingLanguage.PYTHON.value:
            return '    ' * level
        elif self.language in [ProgrammingLanguage.CSHARP.value, ProgrammingLanguage.CPP.value]:
            return '    ' * level
        else:
            return '  ' * level


class PythonGenerator(CodeGenerator):
    """Генератор Python кода"""
    
    def _load_templates(self):
        """Загрузка шаблонов для Python"""
        self.templates = {
            'class': "class {class_name}:\n{indent}\"\"\"{docstring}\"\"\"\n\n{methods}",
            'method': "{indent}def {method_name}(self{params}):\n{indent2}\"\"\"{docstring}\"\"\"\n{body}",
            'variable': "{indent}self.{var_name} = {var_value}",
            'if': "{indent}if {condition}:\n{body}",
            'for': "{indent}for {var} in {iterable}:\n{body}",
            'print': '{indent}print("{message}")',
            'return': '{indent}return {value}',
            'import': 'import {module}',
            'from_import': 'from {module} import {names}'
        }
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация Python кода из визуального скрипта"""
        class_name = self.sanitize_name(visual_script.name)
        indent = self.get_indentation(1)
        indent2 = self.get_indentation(2)
        
        # Генерация заголовка
        code = self.generate_header("визуального скрипта", visual_script.name)
        
        # Импорты
        code += "\nimport json\nimport time\nfrom typing import Dict, List, Any, Optional\n\n"
        
        # Класс
        code += f"class {class_name}:\n"
        code += f'{indent}"""{visual_script.description or "Генерация из визуального скрипта"}"""\n\n'
        
        # Конструктор
        code += f'{indent}def __init__(self):\n'
        code += f'{indent2}"""Инициализация сгенерированного скрипта"""\n'
        code += f'{indent2}self.variables: Dict[str, Any] = {{}}\n'
        code += f'{indent2}self.execution_log: List[str] = []\n'
        code += f'{indent2}self.nodes_data = {self._get_nodes_data(visual_script)}\n'
        code += f'{indent2}self.connections_data = {self._get_connections_data(visual_script)}\n'
        
        # Инициализация переменных из узлов
        variable_nodes = [n for n in visual_script.nodes if n.node_type == NodeType.VARIABLE.value]
        for node in variable_nodes:
            var_name = node.properties.get('name', f'var_{node.id[:8]}')
            var_value = node.properties.get('value', 'None')
            code += f'{indent2}self.variables["{var_name}"] = {var_value}\n'
        
        code += '\n'
        
        # Методы для узлов
        for node in visual_script.nodes:
            if node.node_type == NodeType.EVENT.value:
                code += self._generate_event_node_method(node, indent)
            elif node.node_type == NodeType.ACTION.value:
                code += self._generate_action_node_method(node, indent)
            elif node.node_type == NodeType.FUNCTION.value:
                code += self._generate_function_node_method(node, indent)
        
        # Метод выполнения
        code += self._generate_execution_method(visual_script, indent)
        
        # Метод запуска
        code += self._generate_run_method(indent)
        
        return code
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация Python кода из сценария"""
        class_name = self.sanitize_name(scenario.name)
        indent = self.get_indentation(1)
        indent2 = self.get_indentation(2)
        
        # Генерация заголовка
        code = self.generate_header("сценария", scenario.name)
        
        # Импорты
        code += "\nimport json\nimport time\nfrom enum import Enum\nfrom typing import Dict, List, Any, Optional\nfrom dataclasses import dataclass\n\n"
        
        # Перечисление типов состояний
        code += "class StateType(Enum):\n"
        for state in scenario.states:
            state_type_enum = state.state_type.upper().replace(' ', '_')
            code += f'{indent}{state_type_enum} = "{state.state_type}"\n'
        code += '\n'
        
        # Класс состояния
        code += "@dataclass\n"
        code += "class ScenarioState:\n"
        code += f'{indent}"""Состояние сценария"""\n'
        code += f'{indent}id: str\n'
        code += f'{indent}name: str\n'
        code += f'{indent}type: StateType\n'
        code += f'{indent}position: List[float]\n'
        code += f'{indent}description: Optional[str] = None\n'
        code += f'{indent}properties: Dict[str, Any] = None\n\n'
        
        # Класс перехода
        code += "@dataclass\n"
        code += "class ScenarioTransition:\n"
        code += f'{indent}"""Переход между состояниями"""\n'
        code += f'{indent}id: str\n'
        code += f'{indent}source_state_id: str\n'
        code += f'{indent}target_state_id: str\n'
        code += f'{indent}condition: str\n'
        code += f'{indent}priority: int\n'
        code += f'{indent}actions: List[Dict[str, Any]] = None\n\n'
        
        # Основной класс сценария
        code += f"class {class_name}:\n"
        code += f'{indent}"""{scenario.description or "Сгенерированный сценарий VR/AR"}"""\n\n'
        
        # Конструктор
        code += f'{indent}def __init__(self):\n'
        code += f'{indent2}"""Инициализация сценария"""\n'
        code += f'{indent2}self.name = "{scenario.name}"\n'
        code += f'{indent2}self.description = "{scenario.description or ""}"\n'
        code += f'{indent2}self.states: Dict[str, ScenarioState] = {{}}\n'
        code += f'{indent2}self.transitions: Dict[str, ScenarioTransition] = {{}}\n'
        code += f'{indent2}self.current_state: Optional[ScenarioState] = None\n'
        code += f'{indent2}self.execution_history: List[str] = []\n'
        code += f'{indent2}self.variables: Dict[str, Any] = {json.dumps(scenario.variables, ensure_ascii=False)}\n\n'
        
        # Инициализация состояний и переходов
        code += f'{indent2}# Инициализация состояний\n'
        for state in scenario.states:
            code += f'{indent2}self.states["{state.id}"] = ScenarioState(\n'
            code += f'{indent2}    id="{state.id}",\n'
            code += f'{indent2}    name="{state.name}",\n'
            code += f'{indent2}    type=StateType.{state.state_type.upper().replace(" ", "_")},\n'
            code += f'{indent2}    position=[{state.position_x}, {state.position_y}, {state.position_z}],\n'
            code += f'{indent2}    description="{state.description or ""}",\n'
            code += f'{indent2}    properties={json.dumps(state.properties, ensure_ascii=False)}\n'
            code += f'{indent2})\n'
        
        code += f'\n{indent2}# Инициализация переходов\n'
        for transition in scenario.transitions:
            code += f'{indent2}self.transitions["{transition.id}"] = ScenarioTransition(\n'
            code += f'{indent2}    id="{transition.id}",\n'
            code += f'{indent2}    source_state_id="{transition.source_state_id}",\n'
            code += f'{indent2}    target_state_id="{transition.target_state_id}",\n'
            code += f'{indent2}    condition="{transition.condition or ""}",\n'
            code += f'{indent2}    priority={transition.priority},\n'
            code += f'{indent2}    actions={json.dumps(transition.actions, ensure_ascii=False)}\n'
            code += f'{indent2})\n'
        
        code += '\n'
        
        # Метод запуска сценария
        code += f'{indent}def start(self):\n'
        code += f'{indent2}"""Запуск сценария"""\n'
        
        # Находим начальное состояние
        start_states = [s for s in scenario.states if s.state_type == StateType.START.value]
        if start_states:
            start_state = start_states[0]
            code += f'{indent2}# Начальное состояние\n'
            code += f'{indent2}self.current_state = self.states["{start_state.id}"]\n'
            code += f'{indent2}self.execution_history.append(f"Старт: {{self.current_state.name}}")\n'
            code += f'{indent2}print(f"Сценарий начат. Текущее состояние: {{self.current_state.name}}")\n'
        else:
            code += f'{indent2}# Начальное состояние не найдено, используем первое\n'
            code += f'{indent2}if self.states:\n'
            code += f'{indent2}    first_state_id = list(self.states.keys())[0]\n'
            code += f'{indent2}    self.current_state = self.states[first_state_id]\n'
            code += f'{indent2}    self.execution_history.append(f"Старт: {{self.current_state.name}}")\n'
            code += f'{indent2}    print(f"Сценарий начат. Текущее состояние: {{self.current_state.name}}")\n'
        code += f'{indent2}return self.current_state\n\n'
        
        # Метод выполнения перехода
        code += f'{indent}def execute_transition(self, transition_id: str) -> bool:\n'
        code += f'{indent2}"""Выполнение перехода"""\n'
        code += f'{indent2}transition = self.transitions.get(transition_id)\n'
        code += f'{indent2}if not transition:\n'
        code += f'{indent2}    print(f"Переход {{transition_id}} не найден")\n'
        code += f'{indent2}    return False\n'
        code += f'\n{indent2}# Проверка условия\n'
        code += f'{indent2}if self._check_condition(transition.condition):\n'
        code += f'{indent2}    # Получаем целевое состояние\n'
        code += f'{indent2}    target_state = self.states.get(transition.target_state_id)\n'
        code += f'{indent2}    if target_state:\n'
        code += f'{indent2}        self.current_state = target_state\n'
        code += f'{indent2}        self.execution_history.append(f"Переход: {{transition.id}} -> {{target_state.name}}")\n'
        code += f'{indent2}        print(f"Переход выполнен: {{transition.id}}")\n'
        code += f'{indent2}        # Выполняем действия перехода\n'
        code += f'{indent2}        self._execute_transition_actions(transition)\n'
        code += f'{indent2}        return True\n'
        code += f'{indent2}else:\n'
        code += f'{indent2}    print(f"Условие перехода не выполнено: {{transition.condition}}")\n'
        code += f'{indent2}    return False\n\n'
        
        # Метод проверки условия
        code += f'{indent}def _check_condition(self, condition: str) -> bool:\n'
        code += f'{indent2}"""Проверка условия перехода"""\n'
        code += f'{indent2}if not condition or condition.strip() == "":\n'
        code += f'{indent2}    return True\n'
        code += f'{indent2}try:\n'
        code += f'{indent2}    # Безопасная оценка условия\n'
        code += f'{indent2}    return eval(condition, {{"__builtins__": {{}}}}, self.variables)\n'
        code += f'{indent2}except Exception as e:\n'
        code += f'{indent2}    print(f"Ошибка оценки условия {{condition}}: {{e}}")\n'
        code += f'{indent2}    return False\n\n'
        
        # Метод выполнения действий перехода
        code += f'{indent}def _execute_transition_actions(self, transition: ScenarioTransition):\n'
        code += f'{indent2}"""Выполнение действий перехода"""\n'
        code += f'{indent2}if transition.actions:\n'
        code += f'{indent2}    for action in transition.actions:\n'
        code += f'{indent2}        action_type = action.get("type")\n'
        code += f'{indent2}        action_data = action.get("data", {{}})\n'
        code += f'{indent2}        print(f"Выполнение действия: {{action_type}} {{action_data}}")\n\n'
        
        # Метод выполнения сценария
        code += f'{indent}def run(self, max_iterations: int = 100):\n'
        code += f'{indent2}"""Запуск выполнения сценария"""\n'
        code += f'{indent2}self.start()\n'
        code += f'{indent2}iteration = 0\n'
        code += f'{indent2}while iteration < max_iterations:\n'
        code += f'{indent2}    iteration += 1\n'
        code += f'{indent2}    if not self.current_state:\n'
        code += f'{indent2}        break\n'
        code += f'\n{indent2}    # Находим возможные переходы из текущего состояния\n'
        code += f'{indent2}    possible_transitions = [\n'
        code += f'{indent2}        t for t in self.transitions.values()\n'
        code += f'{indent2}        if t.source_state_id == self.current_state.id\n'
        code += f'{indent2}    ]\n'
        code += f'\n{indent2}    # Сортируем по приоритету\n'
        code += f'{indent2}    possible_transitions.sort(key=lambda x: x.priority, reverse=True)\n'
        code += f'\n{indent2}    executed = False\n'
        code += f'{indent2}    for transition in possible_transitions:\n'
        code += f'{indent2}        if self.execute_transition(transition.id):\n'
        code += f'{indent2}            executed = True\n'
        code += f'{indent2}            break\n'
        code += f'\n{indent2}    if not executed:\n'
        code += f'{indent2}        print(f"Нет доступных переходов из состояния {{self.current_state.name}}")\n'
        code += f'{indent2}        break\n'
        code += f'\n{indent2}    # Проверяем, достигли ли конечного состояния\n'
        code += f'{indent2}    if self.current_state.type == StateType.END:\n'
        code += f'{indent2}        print(f"Достигнуто конечное состояние: {{self.current_state.name}}")\n'
        code += f'{indent2}        break\n'
        code += f'\n{indent2}print("\\nИстория выполнения:")\n'
        code += f'{indent2}for i, step in enumerate(self.execution_history, 1):\n'
        code += f'{indent2}    print(f"  {{i}}. {{step}}")\n\n'
        
        # Статический метод для запуска
        code += f'{indent}@staticmethod\n'
        code += f'{indent}def execute():\n'
        code += f'{indent2}"""Точка входа для выполнения сценария"""\n'
        code += f'{indent2}scenario = {class_name}()\n'
        code += f'{indent2}scenario.run()\n'
        code += f'{indent2}return scenario\n\n'
        
        # Main блок
        code += 'if __name__ == "__main__":\n'
        code += f'{indent}{class_name}.execute()\n'
        
        return code
    
    def check_syntax(self, code: str) -> bool:
        """Проверка синтаксиса Python кода"""
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _get_nodes_data(self, visual_script: VisualScript) -> str:
        """Получение данных узлов в формате Python"""
        nodes_data = []
        for node in visual_script.nodes:
            node_data = {
                'id': node.id,
                'name': node.name,
                'type': node.node_type,
                'position': {'x': node.position_x, 'y': node.position_y},
                'properties': node.properties
            }
            nodes_data.append(node_data)
        return json.dumps(nodes_data, ensure_ascii=False, indent=2)
    
    def _get_connections_data(self, visual_script: VisualScript) -> str:
        """Получение данных соединений в формате Python"""
        connections_data = []
        for conn in visual_script.connections:
            conn_data = {
                'id': conn.id,
                'source': conn.source_node_id,
                'target': conn.target_node_id,
                'type': conn.connection_type,
                'data': conn.data
            }
            connections_data.append(conn_data)
        return json.dumps(connections_data, ensure_ascii=False, indent=2)
    
    def _generate_event_node_method(self, node: Node, indent: str) -> str:
        """Генерация метода для узла-события"""
        method_name = f"handle_{node.name.lower().replace(' ', '_')}"
        event_name = node.properties.get('event_name', 'unnamed_event')
        
        method = f'{indent}def {method_name}(self, data=None):\n'
        method += f'{indent}    """Обработка события: {node.name}"""\n'
        method += f'{indent}    self.execution_log.append(f"Событие: {event_name} с данными: {{data}}")\n'
        method += f'{indent}    print(f"Событие {{self.nodes_data[...]}} обработано")\n'
        method += f'{indent}    return True\n\n'
        
        return method
    
    def _generate_action_node_method(self, node: Node, indent: str) -> str:
        """Генерация метода для узла-действия"""
        method_name = f"execute_{node.name.lower().replace(' ', '_')}"
        action_type = node.properties.get('action', 'unknown_action')
        
        method = f'{indent}def {method_name}(self, params=None):\n'
        method += f'{indent}    """Выполнение действия: {node.name}"""\n'
        method += f'{indent}    self.execution_log.append(f"Действие: {action_type}")\n'
        method += f'{indent}    print(f"Действие {{self.nodes_data[...]}} выполнено")\n'
        
        if action_type == 'set_variable':
            var_name = node.properties.get('variable_name', '')
            var_value = node.properties.get('value', 'None')
            method += f'{indent}    self.variables["{var_name}"] = {var_value}\n'
        elif action_type == 'log_message':
            message = node.properties.get('message', '')
            method += f'{indent}    print("{message}")\n'
        
        method += f'{indent}    return True\n\n'
        
        return method
    
    def _generate_function_node_method(self, node: Node, indent: str) -> str:
        """Генерация метода для узла-функции"""
        method_name = node.properties.get('function_name', f'func_{node.id[:8]}')
        
        method = f'{indent}def {method_name}(self, *args, **kwargs):\n'
        method += f'{indent}    """Функция: {node.name}"""\n'
        method += f'{indent}    self.execution_log.append(f"Функция: {node.name} вызвана")\n'
        
        # Простая реализация на основе свойств
        return_expr = node.properties.get('return_expression', 'None')
        method += f'{indent}    return {return_expr}\n\n'
        
        return method
    
    def _generate_execution_method(self, visual_script: VisualScript, indent: str) -> str:
        """Генерация метода выполнения логики"""
        method = f'{indent}def execute_logic(self):\n'
        method += f'{indent}    """Выполнение логики визуального скрипта"""\n'
        method += f'{indent}    self.execution_log.append("Начало выполнения логики")\n'
        method += f'{indent}    print("Выполнение логики визуального скрипта...")\n\n'
        
        # Простая логика выполнения на основе соединений
        if visual_script.connections:
            method += f'{indent}    # Логика на основе соединений\n'
            for conn in visual_script.connections[:5]:  # Ограничиваем для примера
                source_node = next((n for n in visual_script.nodes if n.id == conn.source_node_id), None)
                target_node = next((n for n in visual_script.nodes if n.id == conn.target_node_id), None)
                
                if source_node and target_node:
                    method += f'{indent}    # {source_node.name} -> {target_node.name}\n'
        
        method += f'{indent}    self.execution_log.append("Логика выполнена")\n'
        method += f'{indent}    return True\n\n'
        
        return method
    
    def _generate_run_method(self, indent: str) -> str:
        """Генерация метода запуска"""
        method = f'{indent}def run(self):\n'
        method += f'{indent}    """Запуск выполнения скрипта"""\n'
        method += f'{indent}    print("Запуск сгенерированного скрипта...")\n'
        method += f'{indent}    self.execute_logic()\n'
        method += f'{indent}    print("\\nИстория выполнения:")\n'
        method += f'{indent}    for i, log in enumerate(self.execution_log, 1):\n'
        method += f'{indent}        print(f"  {{i}}. {{log}}")\n'
        method += f'{indent}    print("Выполнение завершено")\n'
        
        return method


class CSharpGenerator(CodeGenerator):
    """Генератор C# кода"""
    
    def _load_templates(self):
        """Загрузка шаблонов для C#"""
        self.templates = {
            'namespace': "namespace {namespace}\n{{\n{content}\n}}",
            'class': "{access} class {class_name}\n{{\n{members}\n}}",
            'method': "{access} {return_type} {method_name}({params})\n{indent}{{\n{body}\n{indent}}}",
            'property': "{access} {type} {name} {{ get; set; }}",
            'field': "{access} {type} {name};",
            'if': "if ({condition})\n{indent}{{\n{body}\n{indent}}}",
            'for': "for (int i = 0; i < {count}; i++)\n{indent}{{\n{body}\n{indent}}}",
            'foreach': "foreach (var {item} in {collection})\n{indent}{{\n{body}\n{indent}}}",
            'console_write': 'Console.WriteLine("{message}");'
        }
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация C# кода из визуального скрипта"""
        class_name = self.sanitize_name(visual_script.name)
        namespace = "VRAR.GeneratedCode"
        indent = self.get_indentation(1)
        
        # Генерация заголовка
        code = self.generate_header("визуального скрипта", visual_script.name)
        
        # Namespace и using
        code += "using System;\n"
        code += "using System.Collections.Generic;\n"
        code += "using System.Text.Json;\n\n"
        
        # Namespace
        code += f"namespace {namespace}\n"
        code += "{\n"
        
        # Класс
        code += f'{indent}/// <summary>\n'
        code += f'{indent}/// {visual_script.description or "Генерация из визуального скрипта"}\n'
        code += f'{indent}/// </summary>\n'
        code += f'{indent}public class {class_name}\n'
        code += f'{indent}{{\n'
        
        # Поля
        code += f'{indent}    // Поля\n'
        code += f'{indent}    private Dictionary<string, object> variables = new Dictionary<string, object>();\n'
        code += f'{indent}    private List<string> executionLog = new List<string>();\n'
        code += f'{indent}    private List<Dictionary<string, object>> nodesData;\n'
        code += f'{indent}    private List<Dictionary<string, object>> connectionsData;\n\n'
        
        # Конструктор
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Инициализация сгенерированного скрипта\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public {class_name}()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        // Инициализация данных узлов\n'
        code += f'{indent}        nodesData = new List<Dictionary<string, object>>\n'
        code += f'{indent}        {{\n'
        
        for node in visual_script.nodes[:3]:  # Ограничиваем для примера
            code += f'{indent}            new Dictionary<string, object>\n'
            code += f'{indent}            {{\n'
            code += f'{indent}                {{ "id", "{node.id}" }},\n'
            code += f'{indent}                {{ "name", "{node.name}" }},\n'
            code += f'{indent}                {{ "type", "{node.node_type}" }}\n'
            code += f'{indent}            }},\n'
        
        code += f'{indent}        }};\n\n'
        
        code += f'{indent}        // Инициализация данных соединений\n'
        code += f'{indent}        connectionsData = new List<Dictionary<string, object>>();\n'
        code += f'{indent}    }}\n\n'
        
        # Метод выполнения логики
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Выполнение логики визуального скрипта\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public void ExecuteLogic()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        executionLog.Add("Начало выполнения логики");\n'
        code += f'{indent}        Console.WriteLine("Выполнение логики визуального скрипта...");\n\n'
        
        # Простая логика
        if visual_script.connections:
            code += f'{indent}        // Логика на основе соединений\n'
            for conn in visual_script.connections[:3]:
                source_node = next((n for n in visual_script.nodes if n.id == conn.source_node_id), None)
                target_node = next((n for n in visual_script.nodes if n.id == conn.target_node_id), None)
                
                if source_node and target_node:
                    code += f'{indent}        // {source_node.name} -> {target_node.name}\n'
        
        code += f'{indent}        executionLog.Add("Логика выполнена");\n'
        code += f'{indent}    }}\n\n'
        
        # Метод запуска
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Запуск выполнения скрипта\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public void Run()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        Console.WriteLine("Запуск сгенерированного скрипта...");\n'
        code += f'{indent}        ExecuteLogic();\n'
        code += f'{indent}        Console.WriteLine("\\nИстория выполнения:");\n'
        code += f'{indent}        for (int i = 0; i < executionLog.Count; i++)\n'
        code += f'{indent}        {{\n'
        code += f'{indent}            Console.WriteLine($"  {{i + 1}}. {{executionLog[i]}}");\n'
        code += f'{indent}        }}\n'
        code += f'{indent}        Console.WriteLine("Выполнение завершено");\n'
        code += f'{indent}    }}\n'
        
        # Статический метод для запуска
        code += f'\n{indent}    /// <summary>\n'
        code += f'{indent}    /// Точка входа для выполнения скрипта\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public static void Execute()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        var script = new {class_name}();\n'
        code += f'{indent}        script.Run();\n'
        code += f'{indent}    }}\n'
        
        code += f'{indent}}}\n'
        code += "}\n\n"
        
        # Main метод
        code += "class Program\n"
        code += "{\n"
        code += f'{indent}static void Main(string[] args)\n'
        code += f'{indent}{{\n'
        code += f'{indent}    {namespace}.{class_name}.Execute();\n'
        code += f'{indent}}}\n'
        code += "}\n"
        
        return code
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация C# кода из сценария"""
        class_name = self.sanitize_name(scenario.name)
        namespace = "VRAR.GeneratedScenarios"
        indent = self.get_indentation(1)
        
        # Генерация заголовка
        code = self.generate_header("сценария", scenario.name)
        
        # Namespace и using
        code += "using System;\n"
        code += "using System.Collections.Generic;\n"
        code += "using System.Linq;\n\n"
        
        # Namespace
        code += f"namespace {namespace}\n"
        code += "{\n"
        
        # Перечисление типов состояний
        code += f'{indent}/// <summary>\n'
        code += f'{indent}/// Типы состояний сценария\n'
        code += f'{indent}/// </summary>\n'
        code += f'{indent}public enum StateType\n'
        code += f'{indent}{{\n'
        for state in scenario.states:
            state_type_enum = state.state_type.Replace(" ", "").Replace("-", "")
            code += f'{indent}    {state_type_enum},\n'
        code += f'{indent}}}\n\n'
        
        # Класс состояния
        code += f'{indent}/// <summary>\n'
        code += f'{indent}/// Состояние сценария\n'
        code += f'{indent}/// </summary>\n'
        code += f'{indent}public class ScenarioState\n'
        code += f'{indent}{{\n'
        code += f'{indent}    public string Id {{ get; set; }}\n'
        code += f'{indent}    public string Name {{ get; set; }}\n'
        code += f'{indent}    public StateType Type {{ get; set; }}\n'
        code += f'{indent}    public float[] Position {{ get; set; }} = new float[3];\n'
        code += f'{indent}    public string Description {{ get; set; }}\n'
        code += f'{indent}    public Dictionary<string, object> Properties {{ get; set; }}\n'
        code += f'{indent}}}\n\n'
        
        # Класс перехода
        code += f'{indent}/// <summary>\n'
        code += f'{indent}/// Переход между состояниями\n'
        code += f'{indent}/// </summary>\n'
        code += f'{indent}public class ScenarioTransition\n'
        code += f'{indent}{{\n'
        code += f'{indent}    public string Id {{ get; set; }}\n'
        code += f'{indent}    public string SourceStateId {{ get; set; }}\n'
        code += f'{indent}    public string TargetStateId {{ get; set; }}\n'
        code += f'{indent}    public string Condition {{ get; set; }}\n'
        code += f'{indent}    public int Priority {{ get; set; }}\n'
        code += f'{indent}    public List<Dictionary<string, object>> Actions {{ get; set; }}\n'
        code += f'{indent}}}\n\n'
        
        # Основной класс сценария
        code += f'{indent}/// <summary>\n'
        code += f'{indent}/// {scenario.description or "Сгенерированный сценарий VR/AR"}\n'
        code += f'{indent}/// </summary>\n'
        code += f'{indent}public class {class_name}\n'
        code += f'{indent}{{\n'
        
        # Поля
        code += f'{indent}    private Dictionary<string, ScenarioState> states = new Dictionary<string, ScenarioState>();\n'
        code += f'{indent}    private Dictionary<string, ScenarioTransition> transitions = new Dictionary<string, ScenarioTransition>();\n'
        code += f'{indent}    private ScenarioState currentState;\n'
        code += f'{indent}    private List<string> executionHistory = new List<string>();\n'
        code += f'{indent}    private Dictionary<string, object> variables = new Dictionary<string, object>();\n\n'
        
        # Конструктор
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Инициализация сценария\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public {class_name}()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        InitializeStates();\n'
        code += f'{indent}        InitializeTransitions();\n'
        code += f'{indent}    }}\n\n'
        
        # Метод инициализации состояний
        code += f'{indent}    private void InitializeStates()\n'
        code += f'{indent}    {{\n'
        for state in scenario.states:
            code += f'{indent}        states["{state.id}"] = new ScenarioState\n'
            code += f'{indent}        {{\n'
            code += f'{indent}            Id = "{state.id}",\n'
            code += f'{indent}            Name = "{state.name}",\n'
            state_type_enum = state.state_type.Replace(" ", "").Replace("-", "")
            code += f'{indent}            Type = StateType.{state_type_enum},\n'
            code += f'{indent}            Position = new float[] {{ {(float)state.position_x}f, {(float)state.position_y}f, {(float)state.position_z}f }},\n'
            code += f'{indent}            Description = "{state.description or ""}",\n'
            code += f'{indent}            Properties = new Dictionary<string, object>()\n'
            code += f'{indent}        }};\n'
        code += f'{indent}    }}\n\n'
        
        # Метод инициализации переходов
        code += f'{indent}    private void InitializeTransitions()\n'
        code += f'{indent}    {{\n'
        for transition in scenario.transitions:
            code += f'{indent}        transitions["{transition.id}"] = new ScenarioTransition\n'
            code += f'{indent}        {{\n'
            code += f'{indent}            Id = "{transition.id}",\n'
            code += f'{indent}            SourceStateId = "{transition.source_state_id}",\n'
            code += f'{indent}            TargetStateId = "{transition.target_state_id}",\n'
            code += f'{indent}            Condition = "{transition.condition or ""}",\n'
            code += f'{indent}            Priority = {transition.priority},\n'
            code += f'{indent}            Actions = new List<Dictionary<string, object>>()\n'
            code += f'{indent}        }};\n'
        code += f'{indent}    }}\n\n'
        
        # Метод запуска
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Запуск сценария\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public void Run()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        Console.WriteLine("Запуск сценария...");\n'
        code += f'{indent}        // Логика выполнения сценария\n'
        code += f'{indent}        Console.WriteLine("Сценарий завершен");\n'
        code += f'{indent}    }}\n\n'
        
        # Статический метод для запуска
        code += f'{indent}    /// <summary>\n'
        code += f'{indent}    /// Точка входа для выполнения сценария\n'
        code += f'{indent}    /// </summary>\n'
        code += f'{indent}    public static void Execute()\n'
        code += f'{indent}    {{\n'
        code += f'{indent}        var scenario = new {class_name}();\n'
        code += f'{indent}        scenario.Run();\n'
        code += f'{indent}    }}\n'
        
        code += f'{indent}}}\n'
        code += "}\n\n"
        
        # Main класс
        code += "class Program\n"
        code += "{\n"
        code += f'{indent}static void Main(string[] args)\n'
        code += f'{indent}{{\n'
        code += f'{indent}    {namespace}.{class_name}.Execute();\n'
        code += f'{indent}}}\n'
        code += "}\n"
        
        return code
    
    def check_syntax(self, code: str) -> bool:
        """Проверка синтаксиса C# кода (базовая проверка)"""
        # Базовая проверка структуры C#
        required_patterns = [
            r'using\s+System;',
            r'namespace\s+\w+',
            r'class\s+\w+',
            r'public\s+',
            r'static\s+void\s+Main'
        ]
        
        for pattern in required_patterns:
            if not re.search(pattern, code, re.IGNORECASE):
                return False
        
        return True


class CppGenerator(CodeGenerator):
    """Генератор C++ кода"""
    
    def _load_templates(self):
        """Загрузка шаблонов для C++"""
        self.templates = {
            'include': '#include <{header}>',
            'namespace': 'namespace {namespace}\n{{\n{content}\n}}',
            'class': 'class {class_name}\n{{\n{access}:\n{members}\n}};',
            'method': '{return_type} {method_name}({params})\n{{\n{body}\n}}',
            'main': 'int main()\n{{\n{body}\nreturn 0;\n}}',
            'cout': 'std::cout << "{message}" << std::endl;',
            'if': 'if ({condition})\n{{\n{body}\n}}',
            'for': 'for (int i = 0; i < {count}; i++)\n{{\n{body}\n}}'
        }
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация C++ кода из визуального скрипта"""
        class_name = self.sanitize_name(visual_script.name)
        
        # Генерация заголовка
        code = self.generate_header("визуального скрипта", visual_script.name)
        
        # Include
        code += "#include <iostream>\n"
        code += "#include <vector>\n"
        code += "#include <string>\n"
        code += "#include <map>\n\n"
        
        # Using
        code += "using namespace std;\n\n"
        
        # Класс
        code += f"class {class_name}\n"
        code += "{\n"
        code += "private:\n"
        code += "    map<string, void*> variables;\n"
        code += "    vector<string> executionLog;\n\n"
        
        code += "public:\n"
        
        # Конструктор
        code += f"    {class_name}()\n"
        code += "    {\n"
        code += '        executionLog.push_back("Объект создан");\n'
        code += "    }\n\n"
        
        # Деструктор
        code += f"    ~{class_name}()\n"
        code += "    {\n"
        code += '        executionLog.push_back("Объект уничтожен");\n'
        code += "    }\n\n"
        
        # Метод выполнения
        code += "    void execute()\n"
        code += "    {\n"
        code += '        executionLog.push_back("Начало выполнения");\n'
        code += '        cout << "Выполнение визуального скрипта..." << endl;\n'
        
        # Простая логика
        if visual_script.connections:
            code += "        // Логика на основе соединений\n"
            for conn in visual_script.connections[:3]:
                source_node = next((n for n in visual_script.nodes if n.id == conn.source_node_id), None)
                target_node = next((n for n in visual_script.nodes if n.id == conn.target_node_id), None)
                
                if source_node and target_node:
                    code += f'        // {source_node.name} -> {target_node.name}\n'
        
        code += '        executionLog.push_back("Выполнение завершено");\n'
        code += "    }\n\n"
        
        # Метод вывода логов
        code += "    void printLogs()\n"
        code += "    {\n"
        code += '        cout << "\\nИстория выполнения:" << endl;\n'
        code += "        for (size_t i = 0; i < executionLog.size(); i++)\n"
        code += "        {\n"
        code += '            cout << "  " << i + 1 << ". " << executionLog[i] << endl;\n'
        code += "        }\n"
        code += "    }\n"
        
        code += "};\n\n"
        
        # Main функция
        code += "int main()\n"
        code += "{\n"
        code += f'    cout << "Запуск сгенерированного C++ кода..." << endl;\n'
        code += f"    {class_name} script;\n"
        code += "    script.execute();\n"
        code += "    script.printLogs();\n"
        code += '    cout << "Программа завершена" << endl;\n'
        code += "    return 0;\n"
        code += "}\n"
        
        return code
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация C++ кода из сценария"""
        class_name = self.sanitize_name(scenario.name)
        
        # Генерация заголовка
        code = self.generate_header("сценария", scenario.name)
        
        # Include
        code += "#include <iostream>\n"
        code += "#include <vector>\n"
        code += "#include <string>\n"
        code += "#include <map>\n"
        code += "#include <algorithm>\n\n"
        
        # Using
        code += "using namespace std;\n\n"
        
        # Перечисление типов состояний
        code += "enum class StateType\n"
        code += "{\n"
        for state in scenario.states:
            state_type_enum = state.state_type.upper().replace(' ', '_').replace('-', '_')
            code += f"    {state_type_enum},\n"
        code += "};\n\n"
        
        # Структура состояния
        code += "struct ScenarioState\n"
        code += "{\n"
        code += "    string id;\n"
        code += "    string name;\n"
        code += "    StateType type;\n"
        code += "    float position[3];\n"
        code += "    string description;\n"
        code += "    map<string, string> properties;\n"
        code += "};\n\n"
        
        # Структура перехода
        code += "struct ScenarioTransition\n"
        code += "{\n"
        code += "    string id;\n"
        code += "    string sourceStateId;\n"
        code += "    string targetStateId;\n"
        code += "    string condition;\n"
        code += "    int priority;\n"
        code += "    vector<map<string, string>> actions;\n"
        code += "};\n\n"
        
        # Основной класс
        code += f"class {class_name}\n"
        code += "{\n"
        code += "private:\n"
        code += "    map<string, ScenarioState> states;\n"
        code += "    map<string, ScenarioTransition> transitions;\n"
        code += "    ScenarioState* currentState;\n"
        code += "    vector<string> executionHistory;\n"
        code += "    map<string, string> variables;\n\n"
        
        code += "public:\n"
        
        # Конструктор
        code += f"    {class_name}() : currentState(nullptr)\n"
        code += "    {\n"
        code += "        initializeStates();\n"
        code += "        initializeTransitions();\n"
        code += "    }\n\n"
        
        # Метод инициализации состояний
        code += "    void initializeStates()\n"
        code += "    {\n"
        for state in scenario.states:
            state_type_enum = state.state_type.upper().replace(' ', '_').replace('-', '_')
            code += f'        states["{state.id}"] = {{\n'
            code += f'            .id = "{state.id}",\n'
            code += f'            .name = "{state.name}",\n'
            code += f'            .type = StateType::{state_type_enum},\n'
            code += f'            .position = {{{(float)state.position_x}f, {(float)state.position_y}f, {(float)state.position_z}f}},\n'
            code += f'            .description = "{state.description or ""}",\n'
            code += "            .properties = {}\n"
            code += "        };\n"
        code += "    }\n\n"
        
        # Метод инициализации переходов
        code += "    void initializeTransitions()\n"
        code += "    {\n"
        for transition in scenario.transitions:
            code += f'        transitions["{transition.id}"] = {{\n'
            code += f'            .id = "{transition.id}",\n'
            code += f'            .sourceStateId = "{transition.source_state_id}",\n'
            code += f'            .targetStateId = "{transition.target_state_id}",\n'
            code += f'            .condition = "{transition.condition or ""}",\n'
            code += f'            .priority = {transition.priority},\n'
            code += "            .actions = {}\n"
            code += "        };\n"
        code += "    }\n\n"
        
        # Метод запуска
        code += "    void run()\n"
        code += "    {\n"
        code += '        cout << "Запуск сценария..." << endl;\n'
        code += "        // Логика выполнения сценария\n"
        code += '        cout << "Сценарий завершен" << endl;\n'
        code += "    }\n"
        
        code += "};\n\n"
        
        # Main функция
        code += "int main()\n"
        code += "{\n"
        code += f'    cout << "Запуск сгенерированного C++ сценария..." << endl;\n'
        code += f"    {class_name} scenario;\n"
        code += "    scenario.run();\n"
        code += '    cout << "Программа завершена" << endl;\n'
        code += "    return 0;\n"
        code += "}\n"
        
        return code
    
    def check_syntax(self, code: str) -> bool:
        """Проверка синтаксиса C++ кода (базовая проверка)"""
        # Базовая проверка структуры C++
        required_patterns = [
            r'#include\s+<iostream>',
            r'using\s+namespace\s+std;',
            r'int\s+main\s*\(\s*\)',
            r'class\s+\w+',
            r'cout\s*<<'
        ]
        
        for pattern in required_patterns:
            if not re.search(pattern, code, re.IGNORECASE):
                return False
        
        return True


class CodeGeneratorFactory:
    """Фабрика для создания генераторов кода"""
    
    @staticmethod
    def create_generator(language: str) -> CodeGenerator:
        """Создание генератора кода для указанного языка"""
        if language == ProgrammingLanguage.PYTHON.value:
            return PythonGenerator(language)
        elif language == ProgrammingLanguage.CSHARP.value:
            return CSharpGenerator(language)
        elif language == ProgrammingLanguage.CPP.value:
            return CppGenerator(language)
        else:
            raise ValueError(f"Неподдерживаемый язык: {language}")
    
    @staticmethod
    def get_available_languages() -> List[Dict[str, str]]:
        """Получение списка доступных языков"""
        return [
            {"value": ProgrammingLanguage.PYTHON.value, "name": "Python", "extension": ".py"},
            {"value": ProgrammingLanguage.CSHARP.value, "name": "C#", "extension": ".cs"},
            {"value": ProgrammingLanguage.CPP.value, "name": "C++", "extension": ".cpp"}
        ]