"""
API эндпоинты для управления сценариями
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from backend.database import get_db
from backend.services.scenario_service import ScenarioService
from backend.services.project_service import ProjectService
from backend.services.user_service import UserService
from backend.api.auth import get_current_user
from backend.models.enums import UserRole, StateType

router = APIRouter(prefix="/scenarios", tags=["Сценарии"])

@router.get("/")
async def get_scenarios(
    project_id: Optional[str] = None,
    only_active: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка сценариев
    """
    scenario_service = ScenarioService(db)
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    scenarios = []
    
    if project_id:
        # Проверяем доступ к проекту
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден"
            )
        
        # Проверка прав доступа
        has_access = (
            project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in project.managers) or
            user.role in [UserRole.DEVELOPER, UserRole.TESTER]
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к сценариям проекта"
            )
        
        scenarios = scenario_service.get_project_scenarios(project_id, only_active)
    else:
        # Получаем все сценарии, доступные пользователю
        # Для упрощения возвращаем все сценарии для разработчиков и тестировщиков
        if user.role == UserRole.DEVELOPER:
            # Получаем проекты, созданные пользователем
            from backend.models.project import Project
            user_projects = db.query(Project).filter(
                Project.created_by == current_user["id"]
            ).all()
            
            for project in user_projects:
                project_scenarios = scenario_service.get_project_scenarios(project.id, only_active)
                scenarios.extend(project_scenarios)
        elif user.role == UserRole.TESTER:
            # Тестировщики видят все активные сценарии
            from backend.models.scenario import Scenario
            query = db.query(Scenario).filter(Scenario.is_active == True)
            
            if only_active:
                query = query.filter(Scenario.is_active == True)
            
            scenarios = query.limit(limit).offset(offset).all()
        else:
            # Для остальных ролей возвращаем пустой список
            scenarios = []
    
    # Пагинация
    paginated_scenarios = scenarios[offset:offset + limit]
    
    return {
        "success": True,
        "scenarios": [scenario.to_dict() for scenario in paginated_scenarios],
        "total": len(scenarios),
        "limit": limit,
        "offset": offset
    }

@router.post("/")
async def create_scenario(
    name: str,
    project_id: str,
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание нового сценария
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут создавать сценарии"
        )
    
    # Проверяем доступ к проекту
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers)
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания сценария в проекте"
        )
    
    scenario_service = ScenarioService(db)
    
    try:
        scenario = scenario_service.create_scenario(
            name=name,
            project_id=project_id,
            created_by=current_user["id"],
            description=description
        )
        
        return {
            "success": True,
            "message": "Сценарий успешно создан",
            "scenario": scenario.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания сценария: {str(e)}"
        )

@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации о сценарии
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    # Проверяем доступ к проекту
    project_service = ProjectService(db)
    project = project_service.get_project(scenario.project_id)
    
    has_access = False
    if project:
        has_access = (
            project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in project.managers) or
            user.role in [UserRole.DEVELOPER, UserRole.TESTER]
        )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к сценарию"
        )
    
    scenario_data = scenario.to_dict()
    
    # Добавляем подробную информацию
    scenario_data["project"] = {
        "id": scenario.project.id,
        "name": scenario.project.name
    } if scenario.project else None
    
    scenario_data["creator"] = {
        "id": scenario.creator.id,
        "username": scenario.creator.username,
        "full_name": scenario.creator.full_name
    } if scenario.creator else None
    
    # Добавляем статистику
    stats = scenario_service.get_scenario_stats(scenario_id)
    scenario_data["stats"] = stats
    
    # Добавляем утвердивших менеджеров
    scenario_data["approvers"] = [
        {"id": a.id, "username": a.username, "full_name": a.full_name}
        for a in scenario.approvers
    ]
    
    return {
        "success": True,
        "scenario": scenario_data
    }

@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    version: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Обновление сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = False
    if scenario.project:
        has_access = (
            scenario.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in scenario.project.managers) or
            user.role == UserRole.DEVELOPER
        )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления сценария"
        )
    
    # Подготовка данных для обновления
    update_data = {}
    
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if is_active is not None:
        update_data["is_active"] = is_active
    if version is not None:
        update_data["version"] = version
    
    try:
        updated_scenario = scenario_service.update_scenario(scenario_id, **update_data)
        
        return {
            "success": True,
            "message": "Сценарий успешно обновлен",
            "scenario": updated_scenario.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления сценария: {str(e)}"
        )

@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Удаление сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = False
    if scenario.project:
        has_access = (
            scenario.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in scenario.project.managers) or
            user.role == UserRole.DEVELOPER
        )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления сценария"
        )
    
    success = scenario_service.delete_scenario(scenario_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления сценария"
        )
    
    return {
        "success": True,
        "message": "Сценарий успешно удален"
    }

@router.post("/{scenario_id}/execute")
async def execute_scenario(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Выполнение сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role in [UserRole.DEVELOPER, UserRole.TESTER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения сценария"
        )
    
    success, message = scenario_service.execute_scenario(scenario_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/{scenario_id}/validate")
async def validate_scenario(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Валидация сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role in [UserRole.DEVELOPER, UserRole.TESTER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для валидации сценария"
        )
    
    success, errors = scenario_service.validate_scenario(scenario_id)
    
    return {
        "success": success,
        "valid": success,
        "errors": errors,
        "message": "Сценарий валиден" if success else "Обнаружены ошибки валидации"
    }

@router.post("/{scenario_id}/approve")
async def approve_scenario(
    scenario_id: str,
    comments: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Утверждение сценария менеджером
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только менеджеры могут утверждать сценарии"
        )
    
    success = scenario_service.approve_scenario(scenario_id, current_user["id"], comments)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка утверждения сценария"
        )
    
    return {
        "success": True,
        "message": "Сценарий успешно утвержден"
    }

@router.post("/{scenario_id}/states")
async def create_state(
    scenario_id: str,
    name: str,
    state_type: str = StateType.IDLE.value,
    position_json: str = '[0, 0, 0]',
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание состояния в сценарии
    """
    try:
        position = json.loads(position_json)
    except json.JSONDecodeError:
        position = [0, 0, 0]
    
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут создавать состояния"
        )
    
    state = scenario_service.create_state(
        scenario_id=scenario_id,
        name=name,
        state_type=state_type,
        position=position
    )
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания состояния"
        )
    
    if description:
        state.description = description
        db.commit()
    
    return {
        "success": True,
        "message": "Состояние успешно создано",
        "state": state.to_dict()
    }

@router.post("/{scenario_id}/transitions")
async def create_transition(
    scenario_id: str,
    source_state_id: str,
    target_state_id: str,
    condition: str = "",
    priority: int = 1,
    name: str = "",
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание перехода между состояниями
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут создавать переходы"
        )
    
    transition = scenario_service.create_transition(
        source_state_id=source_state_id,
        target_state_id=target_state_id,
        scenario_id=scenario_id,
        condition=condition,
        priority=priority,
        name=name
    )
    
    if not transition:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания перехода"
        )
    
    return {
        "success": True,
        "message": "Переход успешно создан",
        "transition": transition.to_dict()
    }

@router.get("/{scenario_id}/graph")
async def get_scenario_graph(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение графа состояний сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role in [UserRole.DEVELOPER, UserRole.TESTER, UserRole.MANAGER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к графу сценария"
        )
    
    graph_data = scenario_service.get_state_graph(scenario_id)
    
    return {
        "success": True,
        "graph": graph_data,
        "scenario_id": scenario_id,
        "scenario_name": scenario.name
    }

@router.post("/{scenario_id}/objects")
async def add_object_to_scenario(
    scenario_id: str,
    object_3d_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Добавление 3D объекта в сценарий
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role in [UserRole.DEVELOPER, UserRole.DESIGNER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для добавления объектов в сценарий"
        )
    
    success = scenario_service.add_object_3d(scenario_id, object_3d_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка добавления объекта в сценарий"
        )
    
    return {
        "success": True,
        "message": "3D объект успешно добавлен в сценарий"
    }

@router.post("/{scenario_id}/visual-scripts")
async def create_visual_script(
    scenario_id: str,
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание визуального скрипта для сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только разработчики могут создавать визуальные скрипты"
        )
    
    visual_script = scenario_service.create_visual_script(
        scenario_id=scenario_id,
        name=name,
        created_by=current_user["id"]
    )
    
    if not visual_script:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания визуального скрипта"
        )
    
    return {
        "success": True,
        "message": "Визуальный скрипт успешно создан",
        "visual_script": visual_script.to_dict()
    }

@router.get("/{scenario_id}/stats")
async def get_scenario_stats(
    scenario_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение статистики сценария
    """
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role in [UserRole.DEVELOPER, UserRole.TESTER, UserRole.MANAGER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к статистике сценария"
        )
    
    stats = scenario_service.get_scenario_stats(scenario_id)
    
    return {
        "success": True,
        "stats": stats
    }