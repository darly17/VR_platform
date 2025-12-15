/**
 * JavaScript для генерации кода
 */

class CodeGenerator {
    constructor() {
        this.currentSource = 'scenario';
        this.currentLanguage = 'python';
        this.currentTemplate = 'vr_basic';
        this.generatedCode = '';
        this.generatedFiles = [];
        this.generationHistory = [];
        
        this.init();
    }
    
    async init() {
        await this.loadScenarios();
        await this.loadHistory();
        this.setupEventListeners();
        this.setupLanguageSelector();
        this.setupSourceSelector();
    }
    
    // Загрузка сценариев для выбора
    async loadScenarios() {
        try {
            const scenarioSelect = document.getElementById('selectedScenario');
            const visualScriptSelect = document.getElementById('selectedVisualScript');
            
            if (!scenarioSelect && !visualScriptSelect) return;
            
            // В реальном приложении здесь будет запрос к API
            // Для демо используем заглушки
            
            const demoScenarios = [
                { id: 1, name: 'VR Обучение', project: 'Образовательный проект' },
                { id: 2, name: 'AR Навигация', project: 'Городской гид' },
                { id: 3, name: 'Виртуальная экскурсия', project: 'Музей VR' },
                { id: 4, name: 'Игровой сценарий', project: 'VR Игра' }
            ];
            
            if (scenarioSelect) {
                scenarioSelect.innerHTML = '<option value="">Выберите сценарий</option>' +
                    demoScenarios.map(s => 
                        `<option value="${s.id}">${s.name} (${s.project})</option>`
                    ).join('');
            }
            
            if (visualScriptSelect) {
                visualScriptSelect.innerHTML = '<option value="">Выберите скрипт</option>' +
                    demoScenarios.map(s => 
                        `<option value="${s.id}">${s.name} (визуальный скрипт)</option>`
                    ).join('');
            }
        } catch (error) {
            console.error('Ошибка загрузки сценариев:', error);
        }
    }
    
    // Загрузка истории генерации
    async loadHistory() {
        try {
            const history = JSON.parse(localStorage.getItem('codegen_history')) || [];
            this.generationHistory = history;
            this.renderHistory();
        } catch (error) {
            console.error('Ошибка загрузки истории:', error);
        }
    }
    
    // Настройка обработчиков событий
    setupEventListeners() {
        // Переключение источника
        const sourceType = document.getElementById('sourceType');
        if (sourceType) {
            sourceType.addEventListener('change', (e) => {
                this.currentSource = e.target.value;
                this.updateSourceVisibility();
            });
        }
        
        // Кнопки действий
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.classList.contains('action-btn')) {
                    const source = card.dataset.source;
                    this.handleActionClick(source);
                }
            });
        });
        
        // Генерация кода
        const generateBtn = document.getElementById('generateCodeBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateCode());
        }
        
        // Копирование кода
        const copyBtn = document.getElementById('copyAllBtn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyAllCode());
        }
        
        // Скачивание
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadCode());
        }
        
        // Валидация кода
        const validateBtn = document.getElementById('validateCodeBtn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this.validateCode());
        }
        
        // Очистка истории
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        }
    }
    
    // Настройка селектора языка
    setupLanguageSelector() {
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Удаляем активный класс у всех
                languageOptions.forEach(opt => opt.classList.remove('active'));
                // Добавляем активный класс выбранному
                option.classList.add('active');
                this.currentLanguage = option.dataset.language;
            });
        });
    }
    
    // Настройка селектора источника
    setupSourceSelector() {
        const sourceType = document.getElementById('sourceType');
        if (sourceType) {
            this.currentSource = sourceType.value;
            this.updateSourceVisibility();
        }
    }
    
    // Обновление видимости элементов в зависимости от источника
    updateSourceVisibility() {
        const sourceSections = document.querySelectorAll('.source-selector');
        sourceSections.forEach(section => {
            section.classList.add('hidden');
        });
        
        const activeSection = document.getElementById(`${this.currentSource}Source`);
        if (activeSection) {
            activeSection.classList.remove('hidden');
        }
    }
    
    // Обработка клика по кнопке действия
    handleActionClick(source) {
        const sourceSelect = document.getElementById('sourceType');
        if (sourceSelect) {
            sourceSelect.value = source;
            this.currentSource = source;
            this.updateSourceVisibility();
            
            // Прокрутка к настройкам
            document.querySelector('.codegen-configuration').scrollIntoView({
                behavior: 'smooth'
            });
        }
    }
    
    // Генерация кода
    async generateCode() {
        try {
            const generateBtn = document.getElementById('generateCodeBtn');
            const generateStatus = document.getElementById('generateStatus');
            
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
            }
            
            if (generateStatus) {
                generateStatus.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Генерация кода...</p>';
            }
            
            // Получаем настройки
            const settings = this.getGenerationSettings();
            
            // В реальном приложении здесь будет запрос к API
            // Для демо генерируем код локально
            await this.simulateGeneration(settings);
            
            // Сохраняем в историю
            this.saveToHistory(settings);
            
            if (generateStatus) {
                generateStatus.innerHTML = '<p><i class="fas fa-check"></i> Код успешно сгенерирован</p>';
            }
            
            VRARPlatform.showNotification('Код успешно сгенерирован', 'success');
        } catch (error) {
            console.error('Ошибка генерации кода:', error);
            
            const generateStatus = document.getElementById('generateStatus');
            if (generateStatus) {
                generateStatus.innerHTML = `<p><i class="fas fa-times"></i> Ошибка: ${error.message}</p>`;
            }
            
            VRARPlatform.showNotification(`Ошибка генерации кода: ${error.message}`, 'error');
        } finally {
            const generateBtn = document.getElementById('generateCodeBtn');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-cogs"></i> Сгенерировать код';
            }
        }
    }
    
    // Получение настроек генерации
    getGenerationSettings() {
        const sourceId = this.getSelectedSourceId();
        const targetPlatform = document.getElementById('targetPlatform')?.value || 'unity';
        const codeStyle = document.getElementById('codeStyle')?.value || 'standard';
        const generationMode = document.getElementById('generationMode')?.value || 'full';
        const outputFormat = document.getElementById('outputFormat')?.value || 'single';
        const namespace = document.getElementById('namespace')?.value || 'MyVRProject';
        
        // Флаги
        const includeComments = document.getElementById('includeComments')?.checked || false;
        const includeErrorHandling = document.getElementById('includeErrorHandling')?.checked || false;
        const includeLogging = document.getElementById('includeLogging')?.checked || false;
        const optimizeCode = document.getElementById('optimizeCode')?.checked || false;
        const generateTests = document.getElementById('generateTests')?.checked || false;
        
        return {
            source: this.currentSource,
            source_id: sourceId,
            language: this.currentLanguage,
            template: this.currentTemplate,
            target_platform: targetPlatform,
            code_style: codeStyle,
            generation_mode: generationMode,
            output_format: outputFormat,
            namespace: namespace,
            include_comments: includeComments,
            include_error_handling: includeErrorHandling,
            include_logging: includeLogging,
            optimize_code: optimizeCode,
            generate_tests: generateTests,
            timestamp: new Date().toISOString()
        };
    }
    
    // Получение ID выбранного источника
    getSelectedSourceId() {
        switch (this.currentSource) {
            case 'scenario':
                return document.getElementById('selectedScenario')?.value;
            case 'visual':
                return document.getElementById('selectedVisualScript')?.value;
            case 'template':
                return document.getElementById('selectedTemplate')?.value;
            default:
                return null;
        }
    }
    
    // Симуляция генерации кода (для демо)
    async simulateGeneration(settings) {
        return new Promise((resolve) => {
            setTimeout(() => {
                this.generateDemoCode(settings);
                resolve();
            }, 1500);
        });
    }
    
    // Генерация демо-кода
    generateDemoCode(settings) {
        const code = this.generateCodeByLanguage(settings);
        this.generatedCode = code;
        this.generatedFiles = [{
            name: this.getFileName(settings),
            content: code,
            language: settings.language
        }];
        
        this.renderGeneratedCode();
        this.updateCodeInfo();
    }
    
    // Генерация кода в зависимости от языка
    generateCodeByLanguage(settings) {
        const languageGenerators = {
            'python': this.generatePythonCode,
            'csharp': this.generateCSharpCode,
            'cpp': this.generateCppCode,
            'java': this.generateJavaCode,
            'javascript': this.generateJavaScriptCode
        };
        
        const generator = languageGenerators[settings.language] || this.generatePythonCode;
        return generator.call(this, settings);
    }
    
    // Генерация Python кода
    generatePythonCode(settings) {
        const namespace = settings.namespace || 'vr_scenario';
        const hasComments = settings.include_comments;
        const hasErrorHandling = settings.include_error_handling;
        
        return `"""
Генератор кода VR/AR Platform
Сгенерировано: ${new Date().toLocaleString()}
Язык: Python
Платформа: ${settings.target_platform}
Источник: ${settings.source}
"""

import logging
${hasErrorHandling ? 'import traceback' : ''}
import time
from enum import Enum
from typing import Dict, List, Optional, Callable

${hasComments ? '# Настройки логирования' : ''}
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

${hasComments ? '# Перечисление состояний' : ''}
class State(Enum):
    INIT = "init"
    LOADING = "loading"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

${hasComments ? '# Класс VR/AR сценария' : ''}
class ${namespace}Scene:
    ${hasComments ? '# Конструктор класса' : ''}
    def __init__(self, name: str = "VR_Scene"):
        self.name = name
        self.current_state = State.INIT
        self.states: Dict[State, Callable] = {}
        self.transitions: Dict[State, List[State]] = {}
        self.data = {}
        self.initialized = False
        
        ${hasComments ? '# Инициализация состояний' : ''}
        self._init_states()
    
    ${hasComments ? '# Инициализация состояний' : ''}
    def _init_states(self):
        self.states[State.INIT] = self._state_init
        self.states[State.LOADING] = self._state_loading
        self.states[State.RUNNING] = self._state_running
        self.states[State.PAUSED] = self._state_paused
        self.states[State.COMPLETED] = self._state_completed
        self.states[State.ERROR] = self._state_error
        
        ${hasComments ? '# Определение переходов' : ''}
        self.transitions[State.INIT] = [State.LOADING, State.ERROR]
        self.transitions[State.LOADING] = [State.RUNNING, State.ERROR]
        self.transitions[State.RUNNING] = [State.PAUSED, State.COMPLETED, State.ERROR]
        self.transitions[State.PAUSED] = [State.RUNNING, State.ERROR]
    
    ${hasComments ? '# Переход между состояниями' : ''}
    def transition_to(self, new_state: State) -> bool:
        ${hasErrorHandling ? 'try:' : ''}
        ${hasErrorHandling ? '    ' : ''}if new_state in self.transitions.get(self.current_state, []):
        ${hasErrorHandling ? '    ' : ''}    logger.info(f"Переход из {self.current_state.value} в {new_state.value}")
        ${hasErrorHandling ? '    ' : ''}    old_state = self.current_state
        ${hasErrorHandling ? '    ' : ''}    self.current_state = new_state
        ${hasErrorHandling ? '    ' : ''}    
        ${hasErrorHandling ? '    ' : ''}    ${hasComments ? '# Выполнение действий при переходе' : ''}
        ${hasErrorHandling ? '    ' : ''}    self._on_state_exit(old_state)
        ${hasErrorHandling ? '    ' : ''}    self._on_state_enter(new_state)
        ${hasErrorHandling ? '    ' : ''}    
        ${hasErrorHandling ? '    ' : ''}    return True
        ${hasErrorHandling ? '    ' : ''}else:
        ${hasErrorHandling ? '    ' : ''}    logger.warning(f"Недопустимый переход из {self.current_state.value} в {new_state.value}")
        ${hasErrorHandling ? '    ' : ''}    return False
        ${hasErrorHandling ? 'except Exception as e:' : ''}
        ${hasErrorHandling ? '    logger.error(f"Ошибка при переходе: {e}")' : ''}
        ${hasErrorHandling ? '    logger.error(traceback.format_exc())' : ''}
        ${hasErrorHandling ? '    return False' : ''}
    
    ${hasComments ? '# Основной цикл обновления' : ''}
    def update(self, delta_time: float = 0.016):
        ${hasErrorHandling ? 'try:' : ''}
        ${hasErrorHandling ? '    ' : ''}if self.current_state in self.states:
        ${hasErrorHandling ? '    ' : ''}    self.states[self.current_state](delta_time)
        ${hasErrorHandling ? 'except Exception as e:' : ''}
        ${hasErrorHandling ? '    logger.error(f"Ошибка в состоянии {self.current_state.value}: {e}")' : ''}
        ${hasErrorHandling ? '    self.transition_to(State.ERROR)' : ''}
    
    ${hasComments ? '# Методы состояний' : ''}
    def _state_init(self, delta_time: float):
        logger.info("Инициализация сценария...")
        ${hasComments ? '# Инициализация ресурсов' : ''}
        time.sleep(0.1)  # Симуляция загрузки
        self.initialized = True
        self.transition_to(State.LOADING)
    
    def _state_loading(self, delta_time: float):
        logger.info("Загрузка ресурсов...")
        ${hasComments ? '# Загрузка 3D моделей, текстур и т.д.' : ''}
        time.sleep(0.5)  # Симуляция загрузки
        self.data["assets_loaded"] = True
        self.transition_to(State.RUNNING)
    
    def _state_running(self, delta_time: float):
        ${hasComments ? '# Основная логика сценария' : ''}
        ${hasComments ? '# Этот метод должен переопределяться для конкретного сценария' : ''}
        pass
    
    def _state_paused(self, delta_time: float):
        logger.info("Сценарий на паузе")
    
    def _state_completed(self, delta_time: float):
        logger.info("Сценарий завершен успешно")
    
    def _state_error(self, delta_time: float):
        logger.error("Произошла ошибка в сценарии")
    
    ${hasComments ? '# События при входе/выходе из состояния' : ''}
    def _on_state_enter(self, state: State):
        logger.info(f"Вход в состояние: {state.value}")
    
    def _on_state_exit(self, state: State):
        logger.info(f"Выход из состояния: {state.value}")
    
    ${hasComments ? '# Метод запуска сценария' : ''}
    def start(self):
        logger.info(f"Запуск сценария: {self.name}")
        if not self.initialized:
            self.transition_to(State.INIT)
    
    ${hasComments ? '# Метод остановки сценария' : ''}
    def stop(self):
        logger.info(f"Остановка сценария: {self.name}")
        self.transition_to(State.COMPLETED)

${hasComments ? '# Основная функция' : ''}
if __name__ == "__main__":
    ${hasComments ? '# Создание и запуск сценария' : ''}
    scene = ${namespace}Scene("Пример VR сценария")
    scene.start()
    
    ${hasComments ? '# Имитация цикла обновления' : ''}
    try:
        for i in range(100):
            scene.update(0.016)
            time.sleep(0.016)
    except KeyboardInterrupt:
        scene.stop()
    
    logger.info("Сценарий завершен")`;
    }
    
    // Генерация C# кода
    generateCSharpCode(settings) {
        const namespace = settings.namespace || 'VRProject';
        
        return `// Генератор кода VR/AR Platform
// Сгенерировано: ${new Date().toLocaleString()}
// Язык: C#
// Платформа: ${settings.target_platform}
// Источник: ${settings.source}

using System;
using System.Collections.Generic;
using UnityEngine;

namespace ${namespace}
{
    // Перечисление состояний
    public enum SceneState
    {
        Init,
        Loading,
        Running,
        Paused,
        Completed,
        Error
    }

    // Интерфейс для состояний
    public interface ISceneState
    {
        void Enter();
        void Update(float deltaTime);
        void Exit();
        SceneState GetStateType();
    }

    // Базовый класс VR/AR сценария
    public class VRScene : MonoBehaviour
    {
        private Dictionary<SceneState, ISceneState> states = new Dictionary<SceneState, ISceneState>();
        private ISceneState currentState;
        private SceneData sceneData = new SceneData();
        
        // Свойства
        public string SceneName { get; private set; }
        public bool IsInitialized { get; private set; }
        public SceneState CurrentStateType => currentState?.GetStateType() ?? SceneState.Init;

        // Инициализация
        void Start()
        {
            Initialize("VR_Scene");
        }

        // Инициализация сценария
        public void Initialize(string sceneName)
        {
            SceneName = sceneName;
            
            // Создание состояний
            states[SceneState.Init] = new InitState(this);
            states[SceneState.Loading] = new LoadingState(this);
            states[SceneState.Running] = new RunningState(this);
            states[SceneState.Paused] = new PausedState(this);
            states[SceneState.Completed] = new CompletedState(this);
            states[SceneState.Error] = new ErrorState(this);
            
            // Начальное состояние
            TransitionTo(SceneState.Init);
            IsInitialized = true;
            
            Debug.Log($"Сценарий '{SceneName}' инициализирован");
        }

        // Обновление каждый кадр
        void Update()
        {
            if (currentState != null)
            {
                currentState.Update(Time.deltaTime);
            }
        }

        // Переход между состояниями
        public bool TransitionTo(SceneState newState)
        {
            try
            {
                if (states.ContainsKey(newState))
                {
                    if (currentState != null)
                    {
                        currentState.Exit();
                    }
                    
                    currentState = states[newState];
                    currentState.Enter();
                    
                    Debug.Log($"Переход в состояние: {newState}");
                    return true;
                }
                
                Debug.LogWarning($"Недопустимый переход в состояние: {newState}");
                return false;
            }
            catch (Exception ex)
            {
                Debug.LogError($"Ошибка при переходе: {ex.Message}");
                TransitionTo(SceneState.Error);
                return false;
            }
        }

        // Запуск сценария
        public void StartScene()
        {
            Debug.Log($"Запуск сценария: {SceneName}");
            TransitionTo(SceneState.Init);
        }

        // Остановка сценария
        public void StopScene()
        {
            Debug.Log($"Остановка сценария: {SceneName}");
            TransitionTo(SceneState.Completed);
        }

        // Данные сценария
        public SceneData GetSceneData() => sceneData;
    }

    // Класс данных сценария
    public class SceneData
    {
        public Dictionary<string, object> Data = new Dictionary<string, object>();
        
        public void Set(string key, object value) => Data[key] = value;
        public T Get<T>(string key) => Data.ContainsKey(key) ? (T)Data[key] : default;
        public bool Has(string key) => Data.ContainsKey(key);
    }

    // Реализация состояний
    public class InitState : ISceneState
    {
        private VRScene scene;
        
        public InitState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Init;
        
        public void Enter()
        {
            Debug.Log("Вход в состояние: Инициализация");
            // Инициализация ресурсов
        }
        
        public void Update(float deltaTime)
        {
            // Завершение инициализации
            scene.GetSceneData().Set("initialized", true);
            scene.TransitionTo(SceneState.Loading);
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Инициализация");
        }
    }

    public class LoadingState : ISceneState
    {
        private VRScene scene;
        private float loadTime = 0;
        
        public LoadingState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Loading;
        
        public void Enter()
        {
            Debug.Log("Вход в состояние: Загрузка");
            loadTime = 0;
        }
        
        public void Update(float deltaTime)
        {
            loadTime += deltaTime;
            
            // Симуляция загрузки
            if (loadTime >= 2.0f) // 2 секунды загрузки
            {
                scene.GetSceneData().Set("assets_loaded", true);
                scene.TransitionTo(SceneState.Running);
            }
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Загрузка");
        }
    }

    public class RunningState : ISceneState
    {
        private VRScene scene;
        
        public RunningState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Running;
        
        public void Enter()
        {
            Debug.Log("Вход в состояние: Выполнение");
        }
        
        public void Update(float deltaTime)
        {
            // Основная логика сценария
            // Этот метод должен быть расширен для конкретного сценария
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Выполнение");
        }
    }

    public class PausedState : ISceneState
    {
        private VRScene scene;
        
        public PausedState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Paused;
        
        public void Enter()
        {
            Debug.Log("Вход в состояние: Пауза");
        }
        
        public void Update(float deltaTime)
        {
            // Логика в состоянии паузы
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Пауза");
        }
    }

    public class CompletedState : ISceneState
    {
        private VRScene scene;
        
        public CompletedState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Completed;
        
        public void Enter()
        {
            Debug.Log("Вход в состояние: Завершено");
        }
        
        public void Update(float deltaTime)
        {
            // Логика завершения
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Завершено");
        }
    }

    public class ErrorState : ISceneState
    {
        private VRScene scene;
        
        public ErrorState(VRScene scene) => this.scene = scene;
        public SceneState GetStateType() => SceneState.Error;
        
        public void Enter()
        {
            Debug.LogError("Вход в состояние: Ошибка");
        }
        
        public void Update(float deltaTime)
        {
            // Логика обработки ошибок
        }
        
        public void Exit()
        {
            Debug.Log("Выход из состояния: Ошибка");
        }
    }
}`;
    }
    
    // Генерация C++ кода
    generateCppCode(settings) {
        const namespace = settings.namespace || 'VR';
        
        return `// Генератор кода VR/AR Platform
// Сгенерировано: ${new Date().toLocaleString()}
// Язык: C++
// Платформа: ${settings.target_platform}
// Источник: ${settings.source}

#include <iostream>
#include <string>
#include <map>
#include <functional>
#include <chrono>
#include <thread>
#include <memory>

namespace ${namespace} {

// Перечисление состояний
enum class SceneState {
    INIT,
    LOADING,
    RUNNING,
    PAUSED,
    COMPLETED,
    ERROR
};

// Класс данных сценария
class SceneData {
private:
    std::map<std::string, void*> data;
    
public:
    template<typename T>
    void set(const std::string& key, T* value) {
        data[key] = static_cast<void*>(value);
    }
    
    template<typename T>
    T* get(const std::string& key) {
        auto it = data.find(key);
        if (it != data.end()) {
            return static_cast<T*>(it->second);
        }
        return nullptr;
    }
    
    bool has(const std::string& key) const {
        return data.find(key) != data.end();
    }
};

// Базовый класс состояния
class SceneStateBase {
protected:
    std::string stateName;
    
public:
    SceneStateBase(const std::string& name) : stateName(name) {}
    virtual ~SceneStateBase() = default;
    
    virtual void enter() = 0;
    virtual void update(float deltaTime) = 0;
    virtual void exit() = 0;
    virtual SceneState getType() const = 0;
    
    std::string getName() const { return stateName; }
};

// Класс VR/AR сценария
class VRScene {
private:
    std::string sceneName;
    SceneState currentState;
    std::map<SceneState, std::unique_ptr<SceneStateBase>> states;
    SceneData sceneData;
    bool initialized;
    
    // Состояния
    class InitState : public SceneStateBase {
    private:
        VRScene* scene;
        
    public:
        InitState(VRScene* s) : SceneStateBase("INIT"), scene(s) {}
        
        SceneState getType() const override { return SceneState::INIT; }
        
        void enter() override {
            std::cout << "Вход в состояние: Инициализация" << std::endl;
        }
        
        void update(float deltaTime) override {
            // Инициализация ресурсов
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            scene->setData("initialized", new bool(true));
            scene->transitionTo(SceneState::LOADING);
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Инициализация" << std::endl;
        }
    };
    
    class LoadingState : public SceneStateBase {
    private:
        VRScene* scene;
        float loadTime;
        
    public:
        LoadingState(VRScene* s) : SceneStateBase("LOADING"), scene(s), loadTime(0) {}
        
        SceneState getType() const override { return SceneState::LOADING; }
        
        void enter() override {
            std::cout << "Вход в состояние: Загрузка" << std::endl;
            loadTime = 0;
        }
        
        void update(float deltaTime) override {
            loadTime += deltaTime;
            
            // Симуляция загрузки
            if (loadTime >= 2.0f) { // 2 секунды загрузки
                scene->setData("assets_loaded", new bool(true));
                scene->transitionTo(SceneState::RUNNING);
            }
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Загрузка" << std::endl;
        }
    };
    
    class RunningState : public SceneStateBase {
    private:
        VRScene* scene;
        
    public:
        RunningState(VRScene* s) : SceneStateBase("RUNNING"), scene(s) {}
        
        SceneState getType() const override { return SceneState::RUNNING; }
        
        void enter() override {
            std::cout << "Вход в состояние: Выполнение" << std::endl;
        }
        
        void update(float deltaTime) override {
            // Основная логика сценария
            // Этот метод должен быть расширен для конкретного сценария
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Выполнение" << std::endl;
        }
    };
    
    class PausedState : public SceneStateBase {
    private:
        VRScene* scene;
        
    public:
        PausedState(VRScene* s) : SceneStateBase("PAUSED"), scene(s) {}
        
        SceneState getType() const override { return SceneState::PAUSED; }
        
        void enter() override {
            std::cout << "Вход в состояние: Пауза" << std::endl;
        }
        
        void update(float deltaTime) override {
            // Логика в состоянии паузы
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Пауза" << std::endl;
        }
    };
    
    class CompletedState : public SceneStateBase {
    private:
        VRScene* scene;
        
    public:
        CompletedState(VRScene* s) : SceneStateBase("COMPLETED"), scene(s) {}
        
        SceneState getType() const override { return SceneState::COMPLETED; }
        
        void enter() override {
            std::cout << "Вход в состояние: Завершено" << std::endl;
        }
        
        void update(float deltaTime) override {
            // Логика завершения
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Завершено" << std::endl;
        }
    };
    
    class ErrorState : public SceneStateBase {
    private:
        VRScene* scene;
        
    public:
        ErrorState(VRScene* s) : SceneStateBase("ERROR"), scene(s) {}
        
        SceneState getType() const override { return SceneState::ERROR; }
        
        void enter() override {
            std::cerr << "Вход в состояние: Ошибка" << std::endl;
        }
        
        void update(float deltaTime) override {
            // Логика обработки ошибок
        }
        
        void exit() override {
            std::cout << "Выход из состояния: Ошибка" << std::endl;
        }
    };
    
public:
    VRScene(const std::string& name) 
        : sceneName(name), currentState(SceneState::INIT), initialized(false) {
        
        // Создание состояний
        states[SceneState::INIT] = std::make_unique<InitState>(this);
        states[SceneState::LOADING] = std::make_unique<LoadingState>(this);
        states[SceneState::RUNNING] = std::make_unique<RunningState>(this);
        states[SceneState::PAUSED] = std::make_unique<PausedState>(this);
        states[SceneState::COMPLETED] = std::make_unique<CompletedState>(this);
        states[SceneState::ERROR] = std::make_unique<ErrorState>(this);
    }
    
    // Инициализация сценария
    void initialize() {
        std::cout << "Инициализация сценария: " << sceneName << std::endl;
        transitionTo(SceneState::INIT);
        initialized = true;
    }
    
    // Обновление сценария
    void update(float deltaTime) {
        auto it = states.find(currentState);
        if (it != states.end()) {
            it->second->update(deltaTime);
        }
    }
    
    // Переход между состояниями
    bool transitionTo(SceneState newState) {
        try {
            auto oldIt = states.find(currentState);
            auto newIt = states.find(newState);
            
            if (newIt != states.end()) {
                if (oldIt != states.end()) {
                    oldIt->second->exit();
                }
                
                currentState = newState;
                newIt->second->enter();
                
                std::cout << "Переход в состояние: " << newIt->second->getName() << std::endl;
                return true;
            }
            
            std::cout << "Недопустимый переход" << std::endl;
            return false;
        }
        catch (const std::exception& e) {
            std::cerr << "Ошибка при переходе: " << e.what() << std::endl;
            transitionTo(SceneState::ERROR);
            return false;
        }
    }
    
    // Запуск сценария
    void start() {
        std::cout << "Запуск сценария: " << sceneName << std::endl;
        if (!initialized) {
            initialize();
        }
        transitionTo(SceneState::INIT);
    }
    
    // Остановка сценария
    void stop() {
        std::cout << "Остановка сценария: " << sceneName << std::endl;
        transitionTo(SceneState::COMPLETED);
    }
    
    // Установка данных
    template<typename T>
    void setData(const std::string& key, T* value) {
        sceneData.set<T>(key, value);
    }
    
    // Получение данных
    template<typename T>
    T* getData(const std::string& key) {
        return sceneData.get<T>(key);
    }
    
    // Получение текущего состояния
    SceneState getCurrentState() const {
        return currentState;
    }
};

} // namespace ${namespace}

// Основная функция
int main() {
    using namespace ${namespace};
    
    std::cout << "VR/AR Platform - Пример сценария на C++" << std::endl;
    
    // Создание сценария
    VRScene scene("Пример VR сценария");
    scene.start();
    
    // Имитация цикла обновления
    try {
        for (int i = 0; i < 100; ++i) {
            scene.update(0.016f);
            std::this_thread::sleep_for(std::chrono::milliseconds(16));
        }
    }
    catch (...) {
        scene.stop();
    }
    
    std::cout << "Сценарий завершен" << std::endl;
    return 0;
}`;
    }
    
    // Генерация Java кода
    generateJavaCode(settings) {
        const namespace = settings.namespace.replace(/[^a-zA-Z0-9]/g, '') || 'VRScene';
        
        return `// Генератор кода VR/AR Platform
// Сгенерировано: ${new Date().toLocaleString()}
// Язык: Java
// Платформа: ${settings.target_platform}
// Источник: ${settings.source}

package com.vrarplatform.${namespace.toLowerCase()};

import java.util.*;

// Перечисление состояний
enum SceneState {
    INIT,
    LOADING,
    RUNNING,
    PAUSED,
    COMPLETED,
    ERROR
}

// Интерфейс состояния
interface SceneStateInterface {
    void enter();
    void update(float deltaTime);
    void exit();
    SceneState getType();
}

// Класс данных сценария
class SceneData {
    private Map<String, Object> data = new HashMap<>();
    
    public void set(String key, Object value) {
        data.put(key, value);
    }
    
    @SuppressWarnings("unchecked")
    public <T> T get(String key) {
        return (T) data.get(key);
    }
    
    public boolean has(String key) {
        return data.containsKey(key);
    }
}

// Базовый класс VR/AR сценария
public class ${namespace} {
    private String sceneName;
    private SceneState currentState;
    private Map<SceneState, SceneStateInterface> states = new EnumMap<>(SceneState.class);
    private SceneData sceneData = new SceneData();
    private boolean initialized = false;
    
    // Конструктор
    public ${namespace}(String name) {
        this.sceneName = name;
        initializeStates();
    }
    
    // Инициализация состояний
    private void initializeStates() {
        states.put(SceneState.INIT, new InitState());
        states.put(SceneState.LOADING, new LoadingState());
        states.put(SceneState.RUNNING, new RunningState());
        states.put(SceneState.PAUSED, new PausedState());
        states.put(SceneState.COMPLETED, new CompletedState());
        states.put(SceneState.ERROR, new ErrorState());
    }
    
    // Запуск сценария
    public void start() {
        System.out.println("Запуск сценария: " + sceneName);
        if (!initialized) {
            initialize();
        }
        transitionTo(SceneState.INIT);
    }
    
    // Инициализация
    public void initialize() {
        System.out.println("Инициализация сценария: " + sceneName);
        initialized = true;
    }
    
    // Обновление сценария
    public void update(float deltaTime) {
        SceneStateInterface state = states.get(currentState);
        if (state != null) {
            state.update(deltaTime);
        }
    }
    
    // Переход между состояниями
    public boolean transitionTo(SceneState newState) {
        try {
            SceneStateInterface newStateObj = states.get(newState);
            if (newStateObj != null) {
                SceneStateInterface oldStateObj = states.get(currentState);
                if (oldStateObj != null) {
                    oldStateObj.exit();
                }
                
                currentState = newState;
                newStateObj.enter();
                
                System.out.println("Переход в состояние: " + newState);
                return true;
            }
            
            System.out.println("Недопустимый переход: " + newState);
            return false;
        } catch (Exception e) {
            System.err.println("Ошибка при переходе: " + e.getMessage());
            transitionTo(SceneState.ERROR);
            return false;
        }
    }
    
    // Остановка сценария
    public void stop() {
        System.out.println("Остановка сценария: " + sceneName);
        transitionTo(SceneState.COMPLETED);
    }
    
    // Реализации состояний
    class InitState implements SceneStateInterface {
        @Override
        public SceneState getType() { return SceneState.INIT; }
        
        @Override
        public void enter() {
            System.out.println("Вход в состояние: Инициализация");
        }
        
        @Override
        public void update(float deltaTime) {
            try {
                // Инициализация ресурсов
                Thread.sleep(100);
                sceneData.set("initialized", true);
                transitionTo(SceneState.LOADING);
            } catch (InterruptedException e) {
                transitionTo(SceneState.ERROR);
            }
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Инициализация");
        }
    }
    
    class LoadingState implements SceneStateInterface {
        private float loadTime = 0;
        
        @Override
        public SceneState getType() { return SceneState.LOADING; }
        
        @Override
        public void enter() {
            System.out.println("Вход в состояние: Загрузка");
            loadTime = 0;
        }
        
        @Override
        public void update(float deltaTime) {
            loadTime += deltaTime;
            
            // Симуляция загрузки
            if (loadTime >= 2.0f) { // 2 секунды загрузки
                sceneData.set("assets_loaded", true);
                transitionTo(SceneState.RUNNING);
            }
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Загрузка");
        }
    }
    
    class RunningState implements SceneStateInterface {
        @Override
        public SceneState getType() { return SceneState.RUNNING; }
        
        @Override
        public void enter() {
            System.out.println("Вход в состояние: Выполнение");
        }
        
        @Override
        public void update(float deltaTime) {
            // Основная логика сценария
            // Этот метод должен быть расширен для конкретного сценария
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Выполнение");
        }
    }
    
    class PausedState implements SceneStateInterface {
        @Override
        public SceneState getType() { return SceneState.PAUSED; }
        
        @Override
        public void enter() {
            System.out.println("Вход в состояние: Пауза");
        }
        
        @Override
        public void update(float deltaTime) {
            // Логика в состоянии паузы
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Пауза");
        }
    }
    
    class CompletedState implements SceneStateInterface {
        @Override
        public SceneState getType() { return SceneState.COMPLETED; }
        
        @Override
        public void enter() {
            System.out.println("Вход в состояние: Завершено");
        }
        
        @Override
        public void update(float deltaTime) {
            // Логика завершения
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Завершено");
        }
    }
    
    class ErrorState implements SceneStateInterface {
        @Override
        public SceneState getType() { return SceneState.ERROR; }
        
        @Override
        public void enter() {
            System.err.println("Вход в состояние: Ошибка");
        }
        
        @Override
        public void update(float deltaTime) {
            // Логика обработки ошибок
        }
        
        @Override
        public void exit() {
            System.out.println("Выход из состояния: Ошибка");
        }
    }
    
    // Главный метод
    public static void main(String[] args) {
        System.out.println("VR/AR Platform - Пример сценария на Java");
        
        ${namespace} scene = new ${namespace}("Пример VR сценария");
        scene.start();
        
        // Имитация цикла обновления
        try {
            for (int i = 0; i < 100; i++) {
                scene.update(0.016f);
                Thread.sleep(16);
            }
        } catch (InterruptedException e) {
            scene.stop();
        }
        
        System.out.println("Сценарий завершен");
    }
}`;
    }
    
    // Генерация JavaScript кода
    generateJavaScriptCode(settings) {
        return `// Генератор кода VR/AR Platform
// Сгенерировано: ${new Date().toLocaleString()}
// Язык: JavaScript
// Платформа: ${settings.target_platform}
// Источник: ${settings.source}

/**
 * Класс VR/AR сценария на JavaScript
 */
class VRScene {
    /**
     * Конструктор сценария
     * @param {string} name - Название сценария
     */
    constructor(name = 'VR_Scene') {
        this.name = name;
        this.currentState = 'INIT';
        this.states = {};
        this.transitions = {};
        this.data = {};
        this.initialized = false;
        this.frameCount = 0;
        
        // Инициализация состояний
        this._initStates();
    }
    
    /**
     * Инициализация состояний сценария
     * @private
     */
    _initStates() {
        // Определение состояний
        this.states = {
            INIT: {
                enter: () => this._onStateEnter('INIT'),
                update: (deltaTime) => this._stateInit(deltaTime),
                exit: () => this._onStateExit('INIT')
            },
            LOADING: {
                enter: () => this._onStateEnter('LOADING'),
                update: (deltaTime) => this._stateLoading(deltaTime),
                exit: () => this._onStateExit('LOADING')
            },
            RUNNING: {
                enter: () => this._onStateEnter('RUNNING'),
                update: (deltaTime) => this._stateRunning(deltaTime),
                exit: () => this._onStateExit('RUNNING')
            },
            PAUSED: {
                enter: () => this._onStateEnter('PAUSED'),
                update: (deltaTime) => this._statePaused(deltaTime),
                exit: () => this._onStateExit('PAUSED')
            },
            COMPLETED: {
                enter: () => this._onStateEnter('COMPLETED'),
                update: (deltaTime) => this._stateCompleted(deltaTime),
                exit: () => this._onStateExit('COMPLETED')
            },
            ERROR: {
                enter: () => this._onStateEnter('ERROR'),
                update: (deltaTime) => this._stateError(deltaTime),
                exit: () => this._onStateExit('ERROR')
            }
        };
        
        // Определение переходов
        this.transitions = {
            INIT: ['LOADING', 'ERROR'],
            LOADING: ['RUNNING', 'ERROR'],
            RUNNING: ['PAUSED', 'COMPLETED', 'ERROR'],
            PAUSED: ['RUNNING', 'ERROR']
        };
    }
    
    /**
     * Переход между состояниями
     * @param {string} newState - Новое состояние
     * @returns {boolean} Успешность перехода
     */
    transitionTo(newState) {
        try {
            if (this.transitions[this.currentState]?.includes(newState)) {
                console.log(\`Переход из \${this.currentState} в \${newState}\`);
                
                // Выход из текущего состояния
                if (this.states[this.currentState]?.exit) {
                    this.states[this.currentState].exit();
                }
                
                // Сохранение старого состояния
                const oldState = this.currentState;
                
                // Установка нового состояния
                this.currentState = newState;
                
                // Вход в новое состояние
                if (this.states[newState]?.enter) {
                    this.states[newState].enter();
                }
                
                // Событие перехода
                this._onTransition(oldState, newState);
                
                return true;
            } else {
                console.warn(\`Недопустимый переход из \${this.currentState} в \${newState}\`);
                return false;
            }
        } catch (error) {
            console.error(\`Ошибка при переходе: \${error.message}\`);
            this.transitionTo('ERROR');
            return false;
        }
    }
    
    /**
     * Обновление сценария
     * @param {number} deltaTime - Время с последнего обновления (в секундах)
     */
    update(deltaTime = 0.016) {
        try {
            this.frameCount++;
            
            if (this.states[this.currentState]?.update) {
                this.states[this.currentState].update(deltaTime);
            }
            
            // Ограничение частоты обновления для демо
            if (this.frameCount % 60 === 0) {
                console.log(\`Сценарий "\${this.name}" обновлен, кадр: \${this.frameCount}\`);
            }
        } catch (error) {
            console.error(\`Ошибка в состоянии \${this.currentState}: \${error.message}\`);
            this.transitionTo('ERROR');
        }
    }
    
    /**
     * Запуск сценария
     */
    start() {
        console.log(\`Запуск сценария: \${this.name}\`);
        if (!this.initialized) {
            this.transitionTo('INIT');
        }
    }
    
    /**
     * Остановка сценария
     */
    stop() {
        console.log(\`Остановка сценария: \${this.name}\`);
        this.transitionTo('COMPLETED');
    }
    
    /**
     * Состояние: Инициализация
     * @private
     */
    _stateInit(deltaTime) {
        console.log('Инициализация сценария...');
        
        // Симуляция инициализации
        setTimeout(() => {
            this.data.initialized = true;
            this.initialized = true;
            this.transitionTo('LOADING');
        }, 100);
    }
    
    /**
     * Состояние: Загрузка
     * @private
     */
    _stateLoading(deltaTime) {
        // Логика загрузки ресурсов
        // В реальном приложении здесь будет загрузка 3D моделей, текстур и т.д.
        
        if (!this.data.loadProgress) {
            this.data.loadProgress = 0;
        }
        
        this.data.loadProgress += deltaTime * 50; // 50% в секунду
        
        if (this.data.loadProgress >= 100) {
            this.data.loadProgress = 100;
            this.data.assetsLoaded = true;
            this.transitionTo('RUNNING');
        }
        
        console.log(\`Загрузка: \${Math.min(100, Math.round(this.data.loadProgress))}%\`);
    }
    
    /**
     * Состояние: Выполнение
     * @private
     */
    _stateRunning(deltaTime) {
        // Основная логика сценария
        // Этот метод должен быть расширен для конкретного сценария
        
        // Пример: простая анимация или взаимодействие
        if (!this.data.runningTime) {
            this.data.runningTime = 0;
        }
        
        this.data.runningTime += deltaTime;
        
        // Автоматический переход через 10 секунд для демо
        if (this.data.runningTime > 10) {
            this.transitionTo('COMPLETED');
        }
    }
    
    /**
     * Состояние: Пауза
     * @private
     */
    _statePaused(deltaTime) {
        console.log('Сценарий на паузе');
    }
    
    /**
     * Состояние: Завершено
     * @private
     */
    _stateCompleted(deltaTime) {
        console.log('Сценарий успешно завершен');
    }
    
    /**
     * Состояние: Ошибка
     * @private
     */
    _stateError(deltaTime) {
        console.error('Произошла ошибка в сценарии');
    }
    
    /**
     * Событие при входе в состояние
     * @private
     */
    _onStateEnter(state) {
        console.log(\`Вход в состояние: \${state}\`);
    }
    
    /**
     * Событие при выходе из состояния
     * @private
     */
    _onStateExit(state) {
        console.log(\`Выход из состояния: \${state}\`);
    }
    
    /**
     * Событие при переходе между состояниями
     * @private
     */
    _onTransition(fromState, toState) {
        console.log(\`Переход: \${fromState} -> \${toState}\`);
    }
    
    /**
     * Установка данных сценария
     * @param {string} key - Ключ
     * @param {*} value - Значение
     */
    setData(key, value) {
        this.data[key] = value;
    }
    
    /**
     * Получение данных сценария
     * @param {string} key - Ключ
     * @returns {*} Значение
     */
    getData(key) {
        return this.data[key];
    }
}

/**
 * Менеджер сценариев
 */
class SceneManager {
    constructor() {
        this.scenes = new Map();
        this.activeScene = null;
        this.lastUpdateTime = performance.now();
        this.running = false;
    }
    
    /**
     * Добавление сценария
     * @param {string} name - Название сценария
     * @param {VRScene} scene - Экземпляр сценария
     */
    addScene(name, scene) {
        this.scenes.set(name, scene);
    }
    
    /**
     * Запуск сценария
     * @param {string} name - Название сценария
     */
    startScene(name) {
        const scene = this.scenes.get(name);
        if (scene) {
            if (this.activeScene) {
                this.activeScene.stop();
            }
            
            this.activeScene = scene;
            scene.start();
            this.startUpdateLoop();
        } else {
            console.error(\`Сценарий "\${name}" не найден\`);
        }
    }
    
    /**
     * Запуск цикла обновления
     */
    startUpdateLoop() {
        if (this.running) return;
        
        this.running = true;
        this.lastUpdateTime = performance.now();
        
        const update = () => {
            if (!this.running) return;
            
            const currentTime = performance.now();
            const deltaTime = (currentTime - this.lastUpdateTime) / 1000; // В секундах
            this.lastUpdateTime = currentTime;
            
            if (this.activeScene) {
                this.activeScene.update(deltaTime);
            }
            
            requestAnimationFrame(update);
        };
        
        requestAnimationFrame(update);
    }
    
    /**
     * Остановка цикла обновления
     */
    stopUpdateLoop() {
        this.running = false;
    }
}

// Пример использования
if (typeof module !== 'undefined' && module.exports) {
    // Для Node.js
    module.exports = { VRScene, SceneManager };
} else {
    // Для браузера
    window.VRScene = VRScene;
    window.SceneManager = SceneManager;
    
    // Пример создания и запуска сценария
    document.addEventListener('DOMContentLoaded', () => {
        console.log('VR/AR Platform - Пример сценария на JavaScript');
        
        const scene = new VRScene('Пример VR сценария');
        const manager = new SceneManager();
        
        manager.addScene('demo', scene);
        manager.startScene('demo');
        
        // Автоматическая остановка через 15 секунд для демо
        setTimeout(() => {
            scene.stop();
            manager.stopUpdateLoop();
            console.log('Демо завершено');
        }, 15000);
    });
}`;
    }
    
    // Получение имени файла
    getFileName(settings) {
        const extensions = {
            'python': 'py',
            'csharp': 'cs',
            'cpp': 'cpp',
            'java': 'java',
            'javascript': 'js'
        };
        
        const ext = extensions[settings.language] || 'txt';
        return `vr_scenario.${ext}`;
    }
    
    // Отображение сгенерированного кода
    renderGeneratedCode() {
        const codeElement = document.getElementById('generatedCode');
        if (!codeElement) return;
        
        codeElement.textContent = this.generatedCode;
        codeElement.className = `language-${this.currentLanguage} hljs`;
        
        // Применяем подсветку синтаксиса
        if (window.hljs) {
            window.hljs.highlightElement(codeElement);
        }
        
        // Обновляем вкладки файлов
        this.updateCodeTabs();
    }
    
    // Обновление вкладок файлов
    updateCodeTabs() {
        const tabsContainer = document.getElementById('codeTabs');
        if (!tabsContainer) return;
        
        tabsContainer.innerHTML = this.generatedFiles.map((file, index) => `
            <button class="code-tab ${index === 0 ? 'active' : ''}" data-index="${index}">
                <i class="fas fa-file-code"></i> ${file.name}
            </button>
        `).join('');
        
        // Обработчики для вкладок
        const tabs = tabsContainer.querySelectorAll('.code-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const index = parseInt(tab.dataset.index);
                if (index >= 0 && index < this.generatedFiles.length) {
                    this.showFile(index);
                }
            });
        });
    }
    
    // Показ файла по индексу
    showFile(index) {
        if (index < 0 || index >= this.generatedFiles.length) return;
        
        const file = this.generatedFiles[index];
        const codeElement = document.getElementById('generatedCode');
        
        if (codeElement) {
            codeElement.textContent = file.content;
            codeElement.className = `language-${file.language} hljs`;
            
            if (window.hljs) {
                window.hljs.highlightElement(codeElement);
            }
        }
    }
    
    // Обновление информации о коде
    updateCodeInfo() {
        const lineCount = this.generatedCode.split('\n').length;
        const fileCount = this.generatedFiles.length;
        
        // Простая оценка сложности
        let complexity = 'Низкая';
        if (lineCount > 500) complexity = 'Высокая';
        else if (lineCount > 200) complexity = 'Средняя';
        
        document.getElementById('lineCount').textContent = lineCount;
        document.getElementById('fileCount').textContent = fileCount;
        document.getElementById('complexity').textContent = complexity;
        document.getElementById('codeStatus').textContent = 'Сгенерирован';
    }
    
    // Копирование всего кода
    async copyAllCode() {
        try {
            await navigator.clipboard.writeText(this.generatedCode);
            VRARPlatform.showNotification('Код скопирован в буфер обмена', 'success');
        } catch (error) {
            console.error('Ошибка копирования:', error);
            VRARPlatform.showNotification('Не удалось скопировать код', 'error');
        }
    }
    
    // Скачивание кода
    downloadCode() {
        if (!this.generatedCode) {
            VRARPlatform.showNotification('Сначала сгенерируйте код', 'warning');
            return;
        }
        
        const blob = new Blob([this.generatedCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        const fileName = this.getFileName({
            language: this.currentLanguage,
            source: this.currentSource
        });
        
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        VRARPlatform.showNotification(`Код сохранен как ${fileName}`, 'success');
    }
    
    // Валидация кода
    async validateCode() {
        try {
            VRARPlatform.showNotification('Валидация кода...', 'info');
            
            // В реальном приложении здесь будет запрос к API
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Простая проверка для демо
            const issues = [];
            
            if (this.generatedCode.length < 100) {
                issues.push('Код слишком короткий');
            }
            
            if (!this.generatedCode.includes('class') && !this.generatedCode.includes('function')) {
                issues.push('Отсутствуют классы или функции');
            }
            
            if (issues.length === 0) {
                VRARPlatform.showNotification('Код прошел валидацию успешно', 'success');
                
                // Показываем предупреждения
                const warningsList = document.getElementById('warningsList');
                if (warningsList) {
                    warningsList.innerHTML = `
                        <p class="no-warnings"><i class="fas fa-check-circle"></i> Нет предупреждений</p>
                    `;
                }
            } else {
                VRARPlatform.showNotification(`Найдены проблемы: ${issues.join(', ')}`, 'warning');
                
                const warningsList = document.getElementById('warningsList');
                if (warningsList) {
                    warningsList.innerHTML = issues.map(issue => `
                        <p class="warning-item"><i class="fas fa-exclamation-triangle"></i> ${issue}</p>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Ошибка валидации:', error);
            VRARPlatform.showNotification('Ошибка при валидации кода', 'error');
        }
    }
    
    // Сохранение в историю
    saveToHistory(settings) {
        const historyItem = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            settings: settings,
            code_preview: this.generatedCode.substring(0, 200) + '...',
            language: this.currentLanguage,
            source: this.currentSource
        };
        
        this.generationHistory.unshift(historyItem);
        
        // Сохраняем только последние 10 элементов
        if (this.generationHistory.length > 10) {
            this.generationHistory = this.generationHistory.slice(0, 10);
        }
        
        localStorage.setItem('codegen_history', JSON.stringify(this.generationHistory));
        this.renderHistory();
    }
    
    // Отображение истории
    renderHistory() {
        const historyContainer = document.getElementById('generationHistory');
        if (!historyContainer) return;
        
        if (this.generationHistory.length === 0) {
            historyContainer.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-history"></i>
                    <p>История генерации пуста</p>
                </div>
            `;
            return;
        }
        
        historyContainer.innerHTML = this.generationHistory.map(item => `
            <div class="history-item">
                <div class="history-info">
                    <h4>${this.getHistoryTitle(item)}</h4>
                    <p>
                        <i class="fas fa-code"></i> ${this.getLanguageName(item.language)} • 
                        <i class="fas fa-project-diagram"></i> ${this.getSourceName(item.source)} • 
                        ${this.formatTimeAgo(item.timestamp)}
                    </p>
                    <p class="code-preview">${item.code_preview}</p>
                </div>
                <div class="history-actions">
                    <button class="btn btn-icon view-history-btn" data-id="${item.id}" title="Просмотр">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-icon regenerate-btn" data-id="${item.id}" title="Повторить">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button class="btn btn-icon download-history-btn" data-id="${item.id}" title="Скачать">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Обработчики для кнопок истории
        historyContainer.querySelectorAll('.view-history-btn').forEach(btn => {
            btn.addEventListener('click', () => this.viewHistoryItem(btn.dataset.id));
        });
        
        historyContainer.querySelectorAll('.regenerate-btn').forEach(btn => {
            btn.addEventListener('click', () => this.regenerateFromHistory(btn.dataset.id));
        });
        
        historyContainer.querySelectorAll('.download-history-btn').forEach(btn => {
            btn.addEventListener('click', () => this.downloadHistoryItem(btn.dataset.id));
        });
    }
    
    // Получение названия для элемента истории
    getHistoryTitle(item) {
        const sourceNames = {
            'scenario': 'Сценарий',
            'visual': 'Визуальный скрипт',
            'template': 'Шаблон',
            'manual': 'Ручная настройка'
        };
        
        return `Сгенерировано из ${sourceNames[item.source] || item.source}`;
    }
    
    // Получение названия языка
    getLanguageName(lang) {
        const names = {
            'python': 'Python',
            'csharp': 'C#',
            'cpp': 'C++',
            'java': 'Java',
            'javascript': 'JavaScript'
        };
        return names[lang] || lang;
    }
    
    // Получение названия источника
    getSourceName(source) {
        const names = {
            'scenario': 'Сценарий',
            'visual': 'Визуальный скрипт',
            'template': 'Шаблон'
        };
        return names[source] || source;
    }
    
    // Форматирование времени (сколько времени прошло)
    formatTimeAgo(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'только что';
        if (diffMins < 60) return `${diffMins} мин назад`;
        if (diffHours < 24) return `${diffHours} ч назад`;
        if (diffDays < 7) return `${diffDays} дн назад`;
        
        return date.toLocaleDateString('ru-RU');
    }
    
    // Просмотр элемента истории
    viewHistoryItem(id) {
        const item = this.generationHistory.find(h => h.id == id);
        if (!item) return;
        
        // В реальном приложении здесь будет загрузка полного кода
        VRARPlatform.showNotification('Просмотр истории в разработке', 'info');
    }
    
    // Регенерация из истории
    regenerateFromHistory(id) {
        const item = this.generationHistory.find(h => h.id == id);
        if (!item) return;
        
        // Установка настроек из истории
        this.currentSource = item.settings.source;
        this.currentLanguage = item.settings.language;
        
        // Обновление UI
        const sourceType = document.getElementById('sourceType');
        if (sourceType) sourceType.value = this.currentSource;
        
        // Обновление языка
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach(opt => {
            opt.classList.remove('active');
            if (opt.dataset.language === this.currentLanguage) {
                opt.classList.add('active');
            }
        });
        
        this.updateSourceVisibility();
        
        // Прокрутка к генерации
        document.querySelector('.generate-section').scrollIntoView({
            behavior: 'smooth'
        });
        
        VRARPlatform.showNotification('Настройки загружены из истории', 'success');
    }
    
    // Скачивание элемента истории
    downloadHistoryItem(id) {
        const item = this.generationHistory.find(h => h.id == id);
        if (!item) return;
        
        // В реальном приложении здесь будет скачивание полного кода
        VRARPlatform.showNotification('Скачивание истории в разработке', 'info');
    }
    
    // Очистка истории
    clearHistory() {
        if (!confirm('Вы уверены, что хотите очистить историю генерации?')) {
            return;
        }
        
        this.generationHistory = [];
        localStorage.removeItem('codegen_history');
        this.renderHistory();
        
        VRARPlatform.showNotification('История очищена', 'success');
    }
}

// Создание экземпляра генератора кода
let codeGenerator;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    codeGenerator = new CodeGenerator();
    
    // Инициализация Highlight.js
    if (window.hljs) {
        window.hljs.highlightAll();
    }
});

// Глобальный экспорт
window.codeGenerator = codeGenerator;