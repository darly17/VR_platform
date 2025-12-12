"""
Утилиты для обработки файлов
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, BinaryIO
from datetime import datetime
import zipfile
import json
import logging

from backend.config import settings
from backend.models.enums import AssetType

logger = logging.getLogger(__name__)


class FileHandler:
    """Базовый класс для обработки файлов"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_data: bytes, filename: str, subdir: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Сохранение файла на диск
        Возвращает (успех, путь, метаданные)
        """
        try:
            # Создаем поддиректорию если нужно
            save_dir = self.base_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Генерируем безопасное имя файла
            safe_filename = self._generate_safe_filename(filename)
            file_path = save_dir / safe_filename
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Получаем метаданные
            metadata = self._get_file_metadata(file_path, file_data)
            
            logger.info(f"Файл сохранен: {file_path} ({metadata['size']} bytes)")
            return True, str(file_path), metadata
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            return False, "", {}
    
    def delete_file(self, file_path: str) -> bool:
        """Удаление файла"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Файл удален: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Получение информации о файле"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stats = path.stat()
            mime_type, encoding = mimetypes.guess_type(file_path)
            
            return {
                "path": str(path),
                "name": path.name,
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "mime_type": mime_type or "application/octet-stream",
                "extension": path.suffix.lower(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "parent": str(path.parent)
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о файле: {e}")
            return None
    
    def calculate_hash(self, file_path: str, algorithm: str = "sha256") -> Optional[str]:
        """Вычисление хеша файла"""
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Ошибка вычисления хеша: {e}")
            return None
    
    def copy_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """Копирование файла"""
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                return False
            
            if dest.exists() and not overwrite:
                return False
            
            shutil.copy2(source, dest)
            logger.info(f"Файл скопирован: {source_path} -> {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка копирования файла: {e}")
            return False
    
    def move_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """Перемещение файла"""
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                return False
            
            if dest.exists() and not overwrite:
                return False
            
            shutil.move(source, dest)
            logger.info(f"Файл перемещен: {source_path} -> {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка перемещения файла: {e}")
            return False
    
    def create_directory(self, dir_path: str) -> bool:
        """Создание директории"""
        try:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Директория создана: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания директории: {e}")
            return False
    
    def list_directory(self, dir_path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """Список файлов в директории"""
        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                return []
            
            files = []
            
            if recursive:
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        files.append(self._get_file_listing_info(file_path))
            else:
                for file_path in path.iterdir():
                    if file_path.is_file():
                        files.append(self._get_file_listing_info(file_path))
            
            return files
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов: {e}")
            return []
    
    def _generate_safe_filename(self, filename: str) -> str:
        """Генерация безопасного имени файла"""
        # Удаляем опасные символы
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Удаляем управляющие символы
        safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
        # Ограничиваем длину
        max_length = 255
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length - len(ext)] + ext
        
        return safe_name
    
    def _get_file_metadata(self, file_path: Path, file_data: bytes) -> Dict[str, Any]:
        """Получение метаданных файла"""
        stats = file_path.stat()
        mime_type, encoding = mimetypes.guess_type(str(file_path))
        
        # Вычисляем хеш
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        return {
            "filename": file_path.name,
            "size": len(file_data),
            "size_on_disk": stats.st_size,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "mime_type": mime_type or "application/octet-stream",
            "extension": file_path.suffix.lower(),
            "hash_sha256": file_hash,
            "path": str(file_path)
        }
    
    def _get_file_listing_info(self, file_path: Path) -> Dict[str, Any]:
        """Получение информации для списка файлов"""
        stats = file_path.stat()
        mime_type, encoding = mimetypes.guess_type(str(file_path))
        
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stats.st_size,
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "mime_type": mime_type or "application/octet-stream",
            "extension": file_path.suffix.lower(),
            "is_dir": file_path.is_dir()
        }


class AssetFileHandler(FileHandler):
    """Обработчик файлов активов"""
    
    # Поддерживаемые расширения для разных типов активов
    ASSET_EXTENSIONS = {
        AssetType.MODEL_3D.value: ['.fbx', '.obj', '.glb', '.gltf', '.stl', '.dae'],
        AssetType.TEXTURE.value: ['.png', '.jpg', '.jpeg', '.bmp', '.tga', '.tiff', '.psd'],
        AssetType.AUDIO.value: ['.wav', '.mp3', '.ogg', '.flac', '.aac'],
        AssetType.VIDEO.value: ['.mp4', '.avi', '.mov', '.wmv', '.flv'],
        AssetType.SCRIPT.value: ['.py', '.cs', '.cpp', '.js', '.ts', '.lua'],
        AssetType.MATERIAL.value: ['.mat', '.material', '.mtl'],
        AssetType.ANIMATION.value: ['.anim', '.animation', '.fbx'],
        AssetType.DOCUMENT.value: ['.pdf', '.doc', '.docx', '.txt', '.md', '.json', '.xml']
    }
    
    # Максимальные размеры для разных типов активов (в байтах)
    MAX_SIZES = {
        AssetType.MODEL_3D.value: 500 * 1024 * 1024,  # 500MB
        AssetType.TEXTURE.value: 100 * 1024 * 1024,   # 100MB
        AssetType.AUDIO.value: 50 * 1024 * 1024,      # 50MB
        AssetType.VIDEO.value: 1000 * 1024 * 1024,    # 1GB
        AssetType.SCRIPT.value: 10 * 1024 * 1024,     # 10MB
        AssetType.MATERIAL.value: 10 * 1024 * 1024,   # 10MB
        AssetType.ANIMATION.value: 200 * 1024 * 1024, # 200MB
        AssetType.DOCUMENT.value: 20 * 1024 * 1024    # 20MB
    }
    
    def __init__(self):
        super().__init__(settings.UPLOAD_DIR)
        self.asset_types_dir = self.base_dir / "assets"
        self.asset_types_dir.mkdir(exist_ok=True)
    
    def save_asset(self, file_data: bytes, filename: str, asset_type: str, 
                  user_id: str, metadata: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Сохранение актива с проверкой типа и размера
        """
        # Проверяем тип актива
        if asset_type not in self.ASSET_EXTENSIONS:
            logger.error(f"Неподдерживаемый тип актива: {asset_type}")
            return False, "", {}
        
        # Проверяем расширение файла
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ASSET_EXTENSIONS[asset_type]:
            logger.error(f"Неподдерживаемое расширение для типа {asset_type}: {file_ext}")
            return False, "", {}
        
        # Проверяем размер файла
        max_size = self.MAX_SIZES.get(asset_type, settings.MAX_UPLOAD_SIZE)
        if len(file_data) > max_size:
            logger.error(f"Файл слишком большой: {len(file_data)} > {max_size}")
            return False, "", {}
        
        # Создаем директорию для пользователя и типа актива
        user_dir = f"user_{user_id}"
        type_dir = asset_type.lower()
        subdir = f"{user_dir}/{type_dir}"
        
        # Сохраняем файл
        success, file_path, file_metadata = self.save_file(file_data, filename, subdir)
        
        if success:
            # Добавляем информацию об актив
            file_metadata.update({
                "asset_type": asset_type,
                "uploaded_by": user_id,
                "uploaded_at": datetime.now().isoformat(),
                "custom_metadata": metadata or {}
            })
            
            # Создаем миниатюру для изображений и 3D моделей
            if asset_type in [AssetType.TEXTURE.value, AssetType.MODEL_3D.value]:
                self._create_thumbnail(file_path, file_metadata)
        
        return success, file_path, file_metadata
    
    def validate_asset_file(self, file_path: str, asset_type: str) -> Tuple[bool, str]:
        """Валидация файла актива"""
        path = Path(file_path)
        
        if not path.exists():
            return False, "Файл не существует"
        
        # Проверяем расширение
        file_ext = path.suffix.lower()
        if asset_type not in self.ASSET_EXTENSIONS:
            return False, f"Неподдерживаемый тип актива: {asset_type}"
        
        if file_ext not in self.ASSET_EXTENSIONS[asset_type]:
            supported = ", ".join(self.ASSET_EXTENSIONS[asset_type])
            return False, f"Неподдерживаемое расширение. Поддерживаются: {supported}"
        
        # Проверяем размер
        max_size = self.MAX_SIZES.get(asset_type, settings.MAX_UPLOAD_SIZE)
        file_size = path.stat().st_size
        
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            return False, f"Файл слишком большой: {file_size_mb:.2f}MB > {max_size_mb:.2f}MB"
        
        return True, "Файл валиден"
    
    def get_asset_preview(self, asset_path: str, size: str = "medium") -> Optional[bytes]:
        """Получение превью актива"""
        try:
            path = Path(asset_path)
            preview_path = path.parent / f"{path.stem}_preview_{size}.jpg"
            
            if preview_path.exists():
                with open(preview_path, 'rb') as f:
                    return f.read()
            
            # Если превью нет, генерируем его для изображений
            if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                return self._generate_image_preview(asset_path, size)
            
            return None
        except Exception as e:
            logger.error(f"Ошибка получения превью: {e}")
            return None
    
    def extract_asset_metadata(self, asset_path: str, asset_type: str)