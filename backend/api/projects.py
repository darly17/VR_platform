"""
API эндпоинты для управления проектами
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from backend.database import get_db
from backend.services.project_service import ProjectService
from backend.services.user_service import UserService
from backend.api.auth import get_current_user
from backend.models.enums import UserRole

router = APIRouter(prefix="/projects", tags=["Проекты"])

@router.get("/")
async def get_projects(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка проектов пользователя
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    project_service = ProjectService(db)
    projects = project_service.get_user_projects(current_user["id"], user.role.value)
    
    # Фильтрация по статусу
    if status:
        projects = [p for p in projects if p.status == status]
    
    # Пагинация
    paginated_projects = projects[offset:offset + limit]
    
    return {
        "success": True,
        "projects": [project.to_dict() for project in paginated_projects],
        "total": len(projects),
        "limit": limit,
        "offset": offset
    }

@router.post("/")
async def create_project(
    name: str,
    description: str,
    target_platform: Optional[str] = None,
    engine: Optional[str] = None,
    tags_json: Optional[str] = '[]',
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание нового проекта
    """
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []
    
    project_service = ProjectService(db)
    
    try:
        project = project_service.create_project(
            name=name,
            description=description,
            created_by=current_user["id"],
            target_platform=target_platform,
            engine=engine,
            tags=tags
        )
        
        return {
            "success": True,
            "message": "Проект успешно создан",
            "project": project.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания проекта: {str(e)}"
        )

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации о проекте
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers)
    )
    
    if not has_access and user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к проекту"
        )
    
    project_data = project.to_dict()
    
    # Добавляем статистику
    stats = project_service.get_project_stats(project_id)
    project_data["stats"] = stats
    
    # Добавляем информацию о менеджерах
    project_data["managers"] = [
        {"id": m.id, "username": m.username, "full_name": m.full_name}
        for m in project.managers
    ]
    
    # Добавляем информацию о создателе
    project_data["creator"] = {
        "id": project.creator.id,
        "username": project.creator.username,
        "full_name": project.creator.full_name
    } if project.creator else None
    
    return {
        "success": True,
        "project": project_data
    }

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    status: Optional[str] = None,
    target_platform: Optional[str] = None,
    engine: Optional[str] = None,
    tags_json: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Обновление проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers) or
        user.role == UserRole.MANAGER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления проекта"
        )
    
    # Подготовка данных для обновления
    update_data = {}
    
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if version is not None:
        update_data["version"] = version
    if status is not None:
        update_data["status"] = status
    if target_platform is not None:
        update_data["target_platform"] = target_platform
    if engine is not None:
        update_data["engine"] = engine
    if tags_json is not None:
        try:
            tags = json.loads(tags_json)
            update_data["tags"] = tags
        except json.JSONDecodeError:
            pass
    
    try:
        updated_project = project_service.update_project(project_id, **update_data)
        
        return {
            "success": True,
            "message": "Проект успешно обновлен",
            "project": updated_project.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления проекта: {str(e)}"
        )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Удаление проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        user.role == UserRole.MANAGER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления проекта"
        )
    
    success = project_service.delete_project(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления проекта"
        )
    
    return {
        "success": True,
        "message": "Проект успешно удален"
    }

@router.post("/{project_id}/managers")
async def add_manager(
    project_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Добавление менеджера проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        user.role == UserRole.MANAGER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления менеджерами проекта"
        )
    
    success = project_service.add_manager(project_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка добавления менеджера"
        )
    
    return {
        "success": True,
        "message": "Менеджер успешно добавлен"
    }

@router.delete("/{project_id}/managers/{user_id}")
async def remove_manager(
    project_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Удаление менеджера проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        user.role == UserRole.MANAGER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления менеджерами проекта"
        )
    
    success = project_service.remove_manager(project_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка удаления менеджера"
        )
    
    return {
        "success": True,
        "message": "Менеджер успешно удален"
    }

@router.post("/{project_id}/assets")
async def add_asset_to_project(
    project_id: str,
    asset_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Добавление актива в проект
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers) or
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления активами проекта"
        )
    
    success = project_service.add_asset(project_id, asset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка добавления актива"
        )
    
    return {
        "success": True,
        "message": "Актив успешно добавлен в проект"
    }

@router.delete("/{project_id}/assets/{asset_id}")
async def remove_asset_from_project(
    project_id: str,
    asset_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Удаление актива из проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers) or
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления активами проекта"
        )
    
    success = project_service.remove_asset(project_id, asset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка удаления актива"
        )
    
    return {
        "success": True,
        "message": "Актив успешно удален из проекта"
    }

@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение статистики проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers)
    )
    
    if not has_access and user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к статистике проекта"
        )
    
    stats = project_service.get_project_stats(project_id)
    
    return {
        "success": True,
        "stats": stats
    }

@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Архивирование проекта
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        project.created_by == current_user["id"] or
        any(manager.id == current_user["id"] for manager in project.managers) or
        user.role == UserRole.MANAGER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для архивации проекта"
        )
    
    success = project_service.archive_project(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка архивации проекта"
        )
    
    return {
        "success": True,
        "message": "Проект успешно архивирован"
    }

@router.get("/search")
async def search_projects(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Поиск проектов
    """
    project_service = ProjectService(db)
    
    projects = project_service.search_projects(query, current_user["id"])
    
    # Пагинация
    paginated_projects = projects[offset:offset + limit]
    
    return {
        "success": True,
        "projects": [project.to_dict() for project in paginated_projects],
        "total": len(projects),
        "limit": limit,
        "offset": offset,
        "query": query
    }