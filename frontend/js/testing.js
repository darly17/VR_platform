/**
 * JavaScript для тестирования сценариев
 */

class TestingManager {
    constructor() {
        this.testRuns = [];
        this.devices = [];
        this.bugReports = [];
        this.currentTab = 'testRuns';
        this.chart = null;
        
        this.init();
    }
    
    async init() {
        await this.loadTestRuns();
        await this.loadDevices();
        await this.loadBugReports();
        await this.loadProjects();
        this.setupEventListeners();
        this.setupModal();
        this.updateStats();
        this.setupChart();
    }
    
    // Загрузка прогонов тестов
    async loadTestRuns() {
        try {
            const container = document.getElementById('testRunsList');
            if (container) {
                container.innerHTML = `
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Загрузка прогонов тестов...</p>
                    </div>
                `;
            }
            
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.testRuns = [
                {
                    id: 1,
                    name: 'VR Обучение - Полный прогон',
                    project: 'Образовательный проект',
                    scenario: 'VR Обучение',
                    status: 'passed',
                    duration: '2 мин 34 сек',
                    started_at: '2024-01-15T10:30:00',
                    passed_tests: 24,
                    failed_tests: 0,
                    total_tests: 24
                },
                {
                    id: 2,
                    name: 'AR Навигация - Тест интерфейса',
                    project: 'Городской гид',
                    scenario: 'AR Навигация',
                    status: 'failed',
                    duration: '1 мин 15 сек',
                    started_at: '2024-01-15T09:15:00',
                    passed_tests: 8,
                    failed_tests: 3,
                    total_tests: 11
                },
                {
                    id: 3,
                    name: 'Виртуальная экскурсия - Производительность',
                    project: 'Музей VR',
                    scenario: 'Виртуальная экскурсия',
                    status: 'running',
                    duration: '45 сек',
                    started_at: '2024-01-15T11:00:00',
                    passed_tests: 12,
                    failed_tests: 0,
                    total_tests: 20
                },
                {
                    id: 4,
                    name: 'Игровой сценарий - Механики',
                    project: 'VR Игра',
                    scenario: 'Игровой сценарий',
                    status: 'pending',
                    duration: '0 сек',
                    started_at: '2024-01-14T16:45:00',
                    passed_tests: 0,
                    failed_tests: 0,
                    total_tests: 18
                }
            ];
            
            this.renderTestRuns();
        } catch (error) {
            console.error('Ошибка загрузки прогонов:', error);
            
            const container = document.getElementById('testRunsList');
            if (container) {
                container.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Не удалось загрузить прогоны тестов: ${error.message}</p>
                        <button class="btn btn-secondary" onclick="testingManager.loadTestRuns()">
                            <i class="fas fa-sync-alt"></i> Повторить
                        </button>
                    </div>
                `;
            }
            
            VRARPlatform.showNotification(`Ошибка загрузки прогонов: ${error.message}`, 'error');
        }
    }
    
    // Отображение прогонов тестов
    renderTestRuns() {
        const container = document.getElementById('testRunsList');
        if (!container) return;
        
        if (this.testRuns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-vial"></i>
                    <h3>Прогоны тестов не найдены</h3>
                    <p>Создайте первый прогон тестов</p>
                    <button class="btn btn-primary" id="createFirstTestRunBtn">
                        <i class="fas fa-plus"></i> Создать прогон
                    </button>
                </div>
            `;
            
            const createBtn = document.getElementById('createFirstTestRunBtn');
            if (createBtn) {
                createBtn.addEventListener('click', () => this.showCreateTestRunModal());
            }
            
            return;
        }
        
        container.innerHTML = this.testRuns.map(run => `
            <div class="test-run-card ${run.status}">
                <div class="test-run-header">
                    <div class="test-run-info">
                        <h4>${run.name}</h4>
                        <div class="test-run-meta">
                            <span><i class="fas fa-project-diagram"></i> ${run.project}</span>
                            <span><i class="fas fa-code-branch"></i> ${run.scenario}</span>
                            <span><i class="fas fa-clock"></i> ${run.duration}</span>
                            <span><i class="fas fa-calendar"></i> ${VRARPlatform.formatDate(run.started_at).split(' ')[0]}</span>
                        </div>
                    </div>
                    <div class="test-run-status">
                        <span class="status-indicator status-${run.status}">
                            ${this.getStatusText(run.status)}
                        </span>
                    </div>
                </div>
                
                <div class="test-run-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${run.status}" 
                             style="width: ${(run.passed_tests / run.total_tests) * 100}%">
                        </div>
                    </div>
                    <div class="progress-label">
                        <span>${run.passed_tests} / ${run.total_tests} тестов пройдено</span>
                        <span>${Math.round((run.passed_tests / run.total_tests) * 100)}%</span>
                    </div>
                </div>
                
                <div class="test-run-footer">
                    <div class="test-run-actions">
                        <button class="btn btn-outline btn-sm view-details-btn" data-id="${run.id}" title="Детали">
                            <i class="fas fa-eye"></i> Детали
                        </button>
                        ${run.status === 'running' ? `
                            <button class="btn btn-danger btn-sm stop-test-btn" data-id="${run.id}" title="Остановить">
                                <i class="fas fa-stop"></i> Остановить
                            </button>
                        ` : ''}
                        ${run.status === 'pending' ? `
                            <button class="btn btn-primary btn-sm start-test-btn" data-id="${run.id}" title="Запустить">
                                <i class="fas fa-play"></i> Запустить
                            </button>
                        ` : ''}
                        <button class="btn btn-outline btn-sm report-bug-btn" data-id="${run.id}" title="Сообщить об ошибке">
                            <i class="fas fa-bug"></i> Баг
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Обработчики кнопок
        container.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', () => this.viewTestRunDetails(btn.dataset.id));
        });
        
        container.querySelectorAll('.stop-test-btn').forEach(btn => {
            btn.addEventListener('click', () => this.stopTestRun(btn.dataset.id));
        });
        
        container.querySelectorAll('.start-test-btn').forEach(btn => {
            btn.addEventListener('click', () => this.startTestRun(btn.dataset.id));
        });
        
        container.querySelectorAll('.report-bug-btn').forEach(btn => {
            btn.addEventListener('click', () => this.reportBug(btn.dataset.id));
        });
    }
    
    // Получение текста статуса
    getStatusText(status) {
        const texts = {
            'passed': 'Успешно',
            'failed': 'Провалено',
            'running': 'В процессе',
            'pending': 'Ожидание',
            'stopped': 'Остановлено'
        };
        return texts[status] || status;
    }
    
    // Загрузка устройств
    async loadDevices() {
        try {
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            this.devices = [
                {
                    id: 1,
                    name: 'Oculus Quest 2',
                    type: 'VR Headset',
                    manufacturer: 'Meta',
                    os: 'Android',
                    connection: 'Wi-Fi',
                    status: 'available'
                },
                {
                    id: 2,
                    name: 'Samsung S21',
                    type: 'AR Smartphone',
                    manufacturer: 'Samsung',
                    os: 'Android 13',
                    connection: 'USB',
                    status: 'busy'
                },
                {
                    id: 3,
                    name: 'HTC Vive Pro',
                    type: 'VR Headset',
                    manufacturer: 'HTC',
                    os: 'Windows',
                    connection: 'Cable',
                    status: 'available'
                },
                {
                    id: 4,
                    name: 'iPhone 14 Pro',
                    type: 'AR Smartphone',
                    manufacturer: 'Apple',
                    os: 'iOS 16',
                    connection: 'Wi-Fi',
                    status: 'maintenance'
                }
            ];
            
            this.renderDevices();
        } catch (error) {
            console.error('Ошибка загрузки устройств:', error);
        }
    }
    
    // Отображение устройств
    renderDevices() {
        const container = document.getElementById('devicesList');
        if (!container) return;
        
        container.innerHTML = this.devices.map(device => `
            <div class="device-card">
                <div class="device-header">
                    <i class="fas fa-${device.type.includes('VR') ? 'vr-cardboard' : 'mobile-alt'}"></i>
                    <div class="device-info">
                        <h3>${device.name}</h3>
                        <span class="status-indicator status-${device.status === 'available' ? 'active' : 'inactive'}">
                            ${device.status === 'available' ? 'Доступно' : 
                              device.status === 'busy' ? 'Занято' : 'Обслуживание'}
                        </span>
                    </div>
                </div>
                <div class="device-body">
                    <p><strong>Тип:</strong> ${device.type}</p>
                    <p><strong>Производитель:</strong> ${device.manufacturer}</p>
                    <p><strong>ОС:</strong> ${device.os}</p>
                    <p><strong>Подключение:</strong> ${device.connection}</p>
                </div>
                <div class="device-footer">
                    <button class="btn btn-outline btn-sm connect-btn" data-id="${device.id}" 
                            ${device.status !== 'available' ? 'disabled' : ''}>
                        ${device.status === 'available' ? 'Подключиться' : 'Недоступно'}
                    </button>
                    <button class="btn btn-outline btn-sm edit-device-btn" data-id="${device.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Обработчики кнопок
        container.querySelectorAll('.connect-btn').forEach(btn => {
            btn.addEventListener('click', () => this.connectToDevice(btn.dataset.id));
        });
        
        container.querySelectorAll('.edit-device-btn').forEach(btn => {
            btn.addEventListener('click', () => this.editDevice(btn.dataset.id));
        });
    }
    
    // Загрузка багрепортов
    async loadBugReports() {
        try {
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            this.bugReports = [
                {
                    id: 1,
                    title: 'Краш при загрузке текстур',
                    severity: 'critical',
                    status: 'open',
                    test_run: 'VR Обучение - Полный прогон',
                    reporter: 'Иван Петров',
                    created_at: '2024-01-15T10:45:00',
                    description: 'Приложение крашится при загрузке текстур высокого разрешения'
                },
                {
                    id: 2,
                    title: 'Не работает навигация в AR',
                    severity: 'high',
                    status: 'in_progress',
                    test_run: 'AR Навигация - Тест интерфейса',
                    reporter: 'Анна Сидорова',
                    created_at: '2024-01-15T09:30:00',
                    description: 'Навигационные стрелки не отображаются в AR режиме'
                },
                {
                    id: 3,
                    title: 'Оптимизация производительности',
                    severity: 'medium',
                    status: 'resolved',
                    test_run: 'Виртуальная экскурсия - Производительность',
                    reporter: 'Петр Иванов',
                    created_at: '2024-01-14T17:20:00',
                    description: 'Низкая частота кадров в некоторых залах музея'
                }
            ];
            
            this.renderBugReports();
        } catch (error) {
            console.error('Ошибка загрузки багрепортов:', error);
        }
    }
    
    // Отображение багрепортов
    renderBugReports() {
        const container = document.getElementById('bugReportsList');
        if (!container) return;
        
        if (this.bugReports.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bug"></i>
                    <h3>Багрепорты не найдены</h3>
                    <p>Сообщите о первой ошибке</p>
                    <button class="btn btn-primary" id="createFirstBugReportBtn">
                        <i class="fas fa-plus"></i> Сообщить об ошибке
                    </button>
                </div>
            `;
            
            const createBtn = document.getElementById('createFirstBugReportBtn');
            if (createBtn) {
                createBtn.addEventListener('click', () => this.showBugReportModal());
            }
            
            return;
        }
        
        container.innerHTML = this.bugReports.map(bug => `
            <div class="bug-report-card">
                <div class="bug-report-header">
                    <div class="bug-report-info">
                        <h4>${bug.title}</h4>
                        <div class="bug-report-meta">
                            <span class="severity-${bug.severity}">
                                <i class="fas fa-exclamation-circle"></i> ${this.getSeverityText(bug.severity)}
                            </span>
                            <span class="status-${bug.status}">
                                ${this.getBugStatusText(bug.status)}
                            </span>
                            <span><i class="fas fa-vial"></i> ${bug.test_run}</span>
                            <span><i class="fas fa-user"></i> ${bug.reporter}</span>
                            <span><i class="fas fa-calendar"></i> ${VRARPlatform.formatDate(bug.created_at).split(' ')[0]}</span>
                        </div>
                    </div>
                </div>
                
                <div class="bug-report-body">
                    <p>${bug.description}</p>
                </div>
                
                <div class="bug-report-footer">
                    <div class="bug-report-actions">
                        <button class="btn btn-outline btn-sm view-bug-btn" data-id="${bug.id}" title="Детали">
                            <i class="fas fa-eye"></i> Детали
                        </button>
                        <button class="btn btn-outline btn-sm assign-bug-btn" data-id="${bug.id}" title="Назначить">
                            <i class="fas fa-user-check"></i> Назначить
                        </button>
                        <button class="btn btn-outline btn-sm close-bug-btn" data-id="${bug.id}" title="Закрыть">
                            <i class="fas fa-check"></i> Закрыть
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Обработчики кнопок
        container.querySelectorAll('.view-bug-btn').forEach(btn => {
            btn.addEventListener('click', () => this.viewBugDetails(btn.dataset.id));
        });
        
        container.querySelectorAll('.assign-bug-btn').forEach(btn => {
            btn.addEventListener('click', () => this.assignBug(btn.dataset.id));
        });
        
        container.querySelectorAll('.close-bug-btn').forEach(btn => {
            btn.addEventListener('click', () => this.closeBug(btn.dataset.id));
        });
    }
    
    // Получение текста серьезности
    getSeverityText(severity) {
        const texts = {
            'critical': 'Критическая',
            'high': 'Высокая',
            'medium': 'Средняя',
            'low': 'Низкая'
        };
        return texts[severity] || severity;
    }
    
    // Получение текста статуса бага
    getBugStatusText(status) {
        const texts = {
            'open': 'Открыт',
            'in_progress': 'В работе',
            'resolved': 'Решен',
            'closed': 'Закрыт',
            'reopened': 'Переоткрыт'
        };
        return texts[status] || status;
    }
    
    // Загрузка проектов для фильтров
    async loadProjects() {
        try {
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            const projects = [
                { id: 1, name: 'Образовательный проект' },
                { id: 2, name: 'Городской гид' },
                { id: 3, name: 'Музей VR' },
                { id: 4, name: 'VR Игра' }
            ];
            
            // Заполняем селекты проектов
            const projectSelects = [
                'testProjectFilter',
                'testRunProject',
                'assetProjectFilter'
            ];
            
            projectSelects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    select.innerHTML = '<option value="">Все проекты</option>' +
                        projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
                }
            });
        } catch (error) {
            console.error('Ошибка загрузки проектов:', error);
        }
    }
    
    // Настройка обработчиков событий
    setupEventListeners() {
        // Вкладки
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
        
        // Фильтры
        const searchInput = document.getElementById('testSearch');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => {
                this.filterTestRuns();
            }, 300));
        }
        
        const statusFilter = document.getElementById('testStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.filterTestRuns();
            });
        }
        
        // Кнопки действий
        const createTestRunBtn = document.getElementById('createTestRunBtn');
        if (createTestRunBtn) {
            createTestRunBtn.addEventListener('click', () => this.showCreateTestRunModal());
        }
        
        const refreshBtn = document.getElementById('refreshTestsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadTestRuns();
                VRARPlatform.showNotification('Данные обновлены', 'success');
            });
        }
        
        const addDeviceBtn = document.getElementById('addDeviceBtn');
        if (addDeviceBtn) {
            addDeviceBtn.addEventListener('click', () => this.showAddDeviceModal());
        }
        
        const createBugReportBtn = document.getElementById('createBugReportBtn');
        if (createBugReportBtn) {
            createBugReportBtn.addEventListener('click', () => this.showBugReportModal());
        }
        
        const generateReportBtn = document.getElementById('generateReportBtn');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', () => this.generateReport());
        }
    }
    
    // Настройка модальных окон
    setupModal() {
        // Модальное окно создания прогона
        const createModal = document.getElementById('createTestRunModal');
        if (createModal) {
            const closeBtn = createModal.querySelector('.modal-close');
            const cancelBtn = createModal.querySelector('.cancel-btn');
            const form = document.getElementById('createTestRunForm');
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideModal('createTestRunModal'));
            }
            
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => this.hideModal('createTestRunModal'));
            }
            
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleCreateTestRun(form);
                });
            }
        }
        
        // Модальное окно деталей прогона
        const detailsModal = document.getElementById('testRunDetailsModal');
        if (detailsModal) {
            const closeBtn = detailsModal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideModal('testRunDetailsModal'));
            }
        }
    }
    
    // Переключение вкладок
    switchTab(tab) {
        this.currentTab = tab;
        
        // Обновление активной кнопки
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            if (btn.dataset.tab === tab) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Показ активного контента
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            if (content.id === `${tab}Tab`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    }
    
    // Фильтрация прогонов тестов
    filterTestRuns() {
        const search = document.getElementById('testSearch')?.value.toLowerCase() || '';
        const status = document.getElementById('testStatusFilter')?.value || '';
        
        const filtered = this.testRuns.filter(run => {
            const matchesSearch = run.name.toLowerCase().includes(search) ||
                                 run.project.toLowerCase().includes(search) ||
                                 run.scenario.toLowerCase().includes(search);
            
            const matchesStatus = !status || run.status === status;
            
            return matchesSearch && matchesStatus;
        });
        
        // В реальном приложении здесь будет перерисовка отфильтрованных данных
        console.log('Отфильтрованные прогоны:', filtered);
    }
    
    // Обновление статистики
    updateStats() {
        const totalRuns = this.testRuns.length;
        const passedRuns = this.testRuns.filter(r => r.status === 'passed').length;
        const failedRuns = this.testRuns.filter(r => r.status === 'failed').length;
        const runningRuns = this.testRuns.filter(r => r.status === 'running').length;
        
        document.getElementById('totalTestRuns').textContent = totalRuns;
        document.getElementById('passedTests').textContent = passedRuns;
        document.getElementById('failedTests').textContent = failedRuns;
        document.getElementById('runningTests').textContent = runningRuns;
    }
    
    // Настройка графика
    setupChart() {
        const canvas = document.getElementById('testResultsChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Данные для графика
        const data = {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
            datasets: [
                {
                    label: 'Успешные тесты',
                    data: [65, 59, 80, 81, 56, 55],
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Проваленные тесты',
                    data: [28, 48, 40, 19, 86, 27],
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                }
            ]
        };
        
        const options = {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Результаты тестирования по месяцам'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Количество тестов'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                }
            }
        };
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: options
        });
        
        // Обновляем сводку
        this.updateReportSummary();
    }
    
    // Обновление сводки отчета
    updateReportSummary() {
        const totalTests = 156;
        const passedTests = 124;
        const failedTests = 32;
        
        document.getElementById('coverageRate').textContent = `${Math.round((passedTests / totalTests) * 100)}%`;
        document.getElementById('avgTestTime').textContent = '45 сек';
        document.getElementById('criticalBugs').textContent = '3';
        document.getElementById('stabilityScore').textContent = '89%';
    }
    
    // Просмотр деталей прогона теста
    async viewTestRunDetails(id) {
        try {
            const run = this.testRuns.find(r => r.id == id);
            if (!run) return;
            
            const modal = document.getElementById('testRunDetailsModal');
            const content = document.getElementById('testRunDetailsContent');
            
            if (!modal || !content) return;
            
            content.innerHTML = `
                <div class="test-run-details">
                    <div class="details-header">
                        <h3>${run.name}</h3>
                        <span class="status-indicator status-${run.status}">
                            ${this.getStatusText(run.status)}
                        </span>
                    </div>
                    
                    <div class="details-body">
                        <div class="details-section">
                            <h4><i class="fas fa-info-circle"></i> Общая информация</h4>
                            <div class="details-grid">
                                <div class="detail-item">
                                    <strong>Проект:</strong> ${run.project}
                                </div>
                                <div class="detail-item">
                                    <strong>Сценарий:</strong> ${run.scenario}
                                </div>
                                <div class="detail-item">
                                    <strong>Длительность:</strong> ${run.duration}
                                </div>
                                <div class="detail-item">
                                    <strong>Начало:</strong> ${VRARPlatform.formatDate(run.started_at)}
                                </div>
                            </div>
                        </div>
                        
                        <div class="details-section">
                            <h4><i class="fas fa-chart-bar"></i> Результаты тестов</h4>
                            <div class="results-summary">
                                <div class="result-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <div class="result-info">
                                        <h5>${run.passed_tests}</h5>
                                        <p>Успешных тестов</p>
                                    </div>
                                </div>
                                <div class="result-item failure">
                                    <i class="fas fa-times-circle"></i>
                                    <div class="result-info">
                                        <h5>${run.failed_tests}</h5>
                                        <p>Проваленных тестов</p>
                                    </div>
                                </div>
                                <div class="result-item total">
                                    <i class="fas fa-vial"></i>
                                    <div class="result-info">
                                        <h5>${run.total_tests}</h5>
                                        <p>Всего тестов</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="progress-container">
                                <div class="progress-bar">
                                    <div class="progress-fill success" style="width: ${(run.passed_tests / run.total_tests) * 100}%"></div>
                                    <div class="progress-fill failure" style="width: ${(run.failed_tests / run.total_tests) * 100}%"></div>
                                </div>
                                <div class="progress-label">
                                    <span>${Math.round((run.passed_tests / run.total_tests) * 100)}% успеха</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="details-section">
                            <h4><i class="fas fa-list"></i> Детали тестов</h4>
                            <div class="test-details-list">
                                ${this.generateTestDetails(run)}
                            </div>
                        </div>
                        
                        ${run.status === 'failed' ? `
                            <div class="details-section">
                                <h4><i class="fas fa-exclamation-triangle"></i> Проблемы</h4>
                                <div class="problems-list">
                                    <div class="problem-item">
                                        <i class="fas fa-bug"></i>
                                        <div class="problem-info">
                                            <h5>Ошибка загрузки текстур</h5>
                                            <p>Файл texture_high_res.png не найден</p>
                                            <small>Время: 00:01:23</small>
                                        </div>
                                    </div>
                                    <div class="problem-item">
                                        <i class="fas fa-bug"></i>
                                        <div class="problem-info">
                                            <h5>Утечка памяти</h5>
                                            <p>Потребление памяти растет при длительной работе</p>
                                            <small>Время: 00:02:15</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="details-footer">
                        <button class="btn btn-primary" id="exportReportBtn">
                            <i class="fas fa-download"></i> Экспорт отчета
                        </button>
                        <button class="btn btn-outline" onclick="testingManager.hideModal('testRunDetailsModal')">
                            Закрыть
                        </button>
                    </div>
                </div>
            `;
            
            // Обработчик кнопки экспорта
            const exportBtn = document.getElementById('exportReportBtn');
            if (exportBtn) {
                exportBtn.addEventListener('click', () => this.exportTestReport(run.id));
            }
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        } catch (error) {
            console.error('Ошибка загрузки деталей:', error);
            VRARPlatform.showNotification('Не удалось загрузить детали прогона', 'error');
        }
    }
    
    // Генерация деталей тестов
    generateTestDetails(run) {
        const tests = [
            { name: 'Загрузка сцены', status: 'passed', duration: '2.3 сек' },
            { name: 'Инициализация VR', status: 'passed', duration: '1.8 сек' },
            { name: 'Загрузка текстур', status: run.status === 'failed' ? 'failed' : 'passed', duration: '4.5 сек' },
            { name: 'Анимации персонажей', status: 'passed', duration: '3.2 сек' },
            { name: 'Физика объектов', status: 'passed', duration: '2.1 сек' },
            { name: 'Интерфейс пользователя', status: 'passed', duration: '1.5 сек' }
        ];
        
        return tests.map(test => `
            <div class="test-detail-item ${test.status}">
                <div class="test-detail-info">
                    <i class="fas fa-${test.status === 'passed' ? 'check-circle' : 'times-circle'}"></i>
                    <div>
                        <h5>${test.name}</h5>
                        <small>Длительность: ${test.duration}</small>
                    </div>
                </div>
                <span class="test-status ${test.status}">
                    ${test.status === 'passed' ? 'Успешно' : 'Провалено'}
                </span>
            </div>
        `).join('');
    }
    
    // Запуск тестового прогона
    async startTestRun(id) {
        try {
            VRARPlatform.showNotification('Запуск тестового прогона...', 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Обновляем статус прогона
            const run = this.testRuns.find(r => r.id == id);
            if (run) {
                run.status = 'running';
                this.renderTestRuns();
                this.updateStats();
                
                VRARPlatform.showNotification('Тестовый прогон запущен', 'success');
            }
        } catch (error) {
            console.error('Ошибка запуска прогона:', error);
            VRARPlatform.showNotification('Не удалось запустить тестовый прогон', 'error');
        }
    }
    
    // Остановка тестового прогона
    async stopTestRun(id) {
        try {
            if (!confirm('Остановить тестовый прогон?')) return;
            
            VRARPlatform.showNotification('Остановка тестового прогона...', 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Обновляем статус прогона
            const run = this.testRuns.find(r => r.id == id);
            if (run) {
                run.status = 'stopped';
                this.renderTestRuns();
                this.updateStats();
                
                VRARPlatform.showNotification('Тестовый прогон остановлен', 'success');
            }
        } catch (error) {
            console.error('Ошибка остановки прогона:', error);
            VRARPlatform.showNotification('Не удалось остановить тестовый прогон', 'error');
        }
    }
    
    // Подключение к устройству
    async connectToDevice(id) {
        try {
            const device = this.devices.find(d => d.id == id);
            if (!device) return;
            
            VRARPlatform.showNotification(`Подключение к ${device.name}...`, 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            VRARPlatform.showNotification(`Успешно подключено к ${device.name}`, 'success');
        } catch (error) {
            console.error('Ошибка подключения:', error);
            VRARPlatform.showNotification('Не удалось подключиться к устройству', 'error');
        }
    }
    
    // Редактирование устройства
    editDevice(id) {
        const device = this.devices.find(d => d.id == id);
        if (device) {
            VRARPlatform.showNotification(`Редактирование устройства ${device.name}`, 'info');
        }
    }
    
    // Просмотр деталей бага
    viewBugDetails(id) {
        const bug = this.bugReports.find(b => b.id == id);
        if (bug) {
            VRARPlatform.showNotification(`Просмотр бага: ${bug.title}`, 'info');
        }
    }
    
    // Назначение бага
    assignBug(id) {
        const bug = this.bugReports.find(b => b.id == id);
        if (bug) {
            VRARPlatform.showNotification(`Назначение бага: ${bug.title}`, 'info');
        }
    }
    
    // Закрытие бага
    closeBug(id) {
        const bug = this.bugReports.find(b => b.id == id);
        if (bug) {
            VRARPlatform.showNotification(`Закрытие бага: ${bug.title}`, 'info');
        }
    }
    
    // Сообщение об ошибке
    reportBug(testRunId) {
        const run = this.testRuns.find(r => r.id == testRunId);
        if (run) {
            VRARPlatform.showNotification(`Сообщение об ошибке для прогона: ${run.name}`, 'info');
            this.showBugReportModal(run);
        }
    }
    
    // Экспорт отчета
    async exportTestReport(id) {
        try {
            VRARPlatform.showNotification('Экспорт отчета...', 'info');
            
            // В реальном приложении здесь будет генерация и скачивание отчета
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            VRARPlatform.showNotification('Отчет экспортирован успешно', 'success');
        } catch (error) {
            console.error('Ошибка экспорта:', error);
            VRARPlatform.showNotification('Не удалось экспортировать отчет', 'error');
        }
    }
    
    // Генерация отчета
    async generateReport() {
        try {
            const period = document.getElementById('reportPeriod')?.value || 'week';
            VRARPlatform.showNotification(`Генерация отчета за ${period}...`, 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            VRARPlatform.showNotification('Отчет сгенерирован успешно', 'success');
            
            // Предлагаем скачать
            this.downloadReport();
        } catch (error) {
            console.error('Ошибка генерации отчета:', error);
            VRARPlatform.showNotification('Не удалось сгенерировать отчет', 'error');
        }
    }
    
    // Скачивание отчета
    downloadReport() {
        const reportData = {
            title: 'Отчет по тестированию',
            period: document.getElementById('reportPeriod')?.value || 'week',
            generated_at: new Date().toISOString(),
            summary: {
                total_runs: this.testRuns.length,
                passed_runs: this.testRuns.filter(r => r.status === 'passed').length,
                failed_runs: this.testRuns.filter(r => r.status === 'failed').length,
                coverage_rate: '78%',
                avg_test_time: '45 сек',
                critical_bugs: 3,
                stability_score: '89%'
            },
            test_runs: this.testRuns,
            devices: this.devices,
            bug_reports: this.bugReports
        };
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        const fileName = `test_report_${new Date().toISOString().split('T')[0]}.json`;
        
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        VRARPlatform.showNotification(`Отчет сохранен как ${fileName}`, 'success');
    }
    
    // Показ модального окна создания прогона
    showCreateTestRunModal(run = null) {
        const modal = document.getElementById('createTestRunModal');
        if (!modal) return;
        
        const form = document.getElementById('createTestRunForm');
        if (form) {
            if (run) {
                // Редактирование существующего прогона
                document.getElementById('testRunName').value = run.name;
                // Заполняем остальные поля...
            } else {
                // Создание нового прогона
                form.reset();
            }
        }
        
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    // Показ модального окна добавления устройства
    showAddDeviceModal() {
        VRARPlatform.showNotification('Добавление устройства в разработке', 'info');
    }
    
    // Показ модального окна багрепорта
    showBugReportModal(run = null) {
        VRARPlatform.showNotification('Сообщение об ошибке в разработке', 'info');
    }
    
    // Скрытие модального окна
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Обработка создания тестового прогона
    async handleCreateTestRun(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Создание...';
            
            const formData = new FormData(form);
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                if (value.trim()) {
                    data[key] = value.trim();
                }
            }
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Добавляем новый прогон в список
            const newRun = {
                id: Date.now(),
                name: data.name || 'Новый прогон',
                project: 'Новый проект',
                scenario: 'Новый сценарий',
                status: 'pending',
                duration: '0 сек',
                started_at: new Date().toISOString(),
                passed_tests: 0,
                failed_tests: 0,
                total_tests: 0
            };
            
            this.testRuns.unshift(newRun);
            this.renderTestRuns();
            this.updateStats();
            
            VRARPlatform.showNotification('Тестовый прогон создан успешно', 'success');
            this.hideModal('createTestRunModal');
        } catch (error) {
            console.error('Ошибка создания прогона:', error);
            VRARPlatform.showNotification('Не удалось создать тестовый прогон', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

// Создание экземпляра менеджера тестирования
let testingManager;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    testingManager = new TestingManager();
});

// Глобальный экспорт
window.testingManager = testingManager;