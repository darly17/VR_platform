"""
Сервис генерации кода (CodeGenController + стратегии генерации)
Соответствует UML диаграмме классов модели
"""

from typing import List, Dict, Optional, Any, Protocol
from abc import ABC, abstractmethod
import logging

from sqlalchemy.orm import Session, joinedload

from backend.models.visual_script import VisualScript, Node, Connection
from backend.models.scenario import Scenario, State, Transition
from backend.models.enums import ProgrammingLanguage, NodeType, StateType
from backend.utils.code_generator import CodeGenerator

logger = logging.getLogger(__name__)

class CodeGenerationStrategy(Protocol):
    """Интерфейс стратегии генерации кода (паттерн Стратегия)"""
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация кода из визуального скрипта"""
        ...
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация кода из сценария"""
        ...
    
    def get_language(self) -> str:
        """Получить язык программирования"""
        ...

class PythonGenerationStrategy:
    """Стратегия генерации Python кода"""
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        """Генерация Python кода из визуального скрипта"""
        code_lines = [
            "# Генерация Python кода из визуального скрипта",
            f"# Название: {visual_script.name}",
            f"# Узлов: {len(visual_script.nodes)}, Соединений: {len(visual_script.connections)}",
            "",
            "import time",
            "",
            "class GeneratedScript:",
            "    def __init__(self):",
            "        self.variables = {}",
            "        self.execution_log = []",
            "",
            "    def execute(self):",
            "        '''Основной метод выполнения'''",
            "        self.execution_log.append('Начало выполнения скрипта')",
            ""
        ]
        
        # Генерация для каждого узла
        for node in visual_script.nodes:
            if node.node_type == NodeType.EVENT.value:
                code_lines.extend([
                    f"    def {node.name.lower().replace(' ', '_')}_event(self):",
                    f"        '''Обработка события: {node.name}'''",
                    f"        self.execution_log.append('Событие: {node.name}')",
                    f"        {self._generate_node_logic(node)}",
                    ""
                ])
            elif node.node_type == NodeType.ACTION.value:
                code_lines.extend([
                    f"    def {node.name.lower().replace(' ', '_')}_action(self):",
                    f"        '''Действие: {node.name}'''",
                    f"        self.execution_log.append('Действие: {node.name}')",
                    f"        {self._generate_node_logic(node)}",
                    ""
                ])
            elif node.node_type == NodeType.VARIABLE.value:
                var_name = node.properties.get('name', 'unnamed')
                var_value = node.properties.get('value', 'None')
                code_lines.extend([
                    f"    def init_{var_name.lower()}(self):",
                    f"        '''Инициализация переменной {var_name}'''",
                    f"        self.variables['{var_name}'] = {var_value}",
                    f"        self.execution_log.append('Инициализирована переменная: {var_name} = {var_value}')",
                    ""
                ])
        
        # Генерация логики выполнения
        code_lines.extend([
            "    def run_logic(self):",
            "        '''Логика выполнения на основе соединений'''",
        ])
        
        # Простая логика выполнения на основе соединений
        for connection in visual_script.connections[:5]:  # Ограничим для примера
            source_node = next((n for n in visual_script.nodes if n.id == connection.source_node_id), None)
            target_node = next((n for n in visual_script.nodes if n.id == connection.target_node_id), None)
            
            if source_node and target_node:
                code_lines.append(
                    f"        # {source_node.name} -> {target_node.name}"
                )
        
        code_lines.extend([
            "        pass",
            "",
            "if __name__ == '__main__':",
            "    script = GeneratedScript()",
            "    script.execute()",
            "    script.run_logic()",
            "    print('Выполнение завершено')",
            "    for log in script.execution_log:",
            "        print(f'  - {log}')",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        """Генерация Python кода из сценария"""
        code_lines = [
            "# Генерация Python кода из сценария",
            f"# Название: {scenario.name}",
            f"# Состояний: {len(scenario.states)}, Переходов: {len(scenario.transitions)}",
            "",
            "class ScenarioStateMachine:",
            "    def __init__(self):",
            "        self.current_state = None",
            "        self.states = {}",
            "        self.transitions = {}",
            "        self.initialize_states()",
            "        self.initialize_transitions()",
            "",
            "    def initialize_states(self):",
        ]
        
        # Инициализация состояний
        for state in scenario.states:
            code_lines.append(
                f"        self.states['{state.id}'] = {{"
            )
            code_lines.append(f"            'name': '{state.name}',")
            code_lines.append(f"            'type': '{state.state_type}',")
            code_lines.append(f"            'position': [{state.position_x}, {state.position_y}, {state.position_z}],")
            code_lines.append(f"            'description': '{state.description or ''}'")
            code_lines.append("        }")
        
        code_lines.extend([
            "",
            "    def initialize_transitions(self):",
        ])
        
        # Инициализация переходов
        for transition in scenario.transitions:
            code_lines.append(
                f"        self.transitions['{transition.id}'] = {{"
            )
            code_lines.append(f"            'source': '{transition.source_state_id}',")
            code_lines.append(f"            'target': '{transition.target_state_id}',")
            code_lines.append(f"            'condition': '{transition.condition or ''}',")
            code_lines.append(f"            'priority': {transition.priority}")
            code_lines.append("        }")
        
        code_lines.extend([
            "",
            "    def start(self):",
            "        '''Начало выполнения сценария'''",
        ])
        
        # Находим начальное состояние
        start_state = next((s for s in scenario.states if s.state_type == StateType.START.value), None)
        if start_state:
            code_lines.append(f"        self.current_state = '{start_state.id}'")
            code_lines.append(f"        print(f'Начало сценария: {start_state.name}')")
        
        code_lines.extend([
            "",
            "    def execute_transition(self, transition_id):",
            "        '''Выполнение перехода'''",
            "        transition = self.transitions.get(transition_id)",
            "        if not transition:",
            "            return False",
            "        ",
            "        # Проверка условия",
            "        condition_result = self.evaluate_condition(transition['condition'])",
            "        if condition_result:",
            "            self.current_state = transition['target']",
            "            print(f'Переход выполнен: {transition_id}')",
            "            return True",
            "        return False",
            "",
            "    def evaluate_condition(self, condition):",
            "        '''Оценка условия перехода'''",
            "        if not condition or condition.strip() == '':",
            "            return True",
            "        try:",
            "            # Простая оценка условий",
            "            # В реальной системе здесь будет полноценный парсер",
            "            return eval(condition, {'__builtins__': {}})",
            "        except:",
            "            return False",
            "",
            "    def run(self):",
            "        '''Основной цикл выполнения'''",
            "        self.start()",
            "        print('Сценарий выполняется...')",
            "        # Логика выполнения переходов",
            "        for _ in range(10):  # Защита от бесконечного цикла",
            "            if not self.execute_available_transitions():",
            "                break",
            "        print('Сценарий завершен')",
            "",
            "    def execute_available_transitions(self):",
            "        '''Выполнение доступных переходов из текущего состояния'''",
            "        transitions = [t for t in self.transitions.values() ",
            "                      if t['source'] == self.current_state]",
            "        transitions.sort(key=lambda x: x['priority'], reverse=True)",
            "        ",
            "        for transition in transitions:",
            "            if self.execute_transition_by_data(transition):",
            "                return True",
            "        return False",
            "",
            "    def execute_transition_by_data(self, transition):",
            "        '''Выполнение перехода по данным'''",
            "        if self.evaluate_condition(transition['condition']):",
            "            self.current_state = transition['target']",
            "            target_state = next((s for s in self.states.values() ",
            "                               if s['name'] == transition['target']), None)",
            "            if target_state:",
            "                print(f'Переход в состояние: {target_state[\"name\"]}')",
            "            return True",
            "        return False",
            "",
            "if __name__ == '__main__':",
            "    scenario = ScenarioStateMachine()",
            "    scenario.run()",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def _generate_node_logic(self, node: Node) -> str:
        """Генерация логики для узла"""
        if node.node_type == NodeType.ACTION.value:
            action = node.properties.get('action', '')
            if action == 'play_animation':
                anim_name = node.properties.get('animation_name', 'default')
                return f"print('Проигрывание анимации: {anim_name}')"
            elif action == 'set_variable':
                var_name = node.properties.get('variable_name', '')
                var_value = node.properties.get('value', '')
                return f"self.variables['{var_name}'] = {var_value}"
        elif node.node_type == NodeType.CONDITION.value:
            condition = node.properties.get('condition', 'True')
            return f"return {condition}"
        
        return "pass"
    
    def get_language(self) -> str:
        return ProgrammingLanguage.PYTHON.value

class CSharpGenerationStrategy:
    """Стратегия генерации C# кода"""
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        code_lines = [
            "// Генерация C# кода из визуального скрипта",
            f"// Название: {visual_script.name}",
            "",
            "using System;",
            "using System.Collections.Generic;",
            "",
            "namespace GeneratedVRARScript",
            "{",
            "    public class GeneratedScript",
            "    {",
            "        private Dictionary<string, object> variables = new Dictionary<string, object>();",
            "        private List<string> executionLog = new List<string>();",
            "",
            "        public void Execute()",
            "        {",
            "            executionLog.Add(\"Начало выполнения скрипта\");",
            "            RunLogic();",
            "            executionLog.Add(\"Завершение выполнения скрипта\");",
            "            ",
            "            foreach (var log in executionLog)",
            "            {",
            "                Console.WriteLine(f\"  - {log}\");",
            "            }",
            "        }",
            "",
            "        private void RunLogic()",
            "        {",
            "            // Логика на основе визуального скрипта",
        ]
        
        for connection in visual_script.connections[:3]:
            source_node = next((n for n in visual_script.nodes if n.id == connection.source_node_id), None)
            target_node = next((n for n in visual_script.nodes if n.id == connection.target_node_id), None)
            
            if source_node and target_node:
                code_lines.append(
                    f"            // {source_node.name} -> {target_node.name}"
                )
        
        code_lines.extend([
            "        }",
            "    }",
            "}",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        code_lines = [
            "// Генерация C# кода из сценария",
            f"// Название: {scenario.name}",
            "",
            "using System;",
            "using System.Collections.Generic;",
            "",
            "namespace VRARScenario",
            "{",
            "    public enum StateType",
            "    {",
            "        Start,",
            "        Idle,",
            "        Interaction,",
            "        End",
            "    }",
            "",
            "    public class ScenarioState",
            "    {",
            "        public string Id { get; set; }",
            "        public string Name { get; set; }",
            "        public StateType Type { get; set; }",
            "        public float[] Position { get; set; } = new float[3];",
            "    }",
            "",
            "    public class ScenarioTransition",
            "    {",
            "        public string SourceStateId { get; set; }",
            "        public string TargetStateId { get; set; }",
            "        public string Condition { get; set; }",
            "        public int Priority { get; set; }",
            "    }",
            "",
            "    public class ScenarioStateMachine",
            "    {",
            "        private Dictionary<string, ScenarioState> states = new Dictionary<string, ScenarioState>();",
            "        private Dictionary<string, ScenarioTransition> transitions = new Dictionary<string, ScenarioTransition>();",
            "        private ScenarioState currentState;",
            "",
            "        public void Initialize()",
            "        {",
            "            // Инициализация состояний",
        ]
        
        for state in scenario.states:
            code_lines.append(f"            states[\"{state.id}\"] = new ScenarioState {{")
            code_lines.append(f"                Id = \"{state.id}\",")
            code_lines.append(f"                Name = \"{state.name}\",")
            code_lines.append(f"                Type = StateType.{state.state_type.capitalize()},")
            code_lines.append(f"                Position = new float[] {{ {state.position_x}f, {state.position_y}f, {state.position_z}f }}")
            code_lines.append("            };")
        
        code_lines.extend([
            "",
            "            // Инициализация переходов",
        ])
        
        for transition in scenario.transitions:
            code_lines.append(f"            transitions[\"{transition.id}\"] = new ScenarioTransition {{")
            code_lines.append(f"                SourceStateId = \"{transition.source_state_id}\",")
            code_lines.append(f"                TargetStateId = \"{transition.target_state_id}\",")
            code_lines.append(f"                Condition = \"{transition.condition or string.Empty}\",")
            code_lines.append(f"                Priority = {transition.priority}")
            code_lines.append("            };")
        
        code_lines.extend([
            "        }",
            "",
            "        public void Run()",
            "        {",
            "            Console.WriteLine(\"Запуск сценария...\");",
            "            // Логика выполнения",
            "            Console.WriteLine(\"Сценарий завершен\");",
            "        }",
            "    }",
            "}",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def get_language(self) -> str:
        return ProgrammingLanguage.CSHARP.value

class CppGenerationStrategy:
    """Стратегия генерации C++ кода"""
    
    def generate_from_visual_script(self, visual_script: VisualScript) -> str:
        code_lines = [
            "// Генерация C++ кода из визуального скрипта",
            f"// Название: {visual_script.name}",
            "",
            "#include <iostream>",
            "#include <vector>",
            "#include <string>",
            "#include <map>",
            "",
            "using namespace std;",
            "",
            "class GeneratedScript {",
            "private:",
            "    map<string, void*> variables;",
            "    vector<string> executionLog;",
            "",
            "public:",
            "    void execute() {",
            "        executionLog.push_back(\"Начало выполнения скрипта\");",
            "        runLogic();",
            "        executionLog.push_back(\"Завершение выполнения скрипта\");",
            "        ",
            "        for (const auto& log : executionLog) {",
            "            cout << \"  - \" << log << endl;",
            "        }",
            "    }",
            "",
            "private:",
            "    void runLogic() {",
            "        // Логика на основе визуального скрипта",
        ]
        
        for connection in visual_script.connections[:3]:
            source_node = next((n for n in visual_script.nodes if n.id == connection.source_node_id), None)
            target_node = next((n for n in visual_script.nodes if n.id == connection.target_node_id), None)
            
            if source_node and target_node:
                code_lines.append(
                    f"        // {source_node.name} -> {target_node.name}"
                )
        
        code_lines.extend([
            "    }",
            "};",
            "",
            "int main() {",
            "    GeneratedScript script;",
            "    script.execute();",
            "    return 0;",
            "}",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def generate_from_scenario(self, scenario: Scenario) -> str:
        code_lines = [
            "// Генерация C++ кода из сценария",
            f"// Название: {scenario.name}",
            "",
            "#include <iostream>",
            "#include <vector>",
            "#include <string>",
            "#include <map>",
            "#include <algorithm>",
            "",
            "using namespace std;",
            "",
            "enum class StateType {",
            "    START,",
            "    IDLE,",
            "    INTERACTION,",
            "    END",
            "};",
            "",
            "struct ScenarioState {",
            "    string id;",
            "    string name;",
            "    StateType type;",
            "    float position[3];",
            "};",
            "",
            "struct ScenarioTransition {",
            "    string sourceStateId;",
            "    string targetStateId;",
            "    string condition;",
            "    int priority;",
            "};",
            "",
            "class ScenarioStateMachine {",
            "private:",
            "    map<string, ScenarioState> states;",
            "    map<string, ScenarioTransition> transitions;",
            "    ScenarioState* currentState;",
            "",
            "public:",
            "    void initialize() {",
            "        // Инициализация состояний",
        ]
        
        for state in scenario.states:
            code_lines.append(f"        states[\"{state.id}\"] = {{")
            code_lines.append(f"            .id = \"{state.id}\",")
            code_lines.append(f"            .name = \"{state.name}\",")
            code_lines.append(f"            .type = StateType::{state.state_type.upper()},")
            code_lines.append(f"            .position = {{{state.position_x}f, {state.position_y}f, {state.position_z}f}}")
            code_lines.append("        };")
        
        code_lines.extend([
            "",
            "        // Инициализация переходов",
        ])
        
        for transition in scenario.transitions:
            code_lines.append(f"        transitions[\"{transition.id}\"] = {{")
            code_lines.append(f"            .sourceStateId = \"{transition.source_state_id}\",")
            code_lines.append(f"            .targetStateId = \"{transition.target_state_id}\",")
            code_lines.append(f"            .condition = \"{transition.condition}\",")
            code_lines.append(f"            .priority = {transition.priority}")
            code_lines.append("        };")
        
        code_lines.extend([
            "    }",
            "",
            "    void run() {",
            "        cout << \"Запуск сценария...\" << endl;",
            "        // Логика выполнения",
            "        cout << \"Сценарий завершен\" << endl;",
            "    }",
            "};",
            "",
            "int main() {",
            "    ScenarioStateMachine machine;",
            "    machine.initialize();",
            "    machine.run();",
            "    return 0;",
            "}",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def get_language(self) -> str:
        return ProgrammingLanguage.CPP.value

class CodeGenService:
    """
    CodeGenController из UML - управление генерацией кода
    Использует паттерн Стратегия для разных языков программирования
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.strategies = {
            ProgrammingLanguage.PYTHON.value: PythonGenerationStrategy(),
            ProgrammingLanguage.CSHARP.value: CSharpGenerationStrategy(),
            ProgrammingLanguage.CPP.value: CppGenerationStrategy()
        }
    
    def generate_code_from_visual_script(self, visual_script_id: str, 
                                        language: str = None) -> Dict[str, Any]:
        """Генерация кода из визуального скрипта"""
        visual_script = self.db.query(VisualScript).options(
            joinedload(VisualScript.nodes),
            joinedload(VisualScript.connections)
        ).filter(VisualScript.id == visual_script_id).first()
        
        if not visual_script:
            return {"error": "Визуальный скрипт не найден"}
        
        language = language or ProgrammingLanguage.PYTHON.value
        strategy = self.strategies.get(language)
        
        if not strategy:
            return {"error": f"Язык {language} не поддерживается"}
        
        try:
            code = strategy.generate_from_visual_script(visual_script)
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "visual_script_id": visual_script_id,
                "visual_script_name": visual_script.name,
                "nodes_count": len(visual_script.nodes),
                "connections_count": len(visual_script.connections)
            }
        except Exception as e:
            logger.error(f"Ошибка генерации кода: {e}")
            return {"error": str(e)}
    
    def generate_code_from_scenario(self, scenario_id: str, 
                                   language: str = None) -> Dict[str, Any]:
        """Генерация кода из сценария"""
        scenario = self.db.query(Scenario).options(
            joinedload(Scenario.states),
            joinedload(Scenario.transitions)
        ).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": "Сценарий не найден"}
        
        language = language or ProgrammingLanguage.PYTHON.value
        strategy = self.strategies.get(language)
        
        if not strategy:
            return {"error": f"Язык {language} не поддерживается"}
        
        try:
            code = strategy.generate_from_scenario(scenario)
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "states_count": len(scenario.states),
                "transitions_count": len(scenario.transitions)
            }
        except Exception as e:
            logger.error(f"Ошибка генерации кода: {e}")
            return {"error": str(e)}
    
    def export_code_to_file(self, code: str, filename: str, 
                           language: str) -> Dict[str, Any]:
        """Экспорт сгенерированного кода в файл"""
        try:
            from pathlib import Path
            
            # Определяем расширение файла
            extensions = {
                ProgrammingLanguage.PYTHON.value: ".py",
                ProgrammingLanguage.CSHARP.value: ".cs",
                ProgrammingLanguage.CPP.value: ".cpp"
            }
            
            extension = extensions.get(language, ".txt")
            export_dir = Path("data/exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = export_dir / f"{filename}{extension}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "filename": file_path.name
            }
        except Exception as e:
            logger.error(f"Ошибка экспорта кода: {e}")
            return {"error": str(e)}
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Получить список поддерживаемых языков программирования"""
        return [
            {"value": ProgrammingLanguage.PYTHON.value, "name": "Python"},
            {"value": ProgrammingLanguage.CSHARP.value, "name": "C#"},
            {"value": ProgrammingLanguage.CPP.value, "name": "C++"}
        ]
    
    def validate_code_syntax(self, code: str, language: str) -> Dict[str, Any]:
        """Проверка синтаксиса кода (метод из UML CodeGenerator)"""
        # В реальной системе здесь будет полноценная проверка синтаксиса
        # Для примера используем простые проверки
        
        if language == ProgrammingLanguage.PYTHON.value:
            # Простая проверка Python
            try:
                import ast
                ast.parse(code)
                return {"valid": True, "message": "Синтаксис Python корректен"}
            except SyntaxError as e:
                return {"valid": False, "message": f"Ошибка синтаксиса Python: {e}"}
        
        elif language == ProgrammingLanguage.CSHARP.value:
            # Простая проверка C#
            if "using" in code and "class" in code and "namespace" in code:
                return {"valid": True, "message": "Базовая структура C# присутствует"}
            else:
                return {"valid": False, "message": "Отсутствуют обязательные элементы C#"}
        
        elif language == ProgrammingLanguage.CPP.value:
            # Простая проверка C++
            if "#include" in code and "int main()" in code:
                return {"valid": True, "message": "Базовая структура C++ присутствует"}
            else:
                return {"valid": False, "message": "Отсутствуют обязательные элементы C++"}
        
        return {"valid": False, "message": f"Язык {language} не поддерживается для проверки"}