"""
API эндпоинты для аутентификации
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt

from backend.database import get_db
from backend.services.user_service import UserService
from backend.config import settings
from backend.models.enums import UserRole

router = APIRouter(prefix="/auth", tags=["Аутентификация"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# JWT настройки
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """
    Создание JWT токена
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Верификация JWT токена
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(payload: Dict[str, Any] = Depends(verify_token), 
                    db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получение текущего пользователя из токена
    """
    user_service = UserService(db)
    user = user_service.get_user(payload.get("sub"))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь деактивирован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name
    }

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), 
                db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Аутентификация пользователя и получение токена
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name
        }
    }

@router.post("/register")
async def register(username: str, email: str, password: str, role: str,
                   full_name: str = None, department: str = None,
                   db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Регистрация нового пользователя
    """
    # Проверяем, что роль валидна
    if role not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимая роль. Допустимые роли: {[r.value for r in UserRole]}"
        )
    
    user_service = UserService(db)
    
    try:
        user = user_service.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            full_name=full_name,
            department=department
        )
        
        return {
            "success": True,
            "message": "Пользователь успешно зарегистрирован",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка регистрации: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user),
                               db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получение информации о текущем пользователе
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user_info = user.to_dict()
    user_info["capabilities"] = user.get_capabilities()
    
    return {
        "success": True,
        "user": user_info
    }

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user),
                db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Выход из системы (на стороне клиента - токен удаляется)
    """
    user_service = UserService(db)
    user = user_service.get_user(current_user["id"])
    
    if user:
        # В реальной системе здесь может быть инвалидация токена
        pass
    
    return {
        "success": True,
        "message": "Выход выполнен успешно"
    }

@router.post("/change-password")
async def change_password(old_password: str, new_password: str,
                         current_user: Dict[str, Any] = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Изменение пароля пользователя
    """
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен содержать не менее 6 символов"
        )
    
    user_service = UserService(db)
    success = user_service.change_password(current_user["id"], old_password, new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный старый пароль"
        )
    
    return {
        "success": True,
        "message": "Пароль успешно изменен"
    }

@router.get("/capabilities")
async def get_user_capabilities(current_user: Dict[str, Any] = Depends(get_current_user),
                               db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получение возможностей текущего пользователя
    """
    user_service = UserService(db)
    capabilities = user_service.get_user_capabilities(current_user["id"])
    
    return {
        "success": True,
        "capabilities": capabilities
    }

@router.get("/users")
async def get_users(role: str = None, department: str = None, 
                   limit: int = 50, offset: int = 0,
                   current_user: Dict[str, Any] = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получение списка пользователей (только для менеджеров)
    """
    user_service = UserService(db)
    current_user_obj = user_service.get_user(current_user["id"])
    
    if current_user_obj.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    users = user_service.search_users(role=role, department=department, 
                                     limit=limit, offset=offset)
    
    return {
        "success": True,
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str,
                         current_user: Dict[str, Any] = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Деактивация пользователя (только для менеджеров)
    """
    user_service = UserService(db)
    current_user_obj = user_service.get_user(current_user["id"])
    
    if current_user_obj.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать самого себя"
        )
    
    success = user_service.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return {
        "success": True,
        "message": "Пользователь деактивирован"
    }

@router.put("/users/{user_id}/activate")
async def activate_user(user_id: str,
                       current_user: Dict[str, Any] = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Активация пользователя (только для менеджеров)
    """
    user_service = UserService(db)
    current_user_obj = user_service.get_user(current_user["id"])
    
    if current_user_obj.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    success = user_service.activate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return {
        "success": True,
        "message": "Пользователь активирован"
    }