"""
API эндпоинты для управления тестированием
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from backend.database import get_db
from backend.services.testing_service import TestingService
from backend.services.scenario_service import ScenarioService
from backend.services.project_service import ProjectService
from backend.services.user_service import UserService
from backend.api.auth import get_current_user
from backend.models.enums import UserRole, TestStatus, ReportFormat, DeviceType

router = APIRouter(prefix="/testing", tags=["Тестирование"])

@router.get("/test-runs")
async def get_test_runs(
    project_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка тестовых прогонов
    """
    testing_service = TestingService(db)
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    test_runs = []
    
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
            user.role == UserRole.TESTER
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к тестовым прогонам проекта"
            )
        
        test_runs = testing_service.get_project_test_runs(project_id, status, limit, offset)
    elif scenario_id:
        # Проверяем доступ к сценарию
        scenario_service = ScenarioService(db)
        scenario = scenario_service.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сценарий не найден"
            )
        
        # Проверка прав доступа
        has_access = (
            user.role == UserRole.TESTER or
            (scenario.project and (
                scenario.project.created_by == current_user["id"] or
                any(manager.id == current_user["id"] for manager in scenario.project.managers)
            ))
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к тестовым прогонам сценария"
            )
        
        test_runs = testing_service.get_scenario_test_runs(scenario_id)
    else:
        # Получаем все тестовые прогоны пользователя (если он тестировщик)
        if user.role == UserRole.TESTER:
            from backend.models.testing import TestRun
            query = db.query(TestRun).filter(TestRun.tester_id == current_user["id"])
            
            if status:
                query = query.filter(TestRun.status == status)
            
            test_runs = query.order_by(TestRun.created_at.desc()).limit(limit).offset(offset).all()
        else:
            # Для остальных ролей возвращаем пустой список
            test_runs = []
    
    return {
        "success": True,
        "test_runs": [test_run.to_dict() for test_run in test_runs],
        "total": len(test_runs),
        "limit": limit,
        "offset": offset
    }

@router.post("/test-runs")
async def create_test_run(
    name: str,
    scenario_id: str,
    project_id: str,
    is_automated: bool = True,
    parameters_json: str = '{}',
    tags_json: str = '[]',
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание тестового прогона
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут создавать тестовые прогоны"
        )
    
    # Проверяем доступ к проекту
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверяем доступ к сценарию
    scenario_service = ScenarioService(db)
    scenario = scenario_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден"
        )
    
    # Проверяем, что сценарий принадлежит проекту
    if scenario.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сценарий не принадлежит указанному проекту"
        )
    
    # Парсим параметры и теги
    try:
        parameters = json.loads(parameters_json)
    except json.JSONDecodeError:
        parameters = {}
    
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []
    
    testing_service = TestingService(db)
    
    try:
        test_run = testing_service.create_test_run(
            name=name,
            scenario_id=scenario_id,
            project_id=project_id,
            tester_id=current_user["id"],
            is_automated=is_automated,
            parameters=parameters,
            tags=tags
        )
        
        if not test_run:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания тестового прогона"
            )
        
        return {
            "success": True,
            "message": "Тестовый прогон успешно создан",
            "test_run": test_run.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания тестового прогона: {str(e)}"
        )

@router.get("/test-runs/{test_run_id}")
async def get_test_run(
    test_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации о тестовом прогоне
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role == UserRole.MANAGER or
        (test_run.project and (
            test_run.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in test_run.project.managers)
        ))
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к тестовому прогону"
        )
    
    test_run_data = test_run.to_dict()
    
    # Добавляем подробную информацию
    test_run_data["scenario"] = {
        "id": test_run.scenario.id,
        "name": test_run.scenario.name
    } if test_run.scenario else None
    
    test_run_data["project"] = {
        "id": test_run.project.id,
        "name": test_run.project.name
    } if test_run.project else None
    
    test_run_data["tester"] = {
        "id": test_run.tester.id,
        "username": test_run.tester.username,
        "full_name": test_run.tester.full_name
    } if test_run.tester else None
    
    test_run_data["devices"] = [
        {"id": device.id, "name": device.name, "type": device.device_type}
        for device in test_run.devices
    ]
    
    if test_run.result:
        test_run_data["result"] = test_run.result.to_dict()
    
    test_run_data["bug_reports"] = [
        bug_report.to_dict() for bug_report in test_run.bug_reports
    ]
    
    return {
        "success": True,
        "test_run": test_run_data
    }

@router.post("/test-runs/{test_run_id}/start")
async def start_test_run(
    test_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Запуск тестового прогона
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role == UserRole.TESTER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для запуска тестового прогона"
        )
    
    success, message = testing_service.start_test_run(test_run_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/test-runs/{test_run_id}/stop")
async def stop_test_run(
    test_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Остановка тестового прогона
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role == UserRole.TESTER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для остановки тестового прогона"
        )
    
    success, message = testing_service.stop_test_run(test_run_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/test-runs/{test_run_id}/execute")
async def execute_test_run(
    test_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Выполнение тестового прогона
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role == UserRole.TESTER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения тестового прогона"
        )
    
    success, message = testing_service.execute_test_run(test_run_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/test-runs/{test_run_id}/devices/{device_id}")
async def add_device_to_test_run(
    test_run_id: str,
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Добавление устройства к тестовому прогону
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role == UserRole.TESTER
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления устройствами тестового прогона"
        )
    
    success = testing_service.add_device_to_test_run(test_run_id, device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка добавления устройства к тестовому прогону"
        )
    
    return {
        "success": True,
        "message": "Устройство успешно добавлено к тестовому прогону"
    }

@router.post("/bug-reports")
async def create_bug_report(
    title: str,
    description: str,
    scenario_id: Optional[str] = None,
    test_run_id: Optional[str] = None,
    severity: str = "medium",
    steps_to_reproduce_json: str = '[]',
    expected_result: Optional[str] = None,
    actual_result: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Создание отчета об ошибке
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут создавать отчеты об ошибках"
        )
    
    # Проверяем доступ к сценарию (если указан)
    if scenario_id:
        scenario_service = ScenarioService(db)
        scenario = scenario_service.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сценарий не найден"
            )
    
    # Проверяем доступ к тестовому прогону (если указан)
    if test_run_id:
        testing_service = TestingService(db)
        test_run = testing_service.get_test_run(test_run_id)
        
        if not test_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тестовый прогон не найден"
            )
        
        # Проверяем, что тестировщик имеет доступ к этому прогону
        if test_run.tester_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания отчета об ошибке для этого тестового прогона"
            )
    
    # Парсим шаги для воспроизведения
    try:
        steps_to_reproduce = json.loads(steps_to_reproduce_json)
    except json.JSONDecodeError:
        steps_to_reproduce = []
    
    testing_service = TestingService(db)
    
    try:
        bug_report = testing_service.create_bug_report(
            title=title,
            description=description,
            reporter_id=current_user["id"],
            scenario_id=scenario_id,
            test_run_id=test_run_id,
            severity=severity,
            steps_to_reproduce=steps_to_reproduce,
            expected_result=expected_result,
            actual_result=actual_result
        )
        
        if not bug_report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания отчета об ошибке"
            )
        
        return {
            "success": True,
            "message": "Отчет об ошибке успешно создан",
            "bug_report": bug_report.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания отчета об ошибке: {str(e)}"
        )

@router.post("/bug-reports/{bug_id}/assign")
async def assign_bug_to_developer(
    bug_id: str,
    developer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Назначение ошибки разработчику
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут назначать ошибки разработчикам"
        )
    
    # Проверяем, что разработчик существует
    developer = user_service.get_user(developer_id)
    
    if not developer or developer.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Указанный пользователь не является разработчиком"
        )
    
    testing_service = TestingService(db)
    
    success = testing_service.assign_bug_to_developer(bug_id, developer_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка назначения ошибки разработчику"
        )
    
    return {
        "success": True,
        "message": "Ошибка успешно назначена разработчику"
    }

@router.post("/devices")
async def register_device(
    name: str,
    device_type: str,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    serial_number: Optional[str] = None,
    capabilities_json: str = '[]',
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Регистрация устройства
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут регистрировать устройства"
        )
    
    # Проверяем тип устройства
    if device_type not in [t.value for t in DeviceType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип устройства. Допустимые типы: {[t.value for t in DeviceType]}"
        )
    
    # Парсим возможности
    try:
        capabilities = json.loads(capabilities_json)
    except json.JSONDecodeError:
        capabilities = []
    
    testing_service = TestingService(db)
    
    device = testing_service.register_device(
        name=name,
        device_type=device_type,
        manufacturer=manufacturer,
        model=model,
        serial_number=serial_number,
        capabilities=capabilities
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка регистрации устройства"
        )
    
    return {
        "success": True,
        "message": "Устройство успешно зарегистрировано",
        "device": device.to_dict()
    }

@router.get("/devices")
async def get_devices(
    device_type: Optional[str] = None,
    only_available: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение списка устройств
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут просматривать устройства"
        )
    
    testing_service = TestingService(db)
    
    if only_available:
        devices = testing_service.get_available_devices(device_type)
    else:
        from backend.models.testing import Device
        query = db.query(Device)
        
        if device_type:
            query = query.filter(Device.device_type == device_type)
        
        devices = query.all()
    
    return {
        "success": True,
        "devices": [device.to_dict() for device in devices],
        "total": len(devices)
    }

@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение информации об устройстве
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут просматривать устройства"
        )
    
    testing_service = TestingService(db)
    device = testing_service.get_device(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найден"
        )
    
    device_data = device.to_dict()
    
    # Добавляем информацию о тестовых прогонах
    device_data["test_runs"] = [
        {"id": tr.id, "name": tr.name, "status": tr.status}
        for tr in device.test_runs
    ]
    
    return {
        "success": True,
        "device": device_data
    }

@router.post("/devices/{device_id}/connect")
async def connect_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Подключение устройства
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут управлять устройствами"
        )
    
    testing_service = TestingService(db)
    
    success, message = testing_service.connect_device(device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Отключение устройства
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role != UserRole.TESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только тестировщики могут управлять устройствами"
        )
    
    testing_service = TestingService(db)
    
    success, message = testing_service.disconnect_device(device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }

@router.get("/test-runs/{test_run_id}/report")
async def generate_test_report(
    test_run_id: str,
    format: str = ReportFormat.HTML.value,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Генерация отчета теста
    """
    testing_service = TestingService(db)
    test_run = testing_service.get_test_run(test_run_id)
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тестовый прогон не найден"
        )
    
    # Проверка прав доступа
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    has_access = (
        test_run.tester_id == current_user["id"] or
        user.role in [UserRole.MANAGER, UserRole.DEVELOPER] or
        (test_run.project and (
            test_run.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in test_run.project.managers)
        ))
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для генерации отчета"
        )
    
    result = testing_service.generate_test_report(test_run_id, format)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/scenarios/{scenario_id}/comparison-report")
async def generate_comparison_report(
    scenario_id: str,
    format: str = ReportFormat.JSON.value,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Генерация сравнительного отчета по всем тестам сценария
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
        user.role in [UserRole.TESTER, UserRole.MANAGER, UserRole.DEVELOPER] or
        (scenario.project and (
            scenario.project.created_by == current_user["id"] or
            any(manager.id == current_user["id"] for manager in scenario.project.managers)
        ))
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для генерации отчета"
        )
    
    testing_service = TestingService(db)
    result = testing_service.generate_comparison_report(scenario_id, format)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/stats")
async def get_testing_stats(
    project_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получение статистики тестирования
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user.role not in [UserRole.TESTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра статистики тестирования"
        )
    
    testing_service = TestingService(db)
    stats = testing_service.get_testing_stats(project_id)
    
    return {
        "success": True,
        "stats": stats
    }