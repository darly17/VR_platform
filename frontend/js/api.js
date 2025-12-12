
/**
 * API клиент для VR/AR Platform
 */

const API = {
    baseURL: '/api',
    authToken: null,
    
    // Установить токен авторизации
    setAuthToken(token) {
        this.authToken = token;
        localStorage.setItem('token', token);
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
    
    // Обработка ответа
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        if (!response.ok) {
            let errorMessage = 'Произошла ошибка';
            
            if (data && data.error) {
                errorMessage = data.error;
            } else if (data && data.details) {
                errorMessage = data.details.map(d => d.message).join(', ');
            } else if (typeof data === 'string') {
                errorMessage = data;
            }
            
            throw {
                status: response.status,
                message: errorMessage,
                data: data
            };
        }
        
        return data;
    },
    
    // GET запрос
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseURL}${endpoint}`, window.location.origin);
        
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`GET ${endpoint} error:`, error);
            throw error;
        }
    },
    
    // POST запрос
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`POST ${endpoint} error:`, error);
            throw error;
        }
    },
    
    // PUT запрос
    async put(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`PUT ${endpoint} error:`, error);
            throw error;
        }
    },
    
    // DELETE запрос
    async delete(endpoint) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`DELETE ${endpoint} error:`, error);
            throw error;
        }
    },
    
    // Загрузка файла
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });
        
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Authorization': this.authToken ? `Bearer ${this.authToken}` : ''
                },
                body: formData
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`Upload to ${endpoint} error:`, error);
            throw error;
        }
    },
    
    // API методы для проектов
    projects: {
        async getAll(params = {}) {
            return await API.get('/projects', params);
        },
        
        async getById(id) {
            return await API.get(`/projects/${id}`);
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
        
        async getStats(id) {
            return await API.get(`/projects/${id}/stats`);
        }
    },
    
    // API методы для сценариев
    scenarios: {
        async getAll(projectId) {
            return await API.get(`/projects/${projectId}/scenarios`);
        },
        
        async getById(id) {
            return await API.get(`/scenarios/${id}`);
        },
        
        async create(projectId, data) {
            return await API.post(`/projects/${projectId}/scenarios`, data);
        },
        
        async update(id, data) {
            return await API.put(`/scenarios/${id}`, data);
        },
        
        async delete(id) {
            return await API.delete(`/scenarios/${id}`);
        },
        
        async execute(id) {
            return await API.post(`/scenarios/${id}/execute`);
        },
        
        async validate(id) {
            return await API.post(`/scenarios/${id}/validate`);
        },
        
        async getStateGraph(id) {
            return await API.get(`/scenarios/${id}/graph`);
        }
    },
    
    // API методы для активов
    assets: {
        async getAll(params = {}) {
            return await API.get('/assets', params);
        },
        
        async getById(id) {
            return await API.get(`/assets/${id}`);
        },
        
        async upload(data) {
            return await API.post('/assets/upload', data);
        },
        
        async update(id, data) {
            return await API.put(`/assets/${id}`, data);
        },
        
        async delete(id) {
            return await API.delete(`/assets/${id}`);
        },
        
        async search(query) {
            return await API.get('/assets/search', { query });
        },
        
        async getStats() {
            return await API.get('/assets/stats');
        }
    },
    
    // API методы для тестирования
    testing: {
        async createTestRun(data) {
            return await API.post('/testing/runs', data);
        },
        
        async getTestRun(id) {
            return await API.get(`/testing/runs/${id}`);
        },
        
        async startTestRun(id) {
            return await API.post(`/testing/runs/${id}/start`);
        },
        
        async stopTestRun(id) {
            return await API.post(`/testing/runs/${id}/stop`);
        },
        
        async getProjectTestRuns(projectId) {
            return await API.get(`/testing/projects/${projectId}/runs`);
        },
        
        async createBugReport(data) {
            return await API.post('/testing/bugs', data);
        }
    },
    
    // API методы для генерации кода
    codegen: {
        async generateFromScenario(scenarioId, language) {
            return await API.post(`/codegen/scenario/${scenarioId}`, { language });
        },
        
        async generateFromVisualScript(scriptId, language) {
            return await API.post(`/codegen/visual-script/${scriptId}`, { language });
        },
        
        async getSupportedLanguages() {
            return await API.get('/codegen/languages');
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

// Инициализация токена при загрузке
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        API.setAuthToken(token);
    }
});

// Глобальный экспорт
window.API = API;

export default API;
