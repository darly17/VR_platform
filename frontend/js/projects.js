
/**
 * JavaScript для управления проектами
 */

class ProjectsManager {
    constructor() {
        this.currentView = 'grid';
        this.currentPage = 1;
        this.pageSize = 12;
        this.totalProjects = 0;
        this.projects = [];
        this.filters = {
            search: '',
            status: '',
            sort: 'newest'
        };
        
        this.init();
    }
    
    async init() {
        await this.loadProjects();
        this.setupEventListeners();
        this.setupModal();
        this.updateStats();
    }
    
    // Загрузка проектов
    async loadProjects() {
        try {
            const container = document.getElementById('projectsContainer');
            if (container) {
                container.innerHTML = `
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Загрузка проектов...</p>
                    </div>
                `;
            }
            
            const params = {
                limit: this.pageSize,
                offset: (this.currentPage - 1) * this.pageSize
            };
            
            // Добавляем фильтры
            if (this.filters.search) {
                params.search = this.filters.search;
            }
            
            if (this.filters.status) {
                params.status = this.filters.status;
            }
            
            if (this.filters.sort) {
                params.sort = this.filters.sort;
            }
            
            const response = await API.projects.getAll(params);
            
            if (response.success) {
                this.projects = response.data || response.projects || [];
                this.totalProjects = response.total || response.count || this.projects.length;
                
                this.renderProjects();
                this.renderPagination();
            } else {
                throw new Error(response.error || 'Ошибка загрузки проектов');
            }
        } catch (error) {
            console.error('Ошибка загрузки проектов:', error);
            
            const container = document.getElementById('projectsContainer');
            if (container) {
                container.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Не удалось загрузить проекты: ${error.message}</p>
                        <button class="btn btn-secondary" onclick="projectsManager.loadProjects()">
                            <i class="fas fa-sync-alt"></i> Повторить
                        </button>
                    </div>
                `;
            }
            
            VRARPlatform.showNotification(`Ошибка загрузки проектов: ${error.message}`, 'error');
        }
    }
    
    // Отображение проектов
    renderProjects() {
        const container = document.getElementById('projectsContainer');
        if (!container) return;
        
        if (this.projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-project-diagram"></i>
                    <h3>Проекты не найдены</h3>
                    <p>${this.filters.search ? 'Попробуйте изменить поисковый запрос' : 'Создайте первый проект'}</p>
                    ${!this.filters.search ? `
                        <button class="btn btn-primary" id="createFirstProjectBtn">
                            <i class="fas fa-plus"></i> Создать проект
                        </button>
                    ` : ''}
                </div>
            `;
            
            // Обработчик для кнопки создания первого проекта
            const createBtn = document.getElementById('createFirstProjectBtn');
            if (createBtn) {
                createBtn.addEventListener('click', () => this.showCreateModal());
            }
            
            return;
        }
        
        container.innerHTML = '';
        
        this.projects.forEach(project => {
            const projectCard = this.createProjectCard(project);
            container.appendChild(projectCard);
        });
    }
    
    // Создание карточки проекта
    createProjectCard(project) {
        const card = document.createElement('div');
        card.className = `project-card ${this.currentView === 'list' ? 'list-view' : ''}`;
        card.dataset.id = project.id;
        
        const statusClass = project.status === 'archived' ? 'status-inactive' : 'status-active';
        const statusText = project.status === 'archived' ? 'Архивный' : 'Активный';
        
        const scenariosCount = project.scenarios_count || project.scenariosCount || 0;
        const assetsCount = project.assets_count || project.assetsCount || 0;
        const testRunsCount = project.test_runs_count || project.testRunsCount || 0;
        
        const tags = project.tags || [];
        const tagsHtml = tags.slice(0, 3).map(tag => 
            `<span class="project-tag">${tag}</span>`
        ).join('');
        
        card.innerHTML = `
            <div class="project-header">
                <div class="project-icon">
                    <i class="fas fa-project-diagram"></i>
                </div>
                <div class="project-info">
                    <h3 class="project-title">${project.name}</h3>
                    <p class="project-description">${project.description || 'Без описания'}</p>
                    <div class="project-meta">
                        <span class="status-indicator ${statusClass}">${statusText}</span>
                        <span>v${project.version || '1.0.0'}</span>
                    </div>
                </div>
            </div>
            <div class="project-body">
                ${tags.length > 0 ? `
                    <div class="project-tags">
                        ${tagsHtml}
                        ${tags.length > 3 ? `<span class="project-tag">+${tags.length - 3}</span>` : ''}
                    </div>
                ` : ''}
                
                <div class="project-stats">
                    <div class="project-stat">
                        <i class="fas fa-code-branch"></i>
                        <p class="project-stat-value">${scenariosCount}</p>
                        <p class="project-stat-label">Сценариев</p>
                    </div>
                    <div class="project-stat">
                        <i class="fas fa-cube"></i>
                        <p class="project-stat-value">${assetsCount}</p>
                        <p class="project-stat-label">Активов</p>
                    </div>
                    <div class="project-stat">
                        <i class="fas fa-vial"></i>
                        <p class="project-stat-value">${testRunsCount}</p>
                        <p class="project-stat-label">Тестов</p>
                    </div>
                    <div class="project-stat">
                        <i class="fas fa-calendar"></i>
                        <p class="project-stat-value">${VRARPlatform.formatDate(project.created_at).split(' ')[0]}</p>
                        <p class="project-stat-label">Создан</p>
                    </div>
                </div>
                
                ${project.target_platform || project.engine ? `
                    <div class="project-details">
                        ${project.target_platform ? `<span><i class="fas fa-vr-cardboard"></i> ${project.target_platform}</span>` : ''}
                        ${project.engine ? `<span><i class="fas fa-cogs"></i> ${project.engine}</span>` : ''}
                    </div>
                ` : ''}
            </div>
            <div class="project-footer">
                <button class="btn btn-outline btn-sm view-project-btn" title="Открыть проект">
                    <i class="fas fa-eye"></i> Открыть
                </button>
                <button class="btn btn-outline btn-sm edit-project-btn" title="Редактировать">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline btn-sm delete-project-btn" title="Удалить">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        // Обработчики событий
        const viewBtn = card.querySelector('.view-project-btn');
        const editBtn = card.querySelector('.edit-project-btn');
        const deleteBtn = card.querySelector('.delete-project-btn');
        
        viewBtn.addEventListener('click', () => this.viewProject(project.id));
        editBtn.addEventListener('click', () => this.editProject(project.id));
        deleteBtn.addEventListener('click', () => this.deleteProject(project.id));
        
        // Клик по карточке
        card.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.viewProject(project.id);
            }
        });
        
        return card;
    }
    
    // Отображение пагинации
    renderPagination() {
        const container = document.getElementById('projectsPagination');
        if (!container) return;
        
        const totalPages = Math.ceil(this.totalProjects / this.pageSize);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let paginationHtml = '';
        
        // Кнопка "Назад"
        paginationHtml += `
            <button class="page-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
                    ${this.currentPage === 1 ? 'disabled' : ''}
                    onclick="projectsManager.changePage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;
        
        // Номера страниц
        const maxVisible = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <button class="page-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="projectsManager.changePage(${i})">
                    ${i}
                </button>
            `;
        }
        
        // Кнопка "Вперед"
        paginationHtml += `
            <button class="page-btn ${this.currentPage === totalPages ? 'disabled' : ''}" 
                    ${this.currentPage === totalPages ? 'disabled' : ''}
                    onclick="projectsManager.changePage(${this.currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        container.innerHTML = paginationHtml;
    }
    
    // Смена страницы
    changePage(page) {
        this.currentPage = page;
        this.loadProjects();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Просмотр проекта
    viewProject(id) {
        window.location.href = `/project.html?id=${id}`;
    }
    
    // Редактирование проекта
    async editProject(id) {
        try {
            const response = await API.projects.getById(id);
            if (response.success) {
                this.showEditModal(response.data);
            }
        } catch (error) {
            console.error('Ошибка загрузки проекта:', error);
            VRARPlatform.showNotification('Не удалось загрузить данные проекта', 'error');
        }
    }
    
    // Удаление проекта
    async deleteProject(id) {
        if (!confirm('Вы уверены, что хотите удалить проект? Это действие нельзя отменить.')) {
            return;
        }
        
        try {
            const response = await API.projects.delete(id);
            if (response.success) {
                VRARPlatform.showNotification('Проект успешно удален', 'success');
                await this.loadProjects();
                await this.updateStats();
            } else {
                throw new Error(response.error || 'Ошибка удаления проекта');
            }
        } catch (error) {
            console.error('Ошибка удаления проекта:', error);
            VRARPlatform.showNotification(`Ошибка удаления проекта: ${error.message}`, 'error');
        }
    }
    
    // Настройка обработчиков событий
    setupEventListeners() {
        // Поиск
        const searchInput = document.getElementById('projectSearch');
        if (searchInput) {
            const debouncedSearch = debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadProjects();
            }, 300);
            
            searchInput.addEventListener('input', debouncedSearch);
            
            // Очистка поиска
            const clearSearchBtn = document.getElementById('clearSearch');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', () => {
                    searchInput.value = '';
                    this.filters.search = '';
                    this.currentPage = 1;
                    this.loadProjects();
                });
            }
        }
        
        // Фильтры
        const filterSelect = document.getElementById('projectFilter');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.currentPage = 1;
                this.loadProjects();
            });
        }
        
        // Сортировка
        const sortSelect = document.getElementById('sortProjects');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.filters.sort = e.target.value;
                this.currentPage = 1;
                this.loadProjects();
            });
        }
        
        // Переключение вида
        const viewBtns = document.querySelectorAll('.view-btn');
        viewBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                this.currentView = view;
                
                // Обновление активной кнопки
                viewBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Обновление отображения
                this.renderProjects();
            });
        });
        
        // Обновление проектов
        const refreshBtn = document.getElementById('refreshProjectsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadProjects();
                VRARPlatform.showNotification('Список проектов обновлен', 'success');
            });
        }
    }
    
    // Настройка модального окна
    setupModal() {
        const createBtn = document.getElementById('createProjectBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateModal());
        }
        
        const modal = document.getElementById('createProjectModal');
        const closeBtn = document.getElementById('closeCreateModal');
        const cancelBtn = document.getElementById('cancelCreateProject');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal());
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal());
        }
        
        // Закрытие по клику вне модального окна
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal();
                }
            });
        }
        
        // Форма создания проекта
        const form = document.getElementById('createProjectForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleCreateProject(form);
            });
        }
    }
    
    // Показать модальное окно создания
    showCreateModal() {
        const modal = document.getElementById('createProjectModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Сброс формы
            const form = document.getElementById('createProjectForm');
            if (form) {
                form.reset();
                document.getElementById('projectName').focus();
            }
        }
    }
    
    // Показать модальное окно редактирования
    showEditModal(project) {
        // TODO: Реализовать редактирование проекта
        console.log('Редактирование проекта:', project);
        VRARPlatform.showNotification('Редактирование проекта пока не реализовано', 'info');
    }
    
    // Скрыть модальное окно
    hideModal() {
        const modal = document.getElementById('createProjectModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Обработка создания проекта
    async handleCreateProject(form) {
        const submitBtn = document.getElementById('submitCreateProject');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Создание...';
            
            const formData = new FormData(form);
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                if (key === 'tags' && value.trim()) {
                    data[key] = value.split(',').map(tag => tag.trim()).filter(tag => tag);
                } else if (value.trim()) {
                    data[key] = value.trim();
                }
            }
            
            const response = await API.projects.create(data);
            
            if (response.success) {
                VRARPlatform.showNotification('Проект успешно создан', 'success');
                this.hideModal();
                await this.loadProjects();
                await this.updateStats();
            } else {
                throw new Error(response.error || 'Ошибка создания проекта');
            }
        } catch (error) {
            console.error('Ошибка создания проекта:', error);
            
            // Показываем ошибки в форме
            const errorElement = document.getElementById('nameError');
            if (errorElement) {
                errorElement.textContent = error.message;
            }
            
            VRARPlatform.showNotification(`Ошибка создания проекта: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    // Обновление статистики
    async updateStats() {
        try {
            const response = await API.get('/status');
            if (response.success && response.database && response.database.tables) {
                const stats = response.database.tables;
                
                document.getElementById('totalProjects').textContent = stats.projects || 0;
                document.getElementById('totalScenarios').textContent = stats.scenarios || 0;
                document.getElementById('totalAssets').textContent = stats.assets || 0;
                document.getElementById('totalTests').textContent = stats.test_runs || 0;
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
}

// Создание экземпляра менеджера проектов
let projectsManager;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    projectsManager = new ProjectsManager();
});

// Глобальный экспорт
window.projectsManager = projectsManager;
