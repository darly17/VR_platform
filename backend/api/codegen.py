"""
API эндпоинты для генерации кода
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from backend.database import get_db
from backend.services.codegen_service import CodeGenService
from backend.services.scenario_service import ScenarioService
from backend.services.user_service import UserService
from backend.api.auth import get_current_user
from backend.models.enums import UserRole, ProgrammingLanguage

router = APIRouter(prefix="/codegen", tags=["Генерация кода"])

@router.get("/languages")
async def get_supported_languages(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка поддерживаемых языков программирования
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут генерировать код"
        )
    
    codegen_service = CodeGenService(db)
    languages = codegen_service.get_supported_languages()
    
    return {
        "success": True,
        "languages": languages
    }

@router.post("/from-visual-script/{visual_script_id}")
async def generate_code_from_visual_script(
    visual_script_id: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    filename: Optional[str] = None,
    export_to_file: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут генерировать код"
        )
    
    # Проверяем доступ к визуальному скрипту
    from backend.models.visual_script import VisualScript
    visual_script = db.query(VisualScript).filter(VisualScript.id == visual_script_id).first()
    
    if not visual_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Визуальный скрипт не найден"
        )
    
    # Проверяем доступ к связанному сценарию
    if visual_script.scenario:
        scenario_service = ScenarioService(db)
        scenario = scenario_service.get_scenario(visual_script.scenario_id)
        
        if scenario:
            has_access = (
                scenario.created_by == current_user["id"] or
                (scenario.project and (
                    scenario.project.created_by == current_user["id"] or
                    any(manager.id == current_user["id"] for manager in scenario.project.managers)
                ))
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для генерации кода из этого визуального скрипта"
                )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.generate_code_from_visual_script(visual_script_id, language)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # Экспорт в файл, если запрошено
    if export_to_file and result["success"]:
        export_filename = filename or f"visual_script_{visual_script_id}"
        
        export_result = codegen_service.export_code_to_file(
            code=result["code"],
            filename=export_filename,
            language=language
        )
        
        if "error" in export_result:
            result["export_error"] = export_result["error"]
        else:
            result["export"] = export_result
    
    return result

@router.post("/from-scenario/{scenario_id}")
async def generate_code_from_scenario(
    scenario_id: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    filename: Optional[str] = None,
    export_to_file: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Генерация кода из сценария
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут генерировать код"
        )
    
    # Проверяем доступ к сценарию
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    has_access = (
        scenario.created_by == current_user["id"] or
        (scenario.project and (
            scenario.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in scenario.project.managers)
        ))
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для генерации кода из этого сценария"
        )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.generate_code_from_scenario(scenario_id, language)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # Экспорт в файл, если запрошено
    if export_to_file and result["success"]:
        export_filename = filename or f"scenario_{scenario_id}"
        
        export_result = codegen_service.export_code_to_file(
            code=result["code"],
            filename=export_filename,
            language=language
        )
        
        if "error" in export_result:
            result["export_error"] = export_result["error"]
        else:
            result["export"] = export_result
    
    return result

@router.post("/validate")
async def validate_code_syntax(
    code: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Проверка синтаксиса кода
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут проверять синтаксис кода"
        )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.validate_code_syntax(code, language)
    
    return {
        "success": True,
        "validation": result
    }

@router.post("/export")
async def export_code_to_file(
    code: str,
    filename: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Экспорт кода в файл
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут экспортировать код"
        )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.export_code_to_file(code, filename, language)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        "success": True,
        "export": result
    }

@router.get("/visual-script/{visual_script_id}/preview")
async def get_visual_script_code_preview(
    visual_script_id: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    lines: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение предварительного просмотра генерируемого кода
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут просматривать предварительный код"
        )
    
    # Проверяем доступ к визуальному скрипту
    from backend.models.visual_script import VisualScript
    visual_script = db.query(VisualScript).filter(VisualScript.id == visual_script_id).first()
    
    if not visual_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Визуальный скрипт не найден"
        )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.generate_code_from_visual_script(visual_script_id, language)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # Обрезаем код для предварительного просмотра
    code_lines = result["code"].split('\n')
    preview_code = '\n'.join(code_lines[:lines])
    
    if len(code_lines) > lines:
        preview_code += f"\n... (еще {len(code_lines) - lines} строк)"
    
    return {
        "success": True,
        "preview": preview_code,
        "total_lines": len(code_lines),
        "preview_lines": lines,
        "visual_script_id": visual_script_id,
        "language": language
    }

@router.get("/scenario/{scenario_id}/preview")
async def get_scenario_code_preview(
    scenario_id: str,
    language: str = ProgrammingLanguage.PYTHON.value,
    lines: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение предварительного просмотра генерируемого кода из сценария
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут просматривать предварительный код"
        )
    
    # Проверяем доступ к сценарию
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    codegen_service = CodeGenService(db)
    result = codegen_service.generate_code_from_scenario(scenario_id, language)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # Обрезаем код для предварительного просмотра
    code_lines = result["code"].split('\n')
    preview_code = '\n'.join(code_lines[:lines])
    
    if len(code_lines) > lines:
        preview_code += f"\n... (еще {len(code_lines) - lines} строк)"
    
    return {
        "success": True,
        "preview": preview_code,
        "total_lines": len(code_lines),
        "preview_lines": lines,
        "scenario_id": scenario_id,
        "language": language
    }

@router.get("/templates")
async def get_code_templates(
    language: str = ProgrammingLanguage.PYTHON.value,
    template_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение шаблонов кода
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут просматривать шаблоны кода"
        )
    
    # Примеры шаблонов
    templates = []
    
    if language == ProgrammingLanguage.PYTHON.value:
        templates = [
            {
                "id": "python_basic",
                "name": "Базовый Python скрипт",
                "description": "Базовый шаблон Python скрипта",
                "code": """#!/usr/bin/env python3
\"\"\"
Сгенерированный Python код из VR/AR платформы
\"\"\"

import time
import math

class GeneratedVRARComponent:
    \"\"\"Компонент VR/AR системы\"\"\"
    
    def __init__(self, name):
        self.name = name
        self.is_active = True
        self.properties = {}
    
    def activate(self):
        \"\"\"Активация компонента\"\"\"
        self.is_active = True
        print(f"Компонент '{self.name}' активирован")
        return True
    
    def deactivate(self):
        \"\"\"Деактивация компонента\"\"\"
        self.is_active = False
        print(f"Компонент '{self.name}' деактивирован")
        return True
    
    def set_property(self, key, value):
        \"\"\"Установка свойства\"\"\"
        self.properties[key] = value
        return True
    
    def get_property(self, key):
        \"\"\"Получение свойства\"\"\"
        return self.properties.get(key)

def main():
    \"\"\"Основная функция\"\"\"
    print("Запуск VR/AR компонента...")
    component = GeneratedVRARComponent("Тестовый компонент")
    component.activate()
    component.set_property("version", "1.0.0")
    print(f"Версия: {component.get_property('version')}")
    component.deactivate()

if __name__ == "__main__":
    main()"""
            },
            {
                "id": "python_state_machine",
                "name": "Python конечный автомат",
                "description": "Шаблон конечного автомата на Python",
                "code": """class StateMachine:
    \"\"\"Конечный автомат\"\"\"
    
    def __init__(self):
        self.states = {}
        self.current_state = None
        self.transitions = []
    
    def add_state(self, state_id, state_name):
        \"\"\"Добавление состояния\"\"\"
        self.states[state_id] = state_name
        if self.current_state is None:
            self.current_state = state_id
    
    def add_transition(self, from_state, to_state, condition):
        \"\"\"Добавление перехода\"\"\"
        self.transitions.append({
            'from': from_state,
            'to': to_state,
            'condition': condition
        })
    
    def execute(self):
        \"\"\"Выполнение автомата\"\"\"
        print(f"Текущее состояние: {self.states.get(self.current_state, 'Неизвестно')}")
        
        for transition in self.transitions:
            if transition['from'] == self.current_state:
                # Проверка условия перехода
                try:
                    if eval(transition['condition'], {'__builtins__': {}}):
                        self.current_state = transition['to']
                        print(f"Переход в состояние: {self.states.get(self.current_state, 'Неизвестно')}")
                        break
                except:
                    pass"""
            }
        ]
    
    elif language == ProgrammingLanguage.CSHARP.value:
        templates = [
            {
                "id": "csharp_basic",
                "name": "Базовый C# класс",
                "description": "Базовый шаблон C# класса",
                "code": """using System;
using System.Collections.Generic;

namespace VRAR.Generated
{
    /// <summary>
    /// Сгенерированный C# код из VR/AR платформы
    /// </summary>
    public class GeneratedComponent
    {
        public string Name { get; set; }
        public bool IsActive { get; set; }
        private Dictionary<string, object> properties = new Dictionary<string, object>();
        
        public GeneratedComponent(string name)
        {
            Name = name;
            IsActive = true;
        }
        
        public void Activate()
        {
            IsActive = true;
            Console.WriteLine($"Компонент '{Name}' активирован");
        }
        
        public void Deactivate()
        {
            IsActive = false;
            Console.WriteLine($"Компонент '{Name}' деактивирован");
        }
        
        public void SetProperty(string key, object value)
        {
            properties[key] = value;
        }
        
        public object GetProperty(string key)
        {
            return properties.ContainsKey(key) ? properties[key] : null;
        }
    }
}"""
            }
        ]
    
    # Фильтрация по типу
    if template_type:
        templates = [t for t in templates if template_type in t["id"]]
    
    return {
        "success": True,
        "templates": templates,
        "language": language,
        "total": len(templates)
    }