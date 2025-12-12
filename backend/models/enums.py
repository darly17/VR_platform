"""
Перечисления для моделей данных (соответствует UML диаграммам)
"""
from enum import Enum

class UserRole(str, Enum):
    """Роли пользователей из UML"""
    DEVELOPER = "developer"      # РазработчикСценариев
    DESIGNER = "designer"        # Дизайнер
    TESTER = "tester"           # Тестировщик
    MANAGER = "manager"         # МенеджерПроекта

class AssetType(str, Enum):
    """Типы активов из UML"""
    MODEL_3D = "3d_model"      # 3D модели (fbx, obj, glb)
    TEXTURE = "texture"        # Текстуры (png, jpg)
    AUDIO = "audio"           # Аудио (wav, mp3)
    VIDEO = "video"           # Видео (mp4, avi)
    SCRIPT = "script"         # Скрипты (py, cs, cpp)
    MATERIAL = "material"     # Материалы
    ANIMATION = "animation"   # Анимации
    DOCUMENT = "document"     # Документация

class DeviceType(str, Enum):
    """Типы устройств для тестирования из UML"""
    VR_HEADSET = "vr_headset"     # VR шлем (Oculus, HTC)
    AR_GLASSES = "ar_glasses"     # AR очки (HoloLens)
    MOBILE = "mobile"            # Мобильные устройства
    DESKTOP = "desktop"          # Компьютеры
    SIMULATOR = "simulator"      # Симуляторы
    CUSTOM = "custom"           # Пользовательские устройства

class ProgrammingLanguage(str, Enum):
    """Языки программирования для генерации кода из UML"""
    PYTHON = "python"
    CSHARP = "csharp"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"

class StateType(str, Enum):
    """Типы состояний из UML"""
    START = "start"           # Начальное состояние
    IDLE = "idle"            # Ожидание
    INTERACTION = "interaction"  # Взаимодействие
    ANIMATION = "animation"   # Анимация
    END = "end"             # Конечное состояние
    CONDITION = "condition"   # Условное
    PARALLEL = "parallel"    # Параллельное

class NodeType(str, Enum):
    """Типы узлов визуального скрипта из UML"""
    EVENT = "event"          # Событие
    ACTION = "action"        # Действие
    CONDITION = "condition"  # Условие
    VARIABLE = "variable"    # Переменная
    FUNCTION = "function"    # Функция
    COMMENT = "comment"      # Комментарий

class ConnectionType(str, Enum):
    """Типы соединений визуального скрипта из UML"""
    EXECUTION = "execution"  # Выполнение
    DATA = "data"           # Данные
    EVENT = "event"         # Событие

class TestStatus(str, Enum):
    """Статусы тестирования из UML"""
    PENDING = "pending"      # Ожидает
    RUNNING = "running"      # Выполняется
    PASSED = "passed"       # Пройден
    FAILED = "failed"       # Не пройден
    ERROR = "error"         # Ошибка
    CANCELLED = "cancelled"  # Отменен

class ReportFormat(str, Enum):
    """Форматы отчетов из UML"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"