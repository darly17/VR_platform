"""
Модели тестирования из UML диаграммы
TestRun, TestResult, Device
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from backend.database import Base
from backend.models.enums import DeviceType, TestStatus, ReportFormat

# Таблица для связи TestRun - Device
test_run_devices = Table(
    'test_run_devices',
    Base.metadata,
    Column('test_run_id', String(36), ForeignKey('test_runs.id'), primary_key=True),
    Column('device_id', String(36), ForeignKey('devices.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)

class TestRun(Base):
    """Класс ТестовыйПрогон из UML"""
    __tablename__ = "test_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    tester_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Статус и параметры
    status = Column(String(20), default=TestStatus.PENDING.value)
    execution_time_ms = Column(Integer, default=0)  # Время выполнения в мс
    parameters = Column(JSON, default=dict)  # Параметры тестирования
    
    # Дополнительные поля
    is_automated = Column(Boolean, default=True)
    iteration = Column(Integer, default=1)  # Номер итерации
    tags = Column(JSON, default=list)
    environment = Column(JSON, default=dict)  # Окружение тестирования
    
    # Связи из UML диаграммы
    # TestRun "1" *-- "1" TestResult : производит (композиция)
    result = relationship("TestResult", back_populates="test_run", 
                         uselist=False, cascade="all, delete-orphan")
    
    # TestRun "1" o-- "1" Device : использует (агрегация)
    devices = relationship("Device", secondary=test_run_devices, 
                         back_populates="test_runs")
    
    # Tester "1" o-- "0..*" TestRun : выполняет
    tester = relationship("User", back_populates="test_runs")
    
    # Scenario "1" *-- "0..*" TestRun
    scenario = relationship("Scenario", back_populates="test_runs")
    
    # Project "1" *-- "0..*" TestRun
    project = relationship("Project", back_populates="test_runs")
    
    # Отчеты об ошибках
    bug_reports = relationship("BugReport", back_populates="test_run", 
                              cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestRun {self.name} ({self.status})>"
    
    def start(self):
        """Запустить тест (метод из UML)"""
        print(f"Запуск тестового прогона '{self.name}'...")
        self.status = TestStatus.RUNNING.value
        self.started_at = func.now()
        return True
    
    def stop(self):
        """Остановить тест (метод из UML)"""
        print(f"Остановка тестового прогона '{self.name}'...")
        
        if self.status == TestStatus.RUNNING.value:
            self.status = TestStatus.CANCELLED.value
            self.completed_at = func.now()
            
            # Рассчитываем время выполнения
            if self.started_at:
                from datetime import datetime
                if isinstance(self.started_at, datetime):
                    execution_time = (datetime.now() - self.started_at).total_seconds() * 1000
                    self.execution_time_ms = int(execution_time)
        
        return True
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "scenario_id": self.scenario_id,
            "project_id": self.project_id,
            "tester_id": self.tester_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "is_automated": self.is_automated,
            "iteration": self.iteration,
            "tags": self.tags,
            "devices_count": len(self.devices),
            "has_result": self.result is not None,
            "bug_reports_count": len(self.bug_reports)
        }
    
    def execute(self):
        """Выполнить тестовый прогон"""
        if self.status != TestStatus.PENDING.value:
            return False
        
        self.start()
        
        try:
            # Симуляция выполнения теста
            print(f"Выполнение теста сценария: {self.scenario.name if self.scenario else 'Unknown'}")
            
            # Исполняем сценарий
            if self.scenario:
                success = self.scenario.execute()
                
                # Создаем результат
                self.result = TestResult(
                    test_run_id=self.id,
                    passed=success,
                    logs=["Тест начат", f"Сценарий выполнен: {success}", "Тест завершен"],
                    errors=[] if success else ["Ошибка выполнения сценария"]
                )
                
                self.status = TestStatus.PASSED.value if success else TestStatus.FAILED.value
            else:
                self.result = TestResult(
                    test_run_id=self.id,
                    passed=False,
                    logs=["Тест начат", "Ошибка: сценарий не найден"],
                    errors=["Сценарий не найден"]
                )
                self.status = TestStatus.ERROR.value
            
        except Exception as e:
            self.result = TestResult(
                test_run_id=self.id,
                passed=False,
                logs=["Тест начат", f"Исключение: {str(e)}"],
                errors=[str(e)]
            )
            self.status = TestStatus.ERROR.value
        
        self.completed_at = func.now()
        
        # Рассчитываем время выполнения
        if self.started_at and self.completed_at:
            from datetime import datetime
            if isinstance(self.started_at, datetime) and isinstance(self.completed_at, datetime):
                execution_time = (self.completed_at - self.started_at).total_seconds() * 1000
                self.execution_time_ms = int(execution_time)
        
        print(f"Тестовый прогон завершен со статусом: {self.status}")
        return True
    
    def add_device(self, device):
        """Добавить устройство для тестирования"""
        if device not in self.devices:
            self.devices.append(device)
            print(f"Устройство '{device.name}' добавлено к тестовому прогону")
            return True
        return False


class TestResult(Base):
    """Класс РезультатТеста из UML"""
    __tablename__ = "test_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_run_id = Column(String(36), ForeignKey("test_runs.id"), nullable=False, unique=True)
    passed = Column(Boolean, default=False)  # Пройден из UML
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Логи и ошибки из UML
    logs = Column(JSON, default=list)  # List<String>
    errors = Column(JSON, default=list)  # List<String>
    
    # Дополнительные поля
    warnings = Column(JSON, default=list)
    performance_metrics = Column(JSON, default=dict)
    screenshots = Column(JSON, default=list)  # Пути к скриншотам
    video_recording = Column(String(500))  # Путь к записи видео
    
    # Связи из UML диаграммы
    # TestRun "1" *-- "1" TestResult : производит
    test_run = relationship("TestRun", back_populates="result")
    
    def __repr__(self):
        return f"<TestResult {'PASSED' if self.passed else 'FAILED'}>"
    
    def generate_report(self, format=ReportFormat.HTML.value):
        """Сгенерировать отчет (метод из UML)"""
        print(f"Генерация отчета теста в формате {format}...")
        
        if format == ReportFormat.HTML.value:
            report = self._generate_html_report()
        elif format == ReportFormat.JSON.value:
            report = self._generate_json_report()
        elif format == ReportFormat.MARKDOWN.value:
            report = self._generate_markdown_report()
        else:
            report = f"Отчет в формате {format} не поддерживается"
        
        return report
    
    def _generate_html_report(self):
        """Генерация HTML отчета"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Отчет теста: {self.test_run.name if self.test_run else 'Unknown'}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .result {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .passed {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .failed {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .logs {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .error {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Отчет теста: {self.test_run.name if self.test_run else 'Unknown'}</h1>
                <p>Время: {self.created_at.isoformat() if self.created_at else 'N/A'}</p>
            </div>
            
            <div class="result {'passed' if self.passed else 'failed'}">
                <h2>Результат: {'ПРОЙДЕН' if self.passed else 'НЕ ПРОЙДЕН'}</h2>
            </div>
            
            <div>
                <h3>Статистика:</h3>
                <p>Всего логов: {len(self.logs)}</p>
                <p>Ошибок: {len(self.errors)}</p>
                <p>Предупреждений: {len(self.warnings)}</p>
            </div>
            
            <div class="logs">
                <h3>Логи выполнения:</h3>
                <ul>
                    {''.join(f'<li>{log}</li>' for log in self.logs)}
                </ul>
            </div>
            
            {f'<div class="logs"><h3>Ошибки:</h3><ul>{"".join(f"<li class=\"error\">{error}</li>" for error in self.errors)}</ul></div>' if self.errors else ''}
        </body>
        </html>
        """
        return html
    
    def _generate_json_report(self):
        """Генерация JSON отчета"""
        import json
        report_data = {
            "test_run_id": self.test_run_id,
            "test_run_name": self.test_run.name if self.test_run else None,
            "passed": self.passed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "logs_count": len(self.logs),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "logs": self.logs,
            "errors": self.errors,
            "warnings": self.warnings,
            "performance_metrics": self.performance_metrics
        }
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_markdown_report(self):
        """Генерация Markdown отчета"""
        markdown = f"""# Отчет теста: {self.test_run.name if self.test_run else 'Unknown'}

**Время:** {self.created_at.isoformat() if self.created_at else 'N/A'}

## Результат: {'✅ ПРОЙДЕН' if self.passed else '❌ НЕ ПРОЙДЕН'}

## Статистика
- Всего логов: {len(self.logs)}
- Ошибок: {len(self.errors)}
- Предупреждений: {len(self.warnings)}

## Логи выполнения
{chr(10).join(f'- {log}' for log in self.logs)}

"""
        if self.errors:
            markdown += f"""
## Ошибки
{chr(10).join(f'- ❌ {error}' for error in self.errors)}
"""
        
        return markdown
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "test_run_id": self.test_run_id,
            "passed": self.passed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "logs_count": len(self.logs),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "performance_metrics": self.performance_metrics,
            "has_screenshots": len(self.screenshots) > 0,
            "has_video": bool(self.video_recording)
        }
    
    def add_log(self, message):
        """Добавить запись в лог"""
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
        return True
    
    def add_error(self, error_message):
        """Добавить ошибку"""
        self.errors.append(error_message)
        self.passed = False
        return True


class Device(Base):
    """Класс Устройство из UML"""
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    device_type = Column(String(50))  # ТипУстройства из UML
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Возможности из UML (List<Возможность>)
    capabilities = Column(JSON, default=list)
    
    # Дополнительные поля
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    firmware_version = Column(String(50))
    ip_address = Column(String(50))
    is_connected = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    properties = Column(JSON, default=dict)
    
    # Связи из UML диаграммы
    # TestRun "1" o-- "1" Device : использует (через таблицу)
    test_runs = relationship("TestRun", secondary=test_run_devices,
                           back_populates="devices")
    
    def __repr__(self):
        return f"<Device {self.name} ({self.device_type})>"
    
    def connect(self):
        """Подключить устройство (метод из UML)"""
        print(f"Подключение устройства '{self.name}'...")
        self.is_connected = True
        self.last_seen = func.now()
        return True
    
    def disconnect(self):
        """Отключить устройство (метод из UML)"""
        print(f"Отключение устройства '{self.name}'...")
        self.is_connected = False
        return True
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "is_connected": self.is_connected,
            "is_available": self.is_available,
            "capabilities": self.capabilities,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "test_runs_count": len(self.test_runs)
        }
    
    def check_capability(self, capability):
        """Проверить наличие возможности"""
        return capability in self.capabilities
    
    def add_capability(self, capability):
        """Добавить возможность"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
        return True
    
    def get_status(self):
        """Получить статус устройства"""
        return {
            "name": self.name,
            "type": self.device_type,
            "connected": self.is_connected,
            "available": self.is_available,
            "last_seen": self.last_seen,
            "capabilities_count": len(self.capabilities),
            "active_tests": len([tr for tr in self.test_runs if tr.status == TestStatus.RUNNING.value])
        }


class BugReport(Base):
    """Отчет об ошибке (дополнительный класс)"""
    __tablename__ = "bug_reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    scenario_id = Column(String(36), ForeignKey("scenarios.id"))
    test_run_id = Column(String(36), ForeignKey("test_runs.id"))
    reporter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Статус и приоритет
    status = Column(String(20), default="open")  # open, assigned, in_progress, resolved, closed
    severity = Column(String(20), default="medium")  # critical, high, medium, low
    priority = Column(Integer, default=3)
    
    # Дополнительные поля
    steps_to_reproduce = Column(JSON, default=list)
    expected_result = Column(Text)
    actual_result = Column(Text)
    screenshots = Column(JSON, default=list)
    logs = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    
    # Связи
    scenario = relationship("Scenario")
    test_run = relationship("TestRun", back_populates="bug_reports")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_bugs")
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<BugReport {self.title} ({self.status})>"
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "scenario_id": self.scenario_id,
            "test_run_id": self.test_run_id,
            "reporter_id": self.reporter_id,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "severity": self.severity,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "steps_count": len(self.steps_to_reproduce),
            "screenshots_count": len(self.screenshots),
            "tags": self.tags
        }
    
    def assign_to_developer(self, developer_id):
        """Назначить ошибку разработчику"""
        self.assigned_to = developer_id
        self.status = "assigned"
        print(f"Ошибка '{self.title}' назначена разработчику {developer_id}")
        return True