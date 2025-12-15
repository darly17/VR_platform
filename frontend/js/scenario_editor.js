/**
 * JavaScript для редактора сценариев
 */

class ScenarioEditor {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.dragging = false;
        this.offsetX = 0;
        this.offsetY = 0;
        this.scale = 1;
        this.panX = 0;
        this.panY = 0;
        this.isPanning = false;
        this.startPanX = 0;
        this.startPanY = 0;
        this.currentScenario = null;
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.setupTools();
        this.loadScenarios();
        this.setupModal();
        
        // Запуск цикла отрисовки
        this.animate();
    }
    
    // Настройка canvas
    setupCanvas() {
        this.canvas = document.getElementById('workspaceCanvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        // Обработчик изменения размера окна
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    // Изменение размера canvas
    resizeCanvas() {
        if (!this.canvas) return;
        
        const container = this.canvas.parentElement;
        if (!container) return;
        
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        
        this.draw();
    }
    
    // Настройка обработчиков событий
    setupEventListeners() {
        if (!this.canvas) return;
        
        // События мыши
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e));
        
        // События для мобильных устройств
        this.canvas.addEventListener('touchstart', (e) => this.onTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.onTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.onTouchEnd(e));
        
        // События клавиатуры
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
        
        // Обработчики кнопок инструментов
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        const centerViewBtn = document.getElementById('centerViewBtn');
        const clearWorkspaceBtn = document.getElementById('clearWorkspaceBtn');
        const saveBtn = document.getElementById('saveScenarioBtn');
        const runBtn = document.getElementById('runScenarioBtn');
        const validateBtn = document.getElementById('validateScenarioBtn');
        
        if (zoomInBtn) zoomInBtn.addEventListener('click', () => this.zoomIn());
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => this.zoomOut());
        if (centerViewBtn) centerViewBtn.addEventListener('click', () => this.centerView());
        if (clearWorkspaceBtn) clearWorkspaceBtn.addEventListener('click', () => this.clearWorkspace());
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveScenario());
        if (runBtn) runBtn.addEventListener('click', () => this.runScenario());
        if (validateBtn) validateBtn.addEventListener('click', () => this.validateScenario());
    }
    
    // Настройка инструментов
    setupTools() {
        const toolItems = document.querySelectorAll('.tool-item');
        toolItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.dataset.type);
            });
        });
        
        // Drop на canvas
        if (this.canvas) {
            this.canvas.addEventListener('dragover', (e) => {
                e.preventDefault();
            });
            
            this.canvas.addEventListener('drop', (e) => {
                e.preventDefault();
                const type = e.dataTransfer.getData('text/plain');
                if (type) {
                    const rect = this.canvas.getBoundingClientRect();
                    const x = (e.clientX - rect.left - this.panX) / this.scale;
                    const y = (e.clientY - rect.top - this.panY) / this.scale;
                    this.addNode(type, x, y);
                }
            });
        }
    }
    
    // Загрузка сценариев
    async loadScenarios() {
        try {
            const container = document.getElementById('scenariosList');
            if (!container) return;
            
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            const demoScenarios = [
                { id: 1, name: 'VR Обучение', description: 'Сценарий обучения в VR' },
                { id: 2, name: 'AR Навигация', description: 'Навигация в дополненной реальности' },
                { id: 3, name: 'Виртуальная экскурсия', description: 'Экскурсия по музею' },
                { id: 4, name: 'Игровой сценарий', description: 'Игровая механика в VR' }
            ];
            
            container.innerHTML = demoScenarios.map(scenario => `
                <div class="scenario-item" data-id="${scenario.id}">
                    <div class="scenario-info">
                        <h4>${scenario.name}</h4>
                        <p>${scenario.description}</p>
                    </div>
                    <div class="scenario-actions">
                        <button class="btn btn-icon load-scenario-btn" title="Загрузить">
                            <i class="fas fa-folder-open"></i>
                        </button>
                        <button class="btn btn-icon edit-scenario-btn" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
            `).join('');
            
            // Обработчики для кнопок сценариев
            container.querySelectorAll('.load-scenario-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const scenarioId = btn.closest('.scenario-item').dataset.id;
                    this.loadScenario(scenarioId);
                });
            });
            
            container.querySelectorAll('.edit-scenario-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const scenarioId = btn.closest('.scenario-item').dataset.id;
                    this.editScenario(scenarioId);
                });
            });
        } catch (error) {
            console.error('Ошибка загрузки сценариев:', error);
        }
    }
    
    // Настройка модальных окон
    setupModal() {
        const createModal = document.getElementById('createScenarioModal');
        if (!createModal) return;
        
        const closeBtn = createModal.querySelector('.modal-close');
        const cancelBtn = createModal.querySelector('.cancel-btn');
        const form = document.getElementById('createScenarioForm');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal('createScenarioModal'));
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal('createScenarioModal'));
        }
        
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreateScenario(form);
            });
        }
    }
    
    // События мыши
    onMouseDown(e) {
        if (!this.canvas) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - this.panX) / this.scale;
        const y = (e.clientY - rect.top - this.panY) / this.scale;
        
        // Проверяем, попал ли клик в узел
        this.selectedNode = this.getNodeAt(x, y);
        
        if (this.selectedNode) {
            this.dragging = true;
            this.offsetX = x - this.selectedNode.x;
            this.offsetY = y - this.selectedNode.y;
        } else if (e.button === 1 || e.ctrlKey) {
            // Средняя кнопка мыши или Ctrl + левая кнопка для панорамирования
            this.isPanning = true;
            this.startPanX = e.clientX;
            this.startPanY = e.clientY;
        }
        
        this.draw();
    }
    
    onMouseMove(e) {
        if (!this.canvas) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - this.panX) / this.scale;
        const y = (e.clientY - rect.top - this.panY) / this.scale;
        
        if (this.dragging && this.selectedNode) {
            this.selectedNode.x = x - this.offsetX;
            this.selectedNode.y = y - this.offsetY;
            this.draw();
        } else if (this.isPanning) {
            const dx = e.clientX - this.startPanX;
            const dy = e.clientY - this.startPanY;
            this.panX += dx;
            this.panY += dy;
            this.startPanX = e.clientX;
            this.startPanY = e.clientY;
            this.draw();
        }
    }
    
    onMouseUp(e) {
        this.dragging = false;
        this.isPanning = false;
        this.selectedNode = null;
    }
    
    onWheel(e) {
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const zoomFactor = 0.1;
        const oldScale = this.scale;
        
        if (e.deltaY < 0) {
            // Увеличение
            this.scale *= 1 + zoomFactor;
        } else {
            // Уменьшение
            this.scale /= 1 + zoomFactor;
        }
        
        // Ограничиваем масштаб
        this.scale = Math.max(0.1, Math.min(5, this.scale));
        
        // Корректируем панорамирование для сохранения позиции мыши
        const scaleChange = this.scale / oldScale;
        this.panX = mouseX - (mouseX - this.panX) * scaleChange;
        this.panY = mouseY - (mouseY - this.panY) * scaleChange;
        
        this.draw();
    }
    
    // События для сенсорных устройств
    onTouchStart(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.onMouseDown(mouseEvent);
        } else if (e.touches.length === 2) {
            e.preventDefault();
        }
    }
    
    onTouchMove(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.onMouseMove(mouseEvent);
        } else if (e.touches.length === 2) {
            e.preventDefault();
            // Масштабирование двумя пальцами
            this.handlePinchZoom(e);
        }
    }
    
    onTouchEnd(e) {
        const mouseEvent = new MouseEvent('mouseup');
        this.onMouseUp(mouseEvent);
    }
    
    handlePinchZoom(e) {
        if (e.touches.length !== 2) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        const currentDistance = Math.hypot(
            touch1.clientX - touch2.clientX,
            touch1.clientY - touch2.clientY
        );
        
        if (this.lastPinchDistance) {
            const delta = currentDistance - this.lastPinchDistance;
            const zoomFactor = delta * 0.01;
            
            this.scale *= 1 + zoomFactor;
            this.scale = Math.max(0.1, Math.min(5, this.scale));
            
            this.draw();
        }
        
        this.lastPinchDistance = currentDistance;
    }
    
    // События клавиатуры
    onKeyDown(e) {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.selectedNode) {
                this.removeNode(this.selectedNode);
                this.selectedNode = null;
                this.draw();
            }
        } else if (e.key === 'Escape') {
            this.selectedNode = null;
            this.draw();
        } else if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            this.saveScenario();
        } else if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            // Отмена последнего действия
        }
    }
    
    // Добавление узла
    addNode(type, x, y) {
        const node = {
            id: Date.now(),
            type: type,
            x: x,
            y: y,
            width: 120,
            height: 80,
            title: this.getNodeTitle(type),
            color: this.getNodeColor(type),
            properties: this.getDefaultProperties(type)
        };
        
        this.nodes.push(node);
        this.updateStats();
        this.draw();
        this.showNodeProperties(node);
    }
    
    // Получение заголовка узла
    getNodeTitle(type) {
        const titles = {
            'state': 'Состояние',
            'action': 'Действие',
            'condition': 'Условие',
            'event': 'Событие',
            'start': 'Старт',
            'end': 'Конец'
        };
        return titles[type] || 'Узел';
    }
    
    // Получение цвета узла
    getNodeColor(type) {
        const colors = {
            'state': '#3498db',
            'action': '#2ecc71',
            'condition': '#f39c12',
            'event': '#9b59b6',
            'start': '#27ae60',
            'end': '#e74c3c'
        };
        return colors[type] || '#95a5a6';
    }
    
    // Получение свойств по умолчанию
    getDefaultProperties(type) {
        const baseProps = {
            id: Date.now(),
            name: this.getNodeTitle(type),
            description: '',
            enabled: true
        };
        
        switch (type) {
            case 'state':
                return {
                    ...baseProps,
                    transitions: [],
                    onEnter: '',
                    onExit: '',
                    onUpdate: '',
                    isInitial: type === 'start'
                };
            case 'action':
                return {
                    ...baseProps,
                    actionType: 'custom',
                    parameters: {},
                    delay: 0,
                    repeat: 1
                };
            case 'condition':
                return {
                    ...baseProps,
                    conditionType: 'boolean',
                    expression: '',
                    trueState: '',
                    falseState: ''
                };
            case 'event':
                return {
                    ...baseProps,
                    eventType: 'custom',
                    trigger: '',
                    targetState: '',
                    data: {}
                };
            default:
                return baseProps;
        }
    }
    
    // Получение узла по координатам
    getNodeAt(x, y) {
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const node = this.nodes[i];
            if (x >= node.x && x <= node.x + node.width &&
                y >= node.y && y <= node.y + node.height) {
                return node;
            }
        }
        return null;
    }
    
    // Удаление узла
    removeNode(node) {
        const index = this.nodes.indexOf(node);
        if (index !== -1) {
            this.nodes.splice(index, 1);
            
            // Удаляем соединения, связанные с этим узлом
            this.connections = this.connections.filter(conn => 
                conn.from !== node.id && conn.to !== node.id
            );
            
            this.updateStats();
        }
    }
    
    // Отображение свойств узла
    showNodeProperties(node) {
        const panel = document.getElementById('propertiesPanel');
        if (!panel) return;
        
        panel.innerHTML = `
            <h4>${node.title} (${node.type})</h4>
            <form class="node-properties-form">
                <div class="form-group">
                    <label for="nodeName">Название</label>
                    <input type="text" id="nodeName" value="${node.properties.name}" 
                           class="form-control" data-property="name">
                </div>
                <div class="form-group">
                    <label for="nodeDescription">Описание</label>
                    <textarea id="nodeDescription" rows="2" 
                              class="form-control" data-property="description">${node.properties.description}</textarea>
                </div>
                ${this.getTypeSpecificProperties(node)}
                <div class="form-group">
                    <button type="button" class="btn btn-primary save-properties-btn" data-node-id="${node.id}">
                        Сохранить
                    </button>
                    <button type="button" class="btn btn-outline delete-node-btn" data-node-id="${node.id}">
                        Удалить
                    </button>
                </div>
            </form>
        `;
        
        // Обработчики для формы
        const form = panel.querySelector('.node-properties-form');
        const saveBtn = panel.querySelector('.save-properties-btn');
        const deleteBtn = panel.querySelector('.delete-node-btn');
        
        if (form) {
            form.addEventListener('input', (e) => {
                if (e.target.dataset.property) {
                    node.properties[e.target.dataset.property] = e.target.value;
                }
            });
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveNodeProperties(node);
            });
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.removeNode(node);
                panel.innerHTML = '<p class="placeholder-text">Выберите узел для редактирования свойств</p>';
                this.draw();
            });
        }
    }
    
    // Получение специфичных свойств для типа узла
    getTypeSpecificProperties(node) {
        switch (node.type) {
            case 'state':
                return `
                    <div class="form-group">
                        <label for="stateOnEnter">При входе</label>
                        <textarea id="stateOnEnter" rows="2" 
                                  class="form-control" data-property="onEnter">${node.properties.onEnter}</textarea>
                    </div>
                    <div class="form-group">
                        <label for="stateOnExit">При выходе</label>
                        <textarea id="stateOnExit" rows="2" 
                                  class="form-control" data-property="onExit">${node.properties.onExit}</textarea>
                    </div>
                `;
            case 'action':
                return `
                    <div class="form-group">
                        <label for="actionType">Тип действия</label>
                        <select id="actionType" class="form-control" data-property="actionType">
                            <option value="custom" ${node.properties.actionType === 'custom' ? 'selected' : ''}>Пользовательское</option>
                            <option value="animation" ${node.properties.actionType === 'animation' ? 'selected' : ''}>Анимация</option>
                            <option value="sound" ${node.properties.actionType === 'sound' ? 'selected' : ''}>Звук</option>
                            <option value="move" ${node.properties.actionType === 'move' ? 'selected' : ''}>Перемещение</option>
                            <option value="wait" ${node.properties.actionType === 'wait' ? 'selected' : ''}>Ожидание</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="actionDelay">Задержка (сек)</label>
                        <input type="number" id="actionDelay" value="${node.properties.delay}" 
                               class="form-control" data-property="delay" step="0.1" min="0">
                    </div>
                `;
            case 'condition':
                return `
                    <div class="form-group">
                        <label for="conditionExpression">Выражение</label>
                        <input type="text" id="conditionExpression" value="${node.properties.expression}" 
                               class="form-control" data-property="expression" placeholder="например: health > 0">
                    </div>
                `;
            default:
                return '';
        }
    }
    
    // Сохранение свойств узла
    saveNodeProperties(node) {
        node.title = node.properties.name;
        this.draw();
        VRARPlatform.showNotification('Свойства сохранены', 'success');
    }
    
    // Обновление статистики
    updateStats() {
        document.getElementById('nodeCount').textContent = this.nodes.length;
        document.getElementById('connectionCount').textContent = this.connections.length;
    }
    
    // Отрисовка
    draw() {
        if (!this.canvas || !this.ctx) return;
        
        // Очищаем canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Сохраняем состояние контекста
        this.ctx.save();
        
        // Применяем трансформации (масштабирование и панорамирование)
        this.ctx.translate(this.panX, this.panY);
        this.ctx.scale(this.scale, this.scale);
        
        // Рисуем сетку
        this.drawGrid();
        
        // Рисуем соединения
        this.drawConnections();
        
        // Рисуем узлы
        this.drawNodes();
        
        // Восстанавливаем состояние контекста
        this.ctx.restore();
    }
    
    // Отрисовка сетки
    drawGrid() {
        const gridSize = 20;
        const width = this.canvas.width / this.scale;
        const height = this.canvas.height / this.scale;
        
        this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.lineWidth = 1;
        
        // Вертикальные линии
        for (let x = -this.panX % gridSize; x < width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }
        
        // Горизонтальные линии
        for (let y = -this.panY % gridSize; y < height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
    }
    
    // Отрисовка узлов
    drawNodes() {
        this.nodes.forEach(node => {
            // Рисуем прямоугольник узла
            this.ctx.fillStyle = node.color;
            this.ctx.strokeStyle = node === this.selectedNode ? '#2c3e50' : '#34495e';
            this.ctx.lineWidth = node === this.selectedNode ? 3 : 2;
            
            // Скругленные углы
            const radius = 8;
            this.ctx.beginPath();
            this.ctx.moveTo(node.x + radius, node.y);
            this.ctx.lineTo(node.x + node.width - radius, node.y);
            this.ctx.quadraticCurveTo(node.x + node.width, node.y, node.x + node.width, node.y + radius);
            this.ctx.lineTo(node.x + node.width, node.y + node.height - radius);
            this.ctx.quadraticCurveTo(node.x + node.width, node.y + node.height, node.x + node.width - radius, node.y + node.height);
            this.ctx.lineTo(node.x + radius, node.y + node.height);
            this.ctx.quadraticCurveTo(node.x, node.y + node.height, node.x, node.y + node.height - radius);
            this.ctx.lineTo(node.x, node.y + radius);
            this.ctx.quadraticCurveTo(node.x, node.y, node.x + radius, node.y);
            this.ctx.closePath();
            
            this.ctx.fill();
            this.ctx.stroke();
            
            // Тень для выбранного узла
            if (node === this.selectedNode) {
                this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                this.ctx.shadowBlur = 10;
                this.ctx.shadowOffsetX = 0;
                this.ctx.shadowOffsetY = 0;
                this.ctx.stroke();
                this.ctx.shadowColor = 'transparent';
                this.ctx.shadowBlur = 0;
            }
            
            // Рисуем иконку
            const icon = this.getNodeIcon(node.type);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '20px FontAwesome';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(icon, node.x + node.width / 2, node.y + 25);
            
            // Рисуем текст
            this.ctx.fillStyle = '#2c3e50';
            this.ctx.font = 'bold 12px Arial';
            this.ctx.fillText(node.title, node.x + node.width / 2, node.y + 55);
            
            // Рисуем порты соединений
            this.drawNodePorts(node);
        });
    }
    
    // Отрисовка портов узла
    drawNodePorts(node) {
        const portSize = 6;
        
        // Входные порты (слева)
        this.ctx.fillStyle = '#3498db';
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y + node.height / 2, portSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Выходные порты (справа)
        this.ctx.fillStyle = '#e74c3c';
        this.ctx.beginPath();
        this.ctx.arc(node.x + node.width, node.y + node.height / 2, portSize, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    // Отрисовка соединений
    drawConnections() {
        this.connections.forEach(conn => {
            const fromNode = this.nodes.find(n => n.id === conn.from);
            const toNode = this.nodes.find(n => n.id === conn.to);
            
            if (!fromNode || !toNode) return;
            
            const startX = fromNode.x + fromNode.width;
            const startY = fromNode.y + fromNode.height / 2;
            const endX = toNode.x;
            const endY = toNode.y + toNode.height / 2;
            
            // Рисуем линию соединения
            this.ctx.strokeStyle = conn.color || '#95a5a6';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash(conn.dashed ? [5, 5] : []);
            
            // Кривая Безье для более красивого соединения
            const cp1x = startX + 50;
            const cp1y = startY;
            const cp2x = endX - 50;
            const cp2y = endY;
            
            this.ctx.beginPath();
            this.ctx.moveTo(startX, startY);
            this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            this.ctx.stroke();
            
            // Рисуем стрелку
            this.drawArrow(endX, endY, Math.atan2(endY - cp2y, endX - cp2x));
            
            this.ctx.setLineDash([]);
        });
    }
    
    // Отрисовка стрелки
    drawArrow(x, y, angle) {
        const length = 10;
        
        this.ctx.save();
        this.ctx.translate(x, y);
        this.ctx.rotate(angle);
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(-length, -length / 2);
        this.ctx.lineTo(-length, length / 2);
        this.ctx.closePath();
        
        this.ctx.fillStyle = '#95a5a6';
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    // Получение иконки для типа узла
    getNodeIcon(type) {
        const icons = {
            'state': '○',
            'action': '⚡',
            'condition': '?',
            'event': '🔔',
            'start': '▶',
            'end': '■'
        };
        return icons[type] || '●';
    }
    
    // Анимация (цикл отрисовки)
    animate() {
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
    
    // Управление масштабом
    zoomIn() {
        this.scale *= 1.1;
        this.scale = Math.min(5, this.scale);
        this.draw();
    }
    
    zoomOut() {
        this.scale /= 1.1;
        this.scale = Math.max(0.1, this.scale);
        this.draw();
    }
    
    centerView() {
        if (this.nodes.length === 0) {
            this.panX = this.canvas.width / 2;
            this.panY = this.canvas.height / 2;
        } else {
            // Находим bounding box всех узлов
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            
            this.nodes.forEach(node => {
                minX = Math.min(minX, node.x);
                minY = Math.min(minY, node.y);
                maxX = Math.max(maxX, node.x + node.width);
                maxY = Math.max(maxY, node.y + node.height);
            });
            
            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;
            
            this.panX = this.canvas.width / 2 - centerX * this.scale;
            this.panY = this.canvas.height / 2 - centerY * this.scale;
        }
        
        this.draw();
    }
    
    // Очистка рабочей области
    clearWorkspace() {
        if (!confirm('Очистить рабочую область? Все несохраненные изменения будут потеряны.')) {
            return;
        }
        
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.updateStats();
        
        const panel = document.getElementById('propertiesPanel');
        if (panel) {
            panel.innerHTML = '<p class="placeholder-text">Выберите узел для редактирования свойств</p>';
        }
        
        VRARPlatform.showNotification('Рабочая область очищена', 'success');
    }
    
    // Загрузка сценария
    async loadScenario(id) {
        try {
            // В реальном приложении здесь будет запрос к API
            VRARPlatform.showNotification('Загрузка сценария...', 'info');
            
            // Демо-данные
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.nodes = [
                {
                    id: 1,
                    type: 'start',
                    x: 100,
                    y: 100,
                    width: 120,
                    height: 80,
                    title: 'Начало',
                    color: '#27ae60',
                    properties: { name: 'Начало', description: 'Начальная точка сценария' }
                },
                {
                    id: 2,
                    type: 'state',
                    x: 300,
                    y: 100,
                    width: 120,
                    height: 80,
                    title: 'Загрузка',
                    color: '#3498db',
                    properties: { name: 'Загрузка', description: 'Загрузка ресурсов' }
                },
                {
                    id: 3,
                    type: 'action',
                    x: 500,
                    y: 100,
                    width: 120,
                    height: 80,
                    title: 'Показать UI',
                    color: '#2ecc71',
                    properties: { name: 'Показать UI', description: 'Отображение интерфейса' }
                },
                {
                    id: 4,
                    type: 'condition',
                    x: 300,
                    y: 250,
                    width: 120,
                    height: 80,
                    title: 'Проверка',
                    color: '#f39c12',
                    properties: { name: 'Проверка', description: 'Проверка условий' }
                },
                {
                    id: 5,
                    type: 'end',
                    x: 500,
                    y: 250,
                    width: 120,
                    height: 80,
                    title: 'Конец',
                    color: '#e74c3c',
                    properties: { name: 'Конец', description: 'Конечная точка сценария' }
                }
            ];
            
            this.connections = [
                { from: 1, to: 2, color: '#3498db' },
                { from: 2, to: 3, color: '#2ecc71' },
                { from: 3, to: 4, color: '#f39c12' },
                { from: 4, to: 5, color: '#e74c3c' }
            ];
            
            this.currentScenario = { id: id, name: 'Демо сценарий' };
            document.getElementById('scenarioTitle').textContent = 'Демо сценарий';
            
            this.updateStats();
            this.centerView();
            
            VRARPlatform.showNotification('Сценарий загружен', 'success');
        } catch (error) {
            console.error('Ошибка загрузки сценария:', error);
            VRARPlatform.showNotification('Не удалось загрузить сценарий', 'error');
        }
    }
    
    // Редактирование сценария
    editScenario(id) {
        // В реальном приложении здесь будет редактирование метаданных сценария
        VRARPlatform.showNotification('Редактирование сценария в разработке', 'info');
    }
    
    // Сохранение сценария
    async saveScenario() {
        if (this.nodes.length === 0) {
            VRARPlatform.showNotification('Нет данных для сохранения', 'warning');
            return;
        }
        
        try {
            const scenarioData = {
                nodes: this.nodes,
                connections: this.connections,
                viewport: {
                    scale: this.scale,
                    panX: this.panX,
                    panY: this.panY
                }
            };
            
            // В реальном приложении здесь будет запрос к API
            VRARPlatform.showNotification('Сохранение сценария...', 'info');
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            VRARPlatform.showNotification('Сценарий сохранен успешно', 'success');
        } catch (error) {
            console.error('Ошибка сохранения сценария:', error);
            VRARPlatform.showNotification('Не удалось сохранить сценарий', 'error');
        }
    }
    
    // Запуск сценария
    async runScenario() {
        if (this.nodes.length === 0) {
            VRARPlatform.showNotification('Нет сценария для запуска', 'warning');
            return;
        }
        
        try {
            VRARPlatform.showNotification('Запуск сценария...', 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            VRARPlatform.showNotification('Сценарий выполнен успешно', 'success');
        } catch (error) {
            console.error('Ошибка выполнения сценария:', error);
            VRARPlatform.showNotification('Ошибка при выполнении сценария', 'error');
        }
    }
    
    // Валидация сценария
    async validateScenario() {
        if (this.nodes.length === 0) {
            VRARPlatform.showNotification('Нет сценария для проверки', 'warning');
            return;
        }
        
        try {
            VRARPlatform.showNotification('Проверка сценария...', 'info');
            
            // Простая валидация для демо
            const issues = [];
            
            // Проверяем наличие начального узла
            const hasStart = this.nodes.some(n => n.type === 'start');
            if (!hasStart) {
                issues.push('Отсутствует начальный узел');
            }
            
            // Проверяем наличие конечного узла
            const hasEnd = this.nodes.some(n => n.type === 'end');
            if (!hasEnd) {
                issues.push('Отсутствует конечный узел');
            }
            
            // Проверяем изолированные узлы
            const connectedNodeIds = new Set();
            this.connections.forEach(conn => {
                connectedNodeIds.add(conn.from);
                connectedNodeIds.add(conn.to);
            });
            
            const isolatedNodes = this.nodes.filter(n => 
                !connectedNodeIds.has(n.id) && n.type !== 'start' && n.type !== 'end'
            );
            
            if (isolatedNodes.length > 0) {
                issues.push(`Найдены изолированные узлы: ${isolatedNodes.map(n => n.title).join(', ')}`);
            }
            
            if (issues.length === 0) {
                VRARPlatform.showNotification('Сценарий прошел проверку успешно', 'success');
            } else {
                VRARPlatform.showNotification(`Найдены проблемы: ${issues.join('; ')}`, 'warning');
            }
        } catch (error) {
            console.error('Ошибка проверки сценария:', error);
            VRARPlatform.showNotification('Ошибка при проверке сценария', 'error');
        }
    }
    
    // Показ модального окна
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Скрытие модального окна
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Обработка создания сценария
    async handleCreateScenario(form) {
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
            
            VRARPlatform.showNotification('Сценарий создан успешно', 'success');
            this.hideModal('createScenarioModal');
            
            // Загружаем новый сценарий
            this.loadScenario(data.id || Date.now());
        } catch (error) {
            console.error('Ошибка создания сценария:', error);
            VRARPlatform.showNotification('Не удалось создать сценарий', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

// Создание экземпляра редактора
let scenarioEditor;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    scenarioEditor = new ScenarioEditor();
});

// Глобальный экспорт
window.scenarioEditor = scenarioEditor;
