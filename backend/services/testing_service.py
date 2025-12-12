"""
Сервис тестирования (TestController + ReportController)
Соответствует UML диаграмме классов модели
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
import logging
import json
from datetime import datetime

from backend.models.testing import TestRun, TestResult, Device, BugReport, test_run_devices
from backend.models.scenario import Scenario
from backend.models.project import Project
from backend.models.user import User
from backend.models.enums import TestStatus, ReportFormat, DeviceType

logger = logging.getLogger(__name__)

class TestingService:
    """
    TestController из UML - управление тестированием
    Включает ReportController для генерации отчетов
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== TestController методы ==========
    
    def create_test_run(self, name: str, scenario_id: str, project_id: str,
                       tester_id: str, is_automated: bool = True,
                       parameters: Dict = None, tags: List[str] = None) -> Optional[TestRun]:
        """
        Создать тестовый прогон (метод из UML Tester)
        """
        try:
            test_run = TestRun(
                name=name,
                scenario_id=scenario_id,
                project_id=project_id,
                tester_id=tester_id,
                is_automated=is_automated,
                parameters=parameters or {},
                tags=tags or []
            )
            
            self.db.add(test_run)
            self.db.commit()
            self.db.refresh(test_run)
            
            logger.info(f"Тестовый прогон создан: {name} (ID: {test_run.id})")
            return test_run
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания тестового прогона: {e}")
            return None
    
    def get_test_run(self, test_run_id: str) -> Optional[TestRun]:
        """Получить тестовый прогон по ID"""
        return self.db.query(TestRun).options(
            joinedload(TestRun.scenario),
            joinedload(TestRun.project),
            joinedload(TestRun.tester),
            joinedload(TestRun.devices),
            joinedload(TestRun.result),
            joinedload(TestRun.bug_reports)
        ).filter(TestRun.id == test_run_id).first()
    
    def start_test_run(self, test_run_id: str) -> Tuple[bool, str]:
        """Запустить тестовый прогон (метод из UML TestRun)"""
        test_run = self.get_test_run(test_run_id)
        if not test_run:
            return False, "Тестовый прогон не найден"
        
        if test_run.status != TestStatus.PENDING.value:
            return False, f"Тестовый прогон уже в статусе {test_run.status}"
        
        try:
            test_run.start()
            self.db.commit()
            return True, "Тестовый прогон запущен"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка запуска тестового прогона: {e}")
            return False, str(e)
    
    def stop_test_run(self, test_run_id: str) -> Tuple[bool, str]:
        """Остановить тестовый прогон (метод из UML TestRun)"""
        test_run = self.get_test_run(test_run_id)
        if not test_run:
            return False, "Тестовый прогон не найден"
        
        if test_run.status != TestStatus.RUNNING.value:
            return False, f"Тестовый прогон не выполняется (статус: {test_run.status})"
        
        try:
            test_run.stop()
            self.db.commit()
            return True, "Тестовый прогон остановлен"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка остановки тестового прогона: {e}")
            return False, str(e)
    
    def execute_test_run(self, test_run_id: str) -> Tuple[bool, str]:
        """Выполнить тестовый прогон"""
        test_run = self.get_test_run(test_run_id)
        if not test_run:
            return False, "Тестовый прогон не найден"
        
        try:
            # Запускаем тестовый прогон
            success = test_run.execute()
            self.db.commit()
            
            if success:
                return True, f"Тестовый прогон выполнен со статусом: {test_run.status}"
            else:
                return False, f"Ошибка выполнения тестового прогона: {test_run.status}"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка выполнения тестового прогона: {e}")
            return False, str(e)
    
    def add_device_to_test_run(self, test_run_id: str, device_id: str) -> bool:
        """Добавить устройство к тестовому прогону"""
        test_run = self.get_test_run(test_run_id)
        device = self.db.query(Device).filter(Device.id == device_id).first()
        
        if not test_run or not device:
            return False
        
        if device not in test_run.devices:
            test_run.devices.append(device)
            try:
                self.db.commit()
                logger.info(f"Устройство добавлено к тестовому прогону: {device_id} -> {test_run_id}")
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка добавления устройства: {e}")
                return False
        return True
    
    def get_project_test_runs(self, project_id: str, 
                             status: str = None,
                             limit: int = 50, offset: int = 0) -> List[TestRun]:
        """Получить тестовые прогоны проекта"""
        query = self.db.query(TestRun).options(
            joinedload(TestRun.scenario),
            joinedload(TestRun.tester)
        ).filter(TestRun.project_id == project_id)
        
        if status:
            query = query.filter(TestRun.status == status)
        
        return query.order_by(desc(TestRun.created_at)).limit(limit).offset(offset).all()
    
    def get_scenario_test_runs(self, scenario_id: str,
                              only_completed: bool = False) -> List[TestRun]:
        """Получить тестовые прогоны сценария"""
        query = self.db.query(TestRun).options(
            joinedload(TestRun.tester),
            joinedload(TestRun.result)
        ).filter(TestRun.scenario_id == scenario_id)
        
        if only_completed:
            completed_statuses = [TestStatus.PASSED.value, TestStatus.FAILED.value, TestStatus.ERROR.value]
            query = query.filter(TestRun.status.in_(completed_statuses))
        
        return query.order_by(desc(TestRun.created_at)).all()
    
    def create_bug_report(self, title: str, description: str, reporter_id: str,
                         scenario_id: str = None, test_run_id: str = None,
                         severity: str = "medium", steps_to_reproduce: List[str] = None,
                         expected_result: str = None, actual_result: str = None) -> Optional[BugReport]:
        """
        Создать отчет об ошибке (метод из UML Tester)
        """
        try:
            bug_report = BugReport(
                title=title,
                description=description,
                reporter_id=reporter_id,
                scenario_id=scenario_id,
                test_run_id=test_run_id,
                severity=severity,
                steps_to_reproduce=steps_to_reproduce or [],
                expected_result=expected_result,
                actual_result=actual_result
            )
            
            self.db.add(bug_report)
            self.db.commit()
            self.db.refresh(bug_report)
            
            logger.info(f"Отчет об ошибке создан: {title} (ID: {bug_report.id})")
            return bug_report
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания отчета об ошибке: {e}")
            return None
    
    def assign_bug_to_developer(self, bug_id: str, developer_id: str) -> bool:
        """Назначить ошибку разработчику (метод из UML Tester)"""
        bug_report = self.db.query(BugReport).filter(BugReport.id == bug_id).first()
        developer = self.db.query(User).filter(User.id == developer_id).first()
        
        if not bug_report or not developer:
            return False
        
        try:
            bug_report.assign_to_developer(developer_id)
            self.db.commit()
            logger.info(f"Ошибка назначена разработчику: {bug_id} -> {developer_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка назначения ошибки разработчику: {e}")
            return False
    
    # ========== DeviceController методы ==========
    
    def register_device(self, name: str, device_type: str, 
                       manufacturer: str = None, model: str = None,
                       serial_number: str = None, capabilities: List[str] = None) -> Optional[Device]:
        """Зарегистрировать устройство"""
        try:
            device = Device(
                name=name,
                device_type=device_type,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                capabilities=capabilities or []
            )
            
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            
            logger.info(f"Устройство зарегистрировано: {name} (ID: {device.id})")
            return device
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка регистрации устройства: {e}")
            return None
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Получить устройство по ID"""
        return self.db.query(Device).options(
            joinedload(Device.test_runs)
        ).filter(Device.id == device_id).first()
    
    def get_available_devices(self, device_type: str = None) -> List[Device]:
        """Получить доступные устройства"""
        query = self.db.query(Device).filter(Device.is_available == True)
        
        if device_type:
            query = query.filter(Device.device_type == device_type)
        
        return query.all()
    
    def connect_device(self, device_id: str) -> Tuple[bool, str]:
        """Подключить устройство (метод из UML Device)"""
        device = self.get_device(device_id)
        if not device:
            return False, "Устройство не найдено"
        
        try:
            device.connect()
            self.db.commit()
            return True, "Устройство подключено"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка подключения устройства: {e}")
            return False, str(e)
    
    def disconnect_device(self, device_id: str) -> Tuple[bool, str]:
        """Отключить устройство (метод из UML Device)"""
        device = self.get_device(device_id)
        if not device:
            return False, "Устройство не найдено"
        
        try:
            device.disconnect()
            self.db.commit()
            return True, "Устройство отключено"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка отключения устройства: {e}")
            return False, str(e)
    
    # ========== ReportController методы ==========
    
    def generate_test_report(self, test_run_id: str, 
                            format: str = ReportFormat.HTML.value) -> Dict[str, Any]:
        """Сгенерировать отчет теста (метод из UML TestResult)"""
        test_run = self.get_test_run(test_run_id)
        if not test_run:
            return {"error": "Тестовый прогон не найден"}
        
        if not test_run.result:
            return {"error": "Результат теста не найден"}
        
        try:
            report_content = test_run.result.generate_report(format)
            
            return {
                "success": True,
                "report": report_content,
                "format": format,
                "test_run_id": test_run_id,
                "test_run_name": test_run.name,
                "passed": test_run.result.passed,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return {"error": str(e)}
    
    def generate_comparison_report(self, scenario_id: str, 
                                  format: str = ReportFormat.JSON.value) -> Dict[str, Any]:
        """Сгенерировать сравнительный отчет по всем тестам сценария"""
        test_runs = self.get_scenario_test_runs(scenario_id, only_completed=True)
        
        if not test_runs:
            return {"error": "Нет завершенных тестовых прогонов для сценария"}
        
        try:
            report_data = {
                "scenario_id": scenario_id,
                "scenario_name": test_runs[0].scenario.name if test_runs[0].scenario else "Unknown",
                "total_test_runs": len(test_runs),
                "passed": len([tr for tr in test_runs if tr.result and tr.result.passed]),
                "failed": len([tr for tr in test_runs if tr.result and not tr.result.passed]),
                "average_execution_time_ms": self._calculate_average_execution_time(test_runs),
                "test_runs": []
            }
            
            for test_run in test_runs[:10]:  # Ограничим для отчета
                run_data = {
                    "id": test_run.id,
                    "name": test_run.name,
                    "status": test_run.status,
                    "passed": test_run.result.passed if test_run.result else False,
                    "execution_time_ms": test_run.execution_time_ms,
                    "created_at": test_run.created_at.isoformat() if test_run.created_at else None,
                    "tester": test_run.tester.username if test_run.tester else None,
                    "devices_count": len(test_run.devices),
                    "bug_reports_count": len(test_run.bug_reports)
                }
                report_data["test_runs"].append(run_data)
            
            if format == ReportFormat.JSON.value:
                report_content = json.dumps(report_data, ensure_ascii=False, indent=2)
            elif format == ReportFormat.HTML.value:
                report_content = self._generate_html_comparison_report(report_data)
            else:
                report_content = str(report_data)
            
            return {
                "success": True,
                "report": report_content,
                "format": format,
                "scenario_id": scenario_id,
                "test_runs_count": len(test_runs)
            }
        except Exception as e:
            logger.error(f"Ошибка генерации сравнительного отчета: {e}")
            return {"error": str(e)}
    
    def get_testing_stats(self, project_id: str = None) -> Dict[str, Any]:
        """Получить статистику тестирования"""
        query = self.db.query(TestRun)
        
        if project_id:
            query = query.filter(TestRun.project_id == project_id)
        
        total_runs = query.count()
        
        # Статистика по статусам
        status_stats = {}
        for status in TestStatus:
            count = query.filter(TestRun.status == status.value).count()
            status_stats[status.value] = count
        
        # Статистика по времени
        avg_time_query = query.filter(TestRun.execution_time_ms > 0)
        avg_execution_time = avg_time_query.with_entities(
            func.avg(TestRun.execution_time_ms)
        ).scalar() or 0
        
        # Статистика по устройствам
        total_devices = self.db.query(Device).count()
        available_devices = self.db.query(Device).filter(Device.is_available == True).count()
        
        return {
            "total_test_runs": total_runs,
            "status_stats": status_stats,
            "average_execution_time_ms": round(avg_execution_time, 2),
            "devices": {
                "total": total_devices,
                "available": available_devices,
                "in_use": total_devices - available_devices
            }
        }
    
    def _calculate_average_execution_time(self, test_runs: List[TestRun]) -> float:
        """Рассчитать среднее время выполнения"""
        valid_times = [tr.execution_time_ms for tr in test_runs if tr.execution_time_ms > 0]
        if not valid_times:
            return 0.0
        return sum(valid_times) / len(valid_times)
    
    def _generate_html_comparison_report(self, report_data: Dict[str, Any]) -> str:
        """Генерация HTML сравнительного отчета"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Сравнительный отчет: {report_data['scenario_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat-card {{ 
                    background: #f8f9fa; 
                    padding: 15px; 
                    border-radius: 5px; 
                    flex: 1; 
                    margin: 0 10px; 
                    text-align: center;
                    border-left: 4px solid #3498db;
                }}
                .stat-card.passed {{ border-left-color: #2ecc71; }}
                .stat-card.failed {{ border-left-color: #e74c3c; }}
                .table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .table th {{ background-color: #f2f2f2; }}
                .status-passed {{ color: #2ecc71; font-weight: bold; }}
                .status-failed {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Сравнительный отчет: {report_data['scenario_name']}</h1>
                <p>Сценарий ID: {report_data['scenario_id']} | Всего прогонов: {report_data['total_test_runs']}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card passed">
                    <h3>Успешных</h3>
                    <h2>{report_data['passed']}</h2>
                </div>
                <div class="stat-card failed">
                    <h3>Неуспешных</h3>
                    <h2>{report_data['failed']}</h2>
                </div>
                <div class="stat-card">
                    <h3>Среднее время</h3>
                    <h2>{report_data['average_execution_time_ms']:.2f} мс</h2>
                </div>
            </div>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>Название</th>
                        <th>Статус</th>
                        <th>Результат</th>
                        <th>Время (мс)</th>
                        <th>Тестировщик</th>
                        <th>Устройства</th>
                        <th>Ошибки</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for test_run in report_data['test_runs']:
            status_class = "status-passed" if test_run['passed'] else "status-failed"
            status_text = "Пройден" if test_run['passed'] else "Не пройден"
            
            html += f"""
                    <tr>
                        <td>{test_run['name']}</td>
                        <td>{test_run['status']}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{test_run['execution_time_ms']}</td>
                        <td>{test_run['tester'] or 'Не указан'}</td>
                        <td>{test_run['devices_count']}</td>
                        <td>{test_run['bug_reports_count']}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <p><strong>Дата генерации:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                <p><strong>Всего тестовых прогонов:</strong> """ + str(report_data['total_test_runs']) + """</p>
            </div>
        </body>
        </html>
        """
        
        return html