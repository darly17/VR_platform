
class AssetsManager {
    constructor() {
        this.currentView = 'grid';
        this.currentPage = 1;
        this.pageSize = 12;
        this.totalAssets = 0;
        this.assets = [];
        this.filters = {
            search: '',
            type: '',
            project_id: '',
            sort: 'newest'
        };
        
        this.init();
    }
    
    async init() {
        await this.loadAssets();
        this.setupEventListeners();
        this.setupUploadModal();
        this.updateStats();
    }
    
    // Загрузка активов
    async loadAssets() {
        try {
            const container = document.getElementById('assetsContainer');
            if (container) {
                container.innerHTML = `
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Загрузка активов...</p>
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
            
            if (this.filters.type) {
                params.type = this.filters.type;
            }
            
            if (this.filters.project_id) {
                params.project_id = this.filters.project_id;
            }
            
            if (this.filters.sort) {
                params.sort = this.filters.sort;
            }
            
            const response = await API.assets.getAll(params);
            
            if (response.success) {
                this.assets = response.data || response.assets || [];
                this.totalAssets = response.total || response.count || this.assets.length;
                
                this.renderAssets();
                this.renderPagination();
            } else {
                throw new Error(response.error || 'Ошибка загрузки активов');
            }
        } catch (error) {
            console.error('Ошибка загрузки активов:', error);
            
            const container = document.getElementById('assetsContainer');
            if (container) {
                container.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Не удалось загрузить активы: ${error.message}</p>
                        <button class="btn btn-secondary" onclick="assetsManager.loadAssets()">
                            <i class="fas fa-sync-alt"></i> Повторить
                        </button>
                    </div>
                `;
            }
            
            VRARPlatform.showNotification(`Ошибка загрузки активов: ${error.message}`, 'error');
        }
    }
    
    // Отображение активов
    renderAssets() {
        const container = document.getElementById('assetsContainer');
        if (!container) return;
        
        if (this.assets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-cube"></i>
                    <h3>Активы не найдены</h3>
                    <p>${this.filters.search ? 'Попробуйте изменить поисковый запрос' : 'Загрузите первый актив'}</p>
                    ${!this.filters.search ? `
                        <button class="btn btn-primary" id="uploadFirstAssetBtn">
                            <i class="fas fa-upload"></i> Загрузить актив
                        </button>
                    ` : ''}
                </div>
            `;
            
            // Обработчик для кнопки загрузки первого актива
            const uploadBtn = document.getElementById('uploadFirstAssetBtn');
            if (uploadBtn) {
                uploadBtn.addEventListener('click', () => this.showUploadModal());
            }
            
            return;
        }
        
        container.innerHTML = '';
        
        this.assets.forEach(asset => {
            const assetCard = this.createAssetCard(asset);
            container.appendChild(assetCard);
        });
    }
    
    // Создание карточки актива
    createAssetCard(asset) {
        const card = document.createElement('div');
        card.className = `asset-card ${this.currentView === 'list' ? 'list-view' : ''}`;
        card.dataset.id = asset.id;
        
        const icon = this.getAssetIcon(asset.type);
        const typeName = this.getAssetTypeName(asset.type);
        const fileSize = asset.file_size ? VRARPlatform.formatFileSize(asset.file_size) : 'Неизвестно';
        
        card.innerHTML = `
            <div class="asset-preview">
                <div class="asset-icon">
                    <i class="fas fa-${icon}"></i>
                </div>
                ${asset.thumbnail_url ? `
                    <img src="${asset.thumbnail_url}" alt="${asset.name}" class="asset-thumbnail">
                ` : ''}
                <div class="asset-overlay">
                    <button class="btn btn-icon view-asset-btn" title="Просмотр">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-icon download-asset-btn" title="Скачать">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
            <div class="asset-info">
                <h3 class="asset-title">${asset.name}</h3>
                <p class="asset-description">${asset.description || 'Без описания'}</p>
                <div class="asset-meta">
                    <span class="asset-type">${typeName}</span>
                    <span class="asset-size">${fileSize}</span>
                </div>
                ${asset.tags && asset.tags.length > 0 ? `
                    <div class="asset-tags">
                        ${asset.tags.slice(0, 3).map(tag => 
                            `<span class="asset-tag">${tag}</span>`
                        ).join('')}
                    </div>
                ` : ''}
                <div class="asset-footer">
                    <span class="asset-date">${VRARPlatform.formatDate(asset.created_at).split(' ')[0]}</span>
                    <div class="asset-actions">
                        <button class="btn btn-icon edit-asset-btn" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-icon delete-asset-btn" title="Удалить">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Обработчики событий
        const viewBtn = card.querySelector('.view-asset-btn');
        const downloadBtn = card.querySelector('.download-asset-btn');
        const editBtn = card.querySelector('.edit-asset-btn');
        const deleteBtn = card.querySelector('.delete-asset-btn');
        
        viewBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.viewAsset(asset.id);
        });
        
        downloadBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadAsset(asset.id);
        });
        
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.editAsset(asset.id);
        });
        
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteAsset(asset.id);
        });
        
        // Клик по карточке
        card.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.viewAsset(asset.id);
            }
        });
        
        return card;
    }
    
    // Получить иконку для типа актива
    getAssetIcon(type) {
        const icons = {
            'model': 'cube',
            'texture': 'image',
            'sound': 'volume-up',
            'material': 'palette',
            'animation': 'film',
            'script': 'file-code'
        };
        return icons[type] || 'file';
    }
    
    // Получить название типа актива
    getAssetTypeName(type) {
        const names = {
            'model': '3D Модель',
            'texture': 'Текстура',
            'sound': 'Звук',
            'material': 'Материал',
            'animation': 'Анимация',
            'script': 'Скрипт'
        };
        return names[type] || 'Актив';
    }
    
    // Просмотр актива
    async viewAsset(id) {
        try {
            const response = await API.assets.getById(id);
            if (response.success) {
                this.showAssetModal(response.data);
            }
        } catch (error) {
            console.error('Ошибка загрузки актива:', error);
            VRARPlatform.showNotification('Не удалось загрузить данные актива', 'error');
        }
    }
    
    // Скачивание актива
    async downloadAsset(id) {
        try {
            // В реальном приложении здесь будет ссылка на скачивание
            VRARPlatform.showNotification('Функция скачивания в разработке', 'info');
        } catch (error) {
            console.error('Ошибка скачивания:', error);
            VRARPlatform.showNotification('Не удалось скачать актив', 'error');
        }
    }
    
    // Редактирование актива
    async editAsset(id) {
        try {
            const response = await API.assets.getById(id);
            if (response.success) {
                this.showEditModal(response.data);
            }
        } catch (error) {
            console.error('Ошибка загрузки актива:', error);
            VRARPlatform.showNotification('Не удалось загрузить данные актива', 'error');
        }
    }
    
    // Удаление актива
    async deleteAsset(id) {
        if (!confirm('Вы уверены, что хотите удалить актив? Это действие нельзя отменить.')) {
            return;
        }
        
        try {
            const response = await API.assets.delete(id);
            if (response.success) {
                VRARPlatform.showNotification('Актив успешно удален', 'success');
                await this.loadAssets();
                await this.updateStats();
            } else {
                throw new Error(response.error || 'Ошибка удаления актива');
            }
        } catch (error) {
            console.error('Ошибка удаления актива:', error);
            VRARPlatform.showNotification(`Ошибка удаления актива: ${error.message}`, 'error');
        }
    }
    
    // Обновление статистики
    async updateStats() {
        try {
            const response = await API.assets.getStats();
            if (response.success) {
                const stats = response.data || response.stats || {};
                
                document.getElementById('totalAssets').textContent = stats.total || 0;
                document.getElementById('modelsCount').textContent = stats.models || 0;
                document.getElementById('texturesCount').textContent = stats.textures || 0;
                document.getElementById('soundsCount').textContent = stats.sounds || 0;
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
    
    // Настройка обработчиков событий
    setupEventListeners() {
        // Поиск
        const searchInput = document.getElementById('assetSearch');
        if (searchInput) {
            const debouncedSearch = debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadAssets();
            }, 300);
            
            searchInput.addEventListener('input', debouncedSearch);
        }
        
        // Фильтры
        const typeFilter = document.getElementById('assetTypeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.filters.type = e.target.value;
                this.currentPage = 1;
                this.loadAssets();
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
                this.renderAssets();
            });
        });
        
        // Обновление активов
        const refreshBtn = document.getElementById('refreshAssetsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadAssets();
                VRARPlatform.showNotification('Список активов обновлен', 'success');
            });
        }
    }
    
    // Настройка модального окна загрузки
    setupUploadModal() {
        const uploadBtn = document.getElementById('uploadAssetBtn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.showUploadModal());
        }
        
        const modal = document.getElementById('uploadAssetModal');
        const closeBtn = modal?.querySelector('.modal-close');
        const cancelBtn = modal?.querySelector('.cancel-btn');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal('uploadAssetModal'));
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal('uploadAssetModal'));
        }
        
        // Drag and drop
        const uploadArea = document.getElementById('fileUploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });
            
            // Клик для выбора файла
            uploadArea.addEventListener('click', () => {
                document.getElementById('assetFile').click();
            });
            
            // Выбор файла через input
            const fileInput = document.getElementById('assetFile');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        this.handleFileSelect(e.target.files[0]);
                    }
                });
            }
        }
        
        // Форма загрузки
        const form = document.getElementById('uploadAssetForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleUploadAsset(form);
            });
        }
    }
    
    // Обработка выбора файла
    handleFileSelect(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileNameInput = document.getElementById('assetName');
        
        if (fileInfo && fileNameInput) {
            fileInfo.innerHTML = `
                <p><strong>Файл:</strong> ${file.name}</p>
                <p><strong>Размер:</strong> ${VRARPlatform.formatFileSize(file.size)}</p>
                <p><strong>Тип:</strong> ${file.type || 'Неизвестно'}</p>
            `;
            
            // Установить имя файла как название актива (без расширения)
            const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
            fileNameInput.value = nameWithoutExt;
            
            // Определить тип файла по расширению
            this.autoDetectFileType(file.name);
        }
    }
    
    // Автоопределение типа файла по расширению
    autoDetectFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const typeSelect = document.getElementById('assetType');
        
        if (!typeSelect) return;
        
        const typeMap = {
            // 3D модели
            'obj': 'model',
            'fbx': 'model',
            'glb': 'model',
            'gltf': 'model',
            'stl': 'model',
            // Текстуры
            'jpg': 'texture',
            'jpeg': 'texture',
            'png': 'texture',
            'bmp': 'texture',
            'tga': 'texture',
            'hdr': 'texture',
            // Звуки
            'mp3': 'sound',
            'wav': 'sound',
            'ogg': 'sound',
            'flac': 'sound',
            // Видео
            'mp4': 'animation',
            'avi': 'animation',
            'mov': 'animation'
        };
        
        if (typeMap[ext]) {
            typeSelect.value = typeMap[ext];
        }
    }
    
    // Показать модальное окно загрузки
    showUploadModal() {
        const modal = document.getElementById('uploadAssetModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Сброс формы
            const form = document.getElementById('uploadAssetForm');
            if (form) {
                form.reset();
                const fileInfo = document.getElementById('fileInfo');
                if (fileInfo) fileInfo.innerHTML = '';
            }
        }
    }
    
    // Показать модальное окно просмотра
    showAssetModal(asset) {
        const modal = document.getElementById('viewAssetModal');
        if (!modal) return;
        
        const content = document.getElementById('assetViewContent');
        if (!content) return;
        
        const icon = this.getAssetIcon(asset.type);
        const typeName = this.getAssetTypeName(asset.type);
        const fileSize = asset.file_size ? VRARPlatform.formatFileSize(asset.file_size) : 'Неизвестно';
        
        content.innerHTML = `
            <div class="asset-details">
                <div class="asset-header">
                    <div class="asset-icon-large">
                        <i class="fas fa-${icon}"></i>
                    </div>
                    <div class="asset-header-info">
                        <h3>${asset.name}</h3>
                        <p>${asset.description || 'Без описания'}</p>
                        <div class="asset-meta-large">
                            <span class="badge badge-primary">${typeName}</span>
                            <span><i class="fas fa-hdd"></i> ${fileSize}</span>
                            <span><i class="fas fa-calendar"></i> ${VRARPlatform.formatDate(asset.created_at)}</span>
                            ${asset.project_name ? `<span><i class="fas fa-project-diagram"></i> ${asset.project_name}</span>` : ''}
                        </div>
                    </div>
                </div>
                
                ${asset.tags && asset.tags.length > 0 ? `
                    <div class="asset-tags-large">
                        <h4><i class="fas fa-tags"></i> Теги</h4>
                        <div class="tags-container">
                            ${asset.tags.map(tag => 
                                `<span class="asset-tag-large">${tag}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="asset-actions-large">
                    <button class="btn btn-primary download-full-btn" data-id="${asset.id}">
                        <i class="fas fa-download"></i> Скачать
                    </button>
                    <button class="btn btn-outline use-in-project-btn" data-id="${asset.id}">
                        <i class="fas fa-plus"></i> Использовать в проекте
                    </button>
                    <button class="btn btn-outline edit-full-btn" data-id="${asset.id}">
                        <i class="fas fa-edit"></i> Редактировать
                    </button>
                </div>
                
                <div class="asset-preview-large">
                    <h4><i class="fas fa-eye"></i> Предпросмотр</h4>
                    ${this.getAssetPreview(asset)}
                </div>
            </div>
        `;
        
        // Обработчики кнопок в модальном окне
        const downloadBtn = content.querySelector('.download-full-btn');
        const useBtn = content.querySelector('.use-in-project-btn');
        const editBtn = content.querySelector('.edit-full-btn');
        
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadAsset(asset.id));
        }
        
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.hideModal('viewAssetModal');
                this.editAsset(asset.id);
            });
        }
        
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    // Получить превью для актива
    getAssetPreview(asset) {
        switch (asset.type) {
            case 'model':
                return `
                    <div class="model-preview">
                        <div class="model-viewer-placeholder">
                            <i class="fas fa-cube"></i>
                            <p>3D Модель</p>
                            <small>Просмотр 3D моделей в разработке</small>
                        </div>
                    </div>
                `;
            case 'texture':
                return `
                    <div class="texture-preview">
                        <img src="${asset.url || '/assets/images/placeholder.jpg'}" alt="${asset.name}" style="max-width: 100%; border-radius: 8px;">
                    </div>
                `;
            case 'sound':
                return `
                    <div class="sound-preview">
                        <div class="audio-player">
                            <i class="fas fa-music"></i>
                            <p>Аудио файл</p>
                            <button class="btn btn-primary play-audio-btn">
                                <i class="fas fa-play"></i> Воспроизвести
                            </button>
                        </div>
                    </div>
                `;
            default:
                return `
                    <div class="default-preview">
                        <i class="fas fa-file"></i>
                        <p>Предпросмотр не доступен</p>
                    </div>
                `;
        }
    }
    
    // Скрыть модальное окно
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Обработка загрузки актива
    async handleUploadAsset(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
            
            const formData = new FormData(form);
            const fileInput = document.getElementById('assetFile');
            
            if (!fileInput.files.length) {
                throw new Error('Выберите файл для загрузки');
            }
            
            const file = fileInput.files[0];
            const additionalData = {};
            
            // Собираем дополнительные данные из формы
            const nameInput = document.getElementById('assetName');
            const descInput = document.getElementById('assetDescription');
            const typeSelect = document.getElementById('assetType');
            const projectSelect = document.getElementById('assetProject');
            const tagsInput = document.getElementById('assetTags');
            
            if (nameInput?.value) additionalData.name = nameInput.value;
            if (descInput?.value) additionalData.description = descInput.value;
            if (typeSelect?.value) additionalData.type = typeSelect.value;
            if (projectSelect?.value) additionalData.project_id = projectSelect.value;
            if (tagsInput?.value) additionalData.tags = tagsInput.value.split(',').map(tag => tag.trim());
            
            const response = await API.uploadFile('/assets/upload', file, additionalData);
            
            if (response.success) {
                VRARPlatform.showNotification('Актив успешно загружен', 'success');
                this.hideModal('uploadAssetModal');
                await this.loadAssets();
                await this.updateStats();
            } else {
                throw new Error(response.error || 'Ошибка загрузки актива');
            }
        } catch (error) {
            console.error('Ошибка загрузки актива:', error);
            VRARPlatform.showNotification(`Ошибка загрузки актива: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

// Создание экземпляра менеджера активов
let assetsManager;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    assetsManager = new AssetsManager();
});

// Глобальный экспорт
window.assetsManager = assetsManager;