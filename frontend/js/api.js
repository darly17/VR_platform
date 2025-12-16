
/**
 * API клиент для VR/AR Platform
 * Полностью переписанная версия без ошибок модулей
 * Использует глобальный объект window.API для совместимости с обычными <script> тегами
 */

const API = {
    baseURL: '/api',
    authToken: null,

    // Установить токен авторизации
    setAuthToken(token) {
        this.authToken = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    },

    // Очистить токен авторизации
    clearAuthToken() {
        this.authToken = null;
        localStorage.removeItem('token');
    },

    // Создать заголовки запроса
    getHeaders(contentType = 'application/json') {
        const headers = {
            'Accept': 'application/json'
        };

        if (contentType) {
            headers['Content-Type'] = contentType;
        }

        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        return headers;
    },

    // Универсальная обработка ответа
    async handleResponse(response) {
        const contentType = response.headers.get('content-type') || '';
        let data;

        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            const error = new Error(data.detail || data.error || data || 'Неизвестная ошибка сервера');
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    },

    // Универсальные методы HTTP
    async request(method, url, body = null, contentType = 'application/json') {
        const config = {
            method,
            headers: this.getHeaders(contentType)
        };

        if (body !== null) {
            if (contentType === 'application/json' && typeof body === 'object') {
                config.body = JSON.stringify(body);
            } else {
                config.body = body;
            }
        }

        try {
            const response = await fetch(this.baseURL + url, config);
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`Ошибка ${method} запроса к ${url}:`, error);
            throw error;
        }
    },

    async get(url) {
        return await this.request('GET', url);
    },

    async post(url, data) {
        return await this.request('POST', url, data);
    },

    async put(url, data) {
        return await this.request('PUT', url, data);
    },

    async patch(url, data) {
        return await this.request('PATCH', url, data);
    },

    async delete(url) {
        return await this.request('DELETE', url);
    },

    // API методы для проектов
    projects: {
        async getAll(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await API.get(`/projects${query ? '?' + query : ''}`);
        },
        async create(data) {
            return await API.post('/projects', data);
        },
        async update(id, data) {
            return await API.put(`/projects/${id}`, data);
        },
        async delete(id) {
            return await API.delete(`/projects/${id}`);
        },
        async archive(id) {
            return await API.post(`/projects/${id}/archive`);
        },
        async search(query, limit = 20, offset = 0) {
            return await API.get(`/projects/search?query=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`);
        }
    },

    // API методы для сценариев
    scenarios: {
        async getAll(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await API.get(`/scenarios${query ? '?' + query : ''}`);
        },
        async create(data) {
            return await API.post('/scenarios', data);
        },
        async update(id, data) {
            return await API.put(`/scenarios/${id}`, data);
        },
        async delete(id) {
            return await API.delete(`/scenarios/${id}`);
        }
    },

    // API методы для активов
    assets: {
        async getAll(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await API.get(`/assets${query ? '?' + query : ''}`);
        },
        async upload(formData) {
            return await API.request('POST', '/assets/upload', formData, false);  // false - без Content-Type (для FormData)
        },
        async delete(id) {
            return await API.delete(`/assets/${id}`);
        }
    },

    // API методы для тестирования
    testing: {
        async getTestRuns(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await API.get(`/testing/test-runs${query ? '?' + query : ''}`);
        },
        async createTestRun(data) {
            return await API.post('/testing/test-runs', data);
        },
        async getStats(project_id = null) {
            const url = project_id ? `/testing/stats?project_id=${project_id}` : '/testing/stats';
            return await API.get(url);
        }
    },

    // API методы для генерации кода
    codegen: {
        async getLanguages() {
            return await API.get('/codegen/languages');
        },
        async generate(data) {
            return await API.post('/codegen/generate', data);
        },
        async getTemplates(language, template_type = null) {
            const url = template_type ? `/codegen/templates?language=${language}&template_type=${template_type}` : `/codegen/templates?language=${language}`;
            return await API.get(url);
        },
        async validateCode(code, language) {
            return await API.post('/codegen/validate', { code, language });
        }
    },

    // API методы для пользователей
    users: {
        async getCurrent() {
            return await API.get('/users/me');
        },
        async updateProfile(data) {
            return await API.put('/users/me', data);
        },
        async changePassword(data) {
            return await API.put('/users/me/password', data);
        }
    },

    // API методы для аутентификации
    auth: {
        async login(credentials) {
            return await API.post('/auth/login', credentials);
        },
        async register(data) {
            return await API.post('/auth/register', data);
        },
        async logout() {
            return await API.post('/auth/logout');
        },
        async refresh() {
            return await API.post('/auth/refresh');
        }
    }
};

// Инициализация токена при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        API.setAuthToken(token);
    }
    console.log('API.js инициализирован, токен загружен:', !!token);
});

// Глобальный экспорт для доступа из других скриптов
window.API = API;

