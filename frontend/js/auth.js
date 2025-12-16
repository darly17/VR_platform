// frontend/js/auth.js

function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (isAuthenticated() && (path === '/login.html' || path === '/')) {
        window.location.href = "/dashboard.html";  // <-- Если авторизован на логине — на главную
    } else if (!isAuthenticated() && path !== '/login.html' && path !== '/') {
        window.location.href = '/login.html';  // <-- Не авторизован на других страницах — на логин
    }

    const user = getCurrentUser();
    if (user) {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.textContent = `${user.full_name || user.username} (${user.role})`;
        }
    }
});

window.auth = {
    isAuthenticated,
    getCurrentUser,
    logout
};