
/**
 * Основной JavaScript файл для VR/AR Platform
 */

// Глобальный объект приложения
const VRARPlatform = {
    config: {},
    user: null,
    api: null,
    
    // Инициализация приложения
    init() {
        this.loadConfig();
        this.checkAuth();
        this.setupEventListeners();
        this.setupNavigation();
        this.setupNotifications();
    },
    
    // Загрузка конфигурации
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                console.log('Конфигурация загружена:', this.config);
            }
        } catch (error) {
            console.error('Ошибка загрузки конфигурации:', error);
        }
    },
    
    // Проверка аутентификации
    checkAuth() {
        const userStr = localStorage.getItem('user');
        const token = localStorage.getItem('token');
        
        if (userStr && token) {
            try {
                this.user = JSON.parse(userStr);
                this.setupAuthHeader(token);
                this.updateUIForAuth();
            } catch (error) {
                console.error('Ошибка парсинга данных пользователя:', error);
                this.logout();
            }
        }
    },
    
    // Настройка заголовка авторизации
    setupAuthHeader(token) {
        if (window.API) {
            window.API.setAuthToken(token);
        }
    },
    
    // Обновление UI после аутентификации
    updateUIForAuth() {
        const navUser = document.getElementById('navUser');
        if (navUser && this.user) {
            navUser.innerHTML = `
                <div class="user-dropdown">
                    <button class="user-btn">
                        <i class="fas fa-user-circle"></i>
                        <span>${this.user.username}</span>
                        <i class="fas fa-caret-down"></i>
                    </button>
                    <div class="dropdown-menu">
                        <a href="#" class="dropdown-item" data-page="profile">
                            <i class="fas fa-user"></i> Профиль
                        </a>
                        <a href="#" class="dropdown-item" data-page="settings">
                            <i class="fas fa-cog"></i> Настройки
                        </a>
                        <div class="dropdown-divider"></div>
                        <a href="#" class="dropdown-item logout-btn">
                            <i class="fas fa-sign-out-alt"></i> Выйти
                        </a>
                    </div>
                </div>
            `;
        }
    },
    
    // Выход из системы
    logout() {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        this.user = null;
        
        if (window.API) {
            window.API.clearAuthToken();
        }
        
        window.location.href = '/';
    },
    
    // Настройка обработчиков событий
    setupEventListeners() {
        // Обработчик выхода
        document.addEventListener('click', (e) => {
            if (e.target.closest('.logout-btn')) {
                e.preventDefault();
                this.logout();
            }
            
            // Навигация из выпадающего меню
            if (e.target.closest('.dropdown-item[data-page]')) {
                e.preventDefault();
                const page = e.target.closest('.dropdown-item[data-page]').dataset.page;
                this.navigateTo(page);
            }
        });
        
        // Обработчик мобильной навигации
        const navToggle = document.getElementById('navToggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => {
                const navLinks = document.getElementById('navLinks');
                navLinks.classList.toggle('show');
            });
        }
        
        // Закрытие мобильной навигации при клике вне
        document.addEventListener('click', (e) => {
            const navLinks = document.getElementById('navLinks');
            const navToggle = document.getElementById('navToggle');
            
            if (navLinks && navToggle && 
                !navLinks.contains(e.target) && 
                !navToggle.contains(e.target)) {
                navLinks.classList.remove('show');
            }
        });
    },
    
    // Настройка навигации
    setupNavigation() {
        // Подсветка активной страницы
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href');
            if (linkPath === currentPath || 
                (linkPath !== '/' && currentPath.startsWith(linkPath))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        
        // Обработка навигационных ссылок
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link');
            if (navLink && !navLink.classList.contains('active')) {
                navLinks.forEach(link => link.classList.remove('active'));
                navLink.classList.add('active');
            }
        });
    },
    
    // Настройка системы уведомлений
    setupNotifications() {
        // Создание контейнера для уведомлений
        if (!document.getElementById('notifications')) {
            const notificationsDiv = document.createElement('div');
            notificationsDiv.id = 'notifications';
            document.body.appendChild(notificationsDiv);
        }
    },
    
    // Показать уведомление
    showNotification(message, type = 'info', duration = 5000) {
        const notifications = document.getElementById('notifications');
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getNotificationIcon(type);
        
        notification.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <div class="notification-content">${message}</div>
            <button class="notification-close">&times;</button>
        `;
        
        notifications.appendChild(notification);
        
        // Закрытие по клику
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
        
        return notification;
    },
    
    // Получить иконку для типа уведомления
    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    // Навигация
    navigateTo(page) {
        const pages = {
            'profile': '/profile.html',
            'settings': '/settings.html',
            'projects': '/projects.html',
            'scenarios': '/scenario_editor.html',
            'assets': '/assets.html',
            'testing': '/testing.html',
            'codegen': '/codegen.html'
        };
        
        if (pages[page]) {
            window.location.href = pages[page];
        }
    },
    
    // Форматирование даты
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Форматирование размера файла
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Б';
        
        const k = 1024;
        const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    // Получить цвет для роли
    getRoleColor(role) {
        const colors = {
            'developer': 'var(--developer-color)',
            'designer': 'var(--designer-color)',
            'tester': 'var(--tester-color)',
            'manager': 'var(--manager-color)'
        };
        return colors[role] || 'var(--gray-color)';
    },
    
    // Получить иконку для роли
    getRoleIcon(role) {
        const icons = {
            'developer': 'laptop-code',
            'designer': 'paint-brush',
            'tester': 'vial',
            'manager': 'user-tie'
        };
        return icons[role] || 'user';
    }
};

// Инициализация приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    VRARPlatform.init();
});

// Глобальный экспорт
window.VRARPlatform = VRARPlatform;

// Вспомогательные функции
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
