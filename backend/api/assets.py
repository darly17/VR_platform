"""
API эндпоинты для управления активами
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path

from backend.database import get_db
from backend.services.asset_service import AssetService
from backend.services.user_service import UserService
from backend.api.auth import get_current_user
from backend.models.enums import UserRole, AssetType

router = APIRouter(prefix="/assets", tags=["Активы"])

@router.get("/")
async def get_assets(
    query: Optional[str] = None,
    asset_type: Optional[str] = None,
    tags: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка активов
    """
    asset_service = AssetService(db)
    
    # Парсим теги
    tag_list = []
    if tags:
        try:
            tag_list = json.loads(tags)
        except json.JSONDecodeError:
            tag_list = tags.split(',')
    
    assets = asset_service.search_assets(
        query=query,
        asset_type=asset_type,
        tags=tag_list,
        uploaded_by=uploaded_by,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "assets": [asset.to_dict() for asset in assets],
        "total": len(assets),
        "limit": limit,
        "offset": offset
    }

@router.post("/upload")
async def upload_asset(
    name: str = Form(...),
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    metadata_json: str = Form('{}'),
    tags_json: str = Form('[]'),
    is_public: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Загрузка нового актива
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DESIGNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут загружать активы"
        )
    
    # Проверяем тип актива
    if asset_type not in [t.value for t in AssetType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип актива. Допустимые типы: {[t.value for t in AssetType]}"
        )
    
    # Парсим метаданные и теги
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError:
        metadata = {}
    
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []
    
    # Читаем файл
    file_content = await file.read()
    
    asset_service = AssetService(db)
    
    try:
        asset = asset_service.upload_asset(
            name=name,
            asset_type=asset_type,
            uploaded_by=current_user["id"],
            file_data=file_content,
            metadata=metadata,
            tags=tags,
            is_public=is_public
        )
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка загрузки актива"
            )
        
        return {
            "success": True,
            "message": "Актив успешно загружен",
            "asset": asset.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки актива: {str(e)}"
        )

@router.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации об активе
    """
    asset_service = AssetService(db)
    asset = asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Актив не найден"
        )
    
    # Проверяем доступ (публичные активы доступны всем, приватные - только владельцу)
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        asset.is_public or
        asset.uploaded_by == current_user["id"] or
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к активу"
        )
    
    asset_data = asset.to_dict()
    
    # Добавляем информацию о владельце
    asset_data["uploaded_by_user"] = {
        "id": asset.uploaded_by_user.id,
        "username": asset.uploaded_by_user.username,
        "full_name": asset.uploaded_by_user.full_name
    } if asset.uploaded_by_user else None
    
    # Добавляем информацию о библиотеках
    asset_data["libraries"] = [
        {"id": lib.id, "name": lib.name}
        for lib in asset.libraries
    ]
    
    # Добавляем информацию о проектах
    asset_data["projects"] = [
        {"id": proj.id, "name": proj.name}
        for proj in asset.projects
    ]
    
    # Добавляем информацию о файле
    file_info = asset_service.get_asset_file_info(asset_id)
    asset_data["file_info"] = file_info
    
    return {
        "success": True,
        "asset": asset_data
    }

@router.put("/{asset_id}")
async def update_asset(
    asset_id: str,
    name: Optional[str] = None,
    metadata_json: Optional[str] = None,
    tags_json: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Обновление актива
    """
    asset_service = AssetService(db)
    asset = asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Актив не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        asset.uploaded_by == current_user["id"] or
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления актива"
        )
    
    # Подготовка данных для обновления
    update_data = {}
    
    if name is not None:
        update_data["name"] = name
    
    if metadata_json is not None:
        try:
            metadata = json.loads(metadata_json)
            update_data["metadata"] = metadata
        except json.JSONDecodeError:
            pass
    
    if tags_json is not None:
        try:
            tags = json.loads(tags_json)
            update_data["tags"] = tags
        except json.JSONDecodeError:
            pass
    
    if is_public is not None:
        update_data["is_public"] = is_public
    
    try:
        updated_asset = asset_service.update_asset(asset_id, **update_data)
        
        return {
            "success": True,
            "message": "Актив успешно обновлен",
            "asset": updated_asset.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления актива: {str(e)}"
        )

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Удаление актива
    """
    asset_service = AssetService(db)
    asset = asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Актив не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        asset.uploaded_by == current_user["id"] or
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления актива"
        )
    
    success = asset_service.delete_asset(asset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления актива"
        )
    
    return {
        "success": True,
        "message": "Актив успешно удален"
    }

@router.post("/{asset_id}/load")
async def load_asset(
    asset_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Загрузка актива в память
    """
    asset_service = AssetService(db)
    asset = asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Актив не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        asset.is_public or
        asset.uploaded_by == current_user["id"] or
        user.role in [UserRole.DESIGNER, UserRole.DEVELOPER]
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для загрузки актива"
        )
    
    success, message = asset_service.load_asset(asset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/objects")
async def create_object_3d(
    name: str,
    asset_id: str,
    position_json: str = '[0, 0, 0]',
    rotation_json: str = '[0, 0, 0, 1]',
    scale_json: str = '[1, 1, 1]',
    scenario_id: Optional[str] = None,
    current_state_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание 3D объекта
    """
    try:
        position = json.loads(position_json)
    except json.JSONDecodeError:
        position = [0, 0, 0]
    
    try:
        rotation = json.loads(rotation_json)
    except json.JSONDecodeError:
        rotation = [0, 0, 0, 1]
    
    try:
        scale = json.loads(scale_json)
    except json.JSONDecodeError:
        scale = [1, 1, 1]
    
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DESIGNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут создавать 3D объекты"
        )
    
    asset_service = AssetService(db)
    
    object_3d = asset_service.create_object_3d(
        name=name,
        asset_id=asset_id,
        position=position,
        rotation=rotation,
        scale=scale,
        scenario_id=scenario_id,
        current_state_id=current_state_id
    )
    
    if not object_3d:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания 3D объекта"
        )
    
    return {
        "success": True,
        "message": "3D объект успешно создан",
        "object_3d": object_3d.to_dict()
    }

@router.get("/objects/{object_id}")
async def get_object_3d(
    object_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации о 3D объекте
    """
    asset_service = AssetService(db)
    object_3d = asset_service.get_object_3d(object_id)
    
    if not object_3d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="3D объект не найден"
        )
    
    # Проверяем доступ к связанному активу
    if object_3d.asset and not object_3d.asset.is_public:
        user_service = UserService(db)
        user = user_service.get_user(current_user["id"])
        
        has_access = (
            object_3d.asset.uploaded_by == current_user["id"] or
            user.role == UserRole.DESIGNER
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к 3D объекту"
            )
    
    object_data = object_3d.to_dict()
    
    # Добавляем информацию об активе
    if object_3d.asset:
        object_data["asset"] = {
            "id": object_3d.asset.id,
            "name": object_3d.asset.name,
            "type": object_3d.asset.asset_type
        }
    
    # Добавляем информацию о сценарии
    if object_3d.scenario:
        object_data["scenario"] = {
            "id": object_3d.scenario.id,
            "name": object_3d.scenario.name
        }
    
    # Добавляем информацию о состоянии
    if object_3d.current_state:
        object_data["current_state"] = {
            "id": object_3d.current_state.id,
            "name": object_3d.current_state.name
        }
    
    return {
        "success": True,
        "object_3d": object_data
    }

@router.put("/objects/{object_id}")
async def update_object_3d(
    object_id: str,
    name: Optional[str] = None,
    position_json: Optional[str] = None,
    rotation_json: Optional[str] = None,
    scale_json: Optional[str] = None,
    is_interactive: Optional[bool] = None,
    is_visible: Optional[bool] = None,
    current_state_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Обновление 3D объекта
    """
    asset_service = AssetService(db)
    object_3d = asset_service.get_object_3d(object_id)
    
    if not object_3d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="3D объект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут обновлять 3D объекты"
        )
    
    # Подготовка данных для обновления
    update_data = {}
    
    if name is not None:
        update_data["name"] = name
    
    if position_json is not None:
        try:
            position = json.loads(position_json)
            update_data["position_x"] = position[0] if len(position) > 0 else 0.0
            update_data["position_y"] = position[1] if len(position) > 1 else 0.0
            update_data["position_z"] = position[2] if len(position) > 2 else 0.0
        except json.JSONDecodeError:
            pass
    
    if rotation_json is not None:
        try:
            rotation = json.loads(rotation_json)
            update_data["rotation_x"] = rotation[0] if len(rotation) > 0 else 0.0
            update_data["rotation_y"] = rotation[1] if len(rotation) > 1 else 0.0
            update_data["rotation_z"] = rotation[2] if len(rotation) > 2 else 0.0
            update_data["rotation_w"] = rotation[3] if len(rotation) > 3 else 1.0
        except json.JSONDecodeError:
            pass
    
    if scale_json is not None:
        try:
            scale = json.loads(scale_json)
            update_data["scale_x"] = scale[0] if len(scale) > 0 else 1.0
            update_data["scale_y"] = scale[1] if len(scale) > 1 else 1.0
            update_data["scale_z"] = scale[2] if len(scale) > 2 else 1.0
        except json.JSONDecodeError:
            pass
    
    if is_interactive is not None:
        update_data["is_interactive"] = is_interactive
    
    if is_visible is not None:
        update_data["is_visible"] = is_visible
    
    if current_state_id is not None:
        update_data["current_state_id"] = current_state_id
    
    try:
        updated_object = asset_service.update_object_3d(object_id, **update_data)
        
        return {
            "success": True,
            "message": "3D объект успешно обновлен",
            "object_3d": updated_object.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления 3D объекта: {str(e)}"
        )

@router.post("/objects/{object_id}/interact")
async def interact_with_object(
    object_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Взаимодействие с 3D объектом
    """
    asset_service = AssetService(db)
    object_3d = asset_service.get_object_3d(object_id)
    
    if not object_3d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="3D объект не найден"
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
            detail="Недостаточно прав для взаимодействия с объектом"
        )
    
    success, message = asset_service.interact_with_object(object_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/objects/{object_id}/move")
async def move_object(
    object_id: str,
    position_json: str = '[0, 0, 0]',
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Перемещение 3D объекта
    """
    try:
        position = json.loads(position_json)
    except json.JSONDecodeError:
        position = [0, 0, 0]
    
    asset_service = AssetService(db)
    object_3d = asset_service.get_object_3d(object_id)
    
    if not object_3d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="3D объект не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        user.role == UserRole.DESIGNER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут перемещать объекты"
        )
    
    success = asset_service.move_object(object_id, position)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка перемещения объекта"
        )
    
    return {
        "success": True,
        "message": "Объект успешно перемещен"
    }

@router.post("/libraries")
async def create_asset_library(
    name: str,
    description: Optional[str] = None,
    is_public: bool = True,
    category: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание библиотеки активов
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DESIGNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут создавать библиотеки активов"
        )
    
    asset_service = AssetService(db)
    
    library = asset_service.create_asset_library(
        name=name,
        created_by=current_user["id"],
        description=description,
        is_public=is_public,
        category=category
    )
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания библиотеки активов"
        )
    
    return {
        "success": True,
        "message": "Библиотека активов успешно создана",
        "library": library.to_dict()
    }

@router.get("/libraries/{library_id}")
async def get_asset_library(
    library_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации о библиотеке активов
    """
    asset_service = AssetService(db)
    library = asset_service.get_asset_library(library_id)
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Библиотека активов не найден"
        )
    
    # Проверяем доступ
    if not library.is_public:
        user_service = UserService(db)
        user = user_service.get_user(current_user["id"])
        
        has_access = (
            library.created_by == current_user["id"] or
            user.role == UserRole.DESIGNER
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к библиотеке"
            )
    
    library_data = library.to_dict()
    
    # Добавляем информацию о создателе
    library_data["creator"] = {
        "id": library.creator.id,
        "username": library.creator.username,
        "full_name": library.creator.full_name
    } if library.creator else None
    
    # Добавляем список активов
    library_data["assets"] = [
        {"id": asset.id, "name": asset.name, "type": asset.asset_type}
        for asset in library.assets
    ]
    
    return {
        "success": True,
        "library": library_data
    }

@router.post("/libraries/{library_id}/assets/{asset_id}")
async def add_asset_to_library(
    library_id: str,
    asset_id: str,
    tags_json: str = '[]',
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Добавление актива в библиотеку
    """
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []
    
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DESIGNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут управлять библиотеками активов"
        )
    
    asset_service = AssetService(db)
    
    success = asset_service.add_asset_to_library(asset_id, library_id, tags)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка добавления актива в библиотеку"
        )
    
    return {
        "success": True,
        "message": "Актив успешно добавлен в библиотеку"
    }

@router.get("/libraries/{library_id}/search")
async def search_in_library(
    library_id: str,
    query: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Поиск активов в библиотеке
    """
    asset_service = AssetService(db)
    library = asset_service.get_asset_library(library_id)
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Библиотека активов не найден"
        )
    
    # Проверяем доступ
    if not library.is_public:
        user_service = UserService(db)
        user = user_service.get_user(current_user["id"])
        
        has_access = (
            library.created_by == current_user["id"] or
            user.role == UserRole.DESIGNER
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к библиотеке"
            )
    
    assets = asset_service.search_in_library(library_id, query)
    
    return {
        "success": True,
        "assets": [asset.to_dict() for asset in assets],
        "total": len(assets),
        "query": query
    }

@router.get("/stats")
async def get_asset_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение статистики по активам
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.DESIGNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только дизайнеры могут просматривать статистику активов"
        )
    
    asset_service = AssetService(db)
    stats = asset_service.get_asset_stats()
    
    return {
        "success": True,
        "stats": stats
    }