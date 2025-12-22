import React, { useState, useEffect } from 'react';
import { integrationsService } from '../api/integrationsService';
import { projectsService } from '../api/projectsService';
import { Navbar } from '../components/Navbar';
import './Integrations.css';

export const Integrations = () => {
  const [integrations, setIntegrations] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [integrationType, setIntegrationType] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [config, setConfig] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [integrationsData, projectsData] = await Promise.all([
        integrationsService.getIntegrations(),
        projectsService.getProjects()
      ]);
      setIntegrations(integrationsData);
      setProjects(projectsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectTelegram = async () => {
    try {
      const result = await integrationsService.connectTelegram();
      alert(`Откройте ссылку для подключения: ${result.deep_link}`);
      window.open(result.deep_link, '_blank');
      
      // Проверяем статус подключения
      const checkStatus = setInterval(async () => {
        const status = await integrationsService.checkTelegramStatus(result.connection_token);
        if (status.connected) {
          clearInterval(checkStatus);
          alert('Telegram успешно подключен! Chat ID: ' + status.chat_id);
          // Теперь можно создать интеграцию с этим chat_id
        }
      }, 3000);

      // Останавливаем проверку через 2 минуты
      setTimeout(() => clearInterval(checkStatus), 120000);
    } catch (error) {
      console.error('Failed to connect Telegram:', error);
      alert('Ошибка подключения Telegram');
    }
  };

  const handleCreateIntegration = async (e) => {
    e.preventDefault();
    try {
      await integrationsService.createIntegration({
        projectId: selectedProjectId,
        integrationType,
        config
      });
      setShowModal(false);
      setIntegrationType('');
      setSelectedProjectId('');
      setConfig({});
      loadData();
    } catch (error) {
      console.error('Failed to create integration:', error);
      alert('Ошибка создания интеграции');
    }
  };

  const handleDeleteIntegration = async (id) => {
    if (window.confirm('Удалить интеграцию?')) {
      try {
        await integrationsService.deleteIntegration(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete integration:', error);
        alert('Ошибка удаления интеграции');
      }
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="loading-container">Загрузка...</div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Интеграции</h1>
          <div className="header-actions">
            <button className="btn-secondary" onClick={handleConnectTelegram}>
              🤖 Подключить Telegram
            </button>
            <button className="btn-primary" onClick={() => setShowModal(true)}>
              + Добавить интеграцию
            </button>
          </div>
        </div>

        <div className="integrations-grid">
          {integrations.length === 0 ? (
            <div className="empty-state">
              <p>У вас пока нет интеграций</p>
              <button className="btn-primary" onClick={() => setShowModal(true)}>
                Добавить первую интеграцию
              </button>
            </div>
          ) : (
            integrations.map(integration => (
              <div key={integration.id} className="integration-card">
                <div className="integration-header">
                  <div className="integration-icon">
                    {integration.integrationType === 'email' && '📧'}
                    {integration.integrationType === 'telegram' && '💬'}
                    {integration.integrationType === 'github' && '🐙'}
                  </div>
                  <h3>{integration.integrationType.toUpperCase()}</h3>
                  <span className={`status-indicator ${integration.isActive ? 'active' : 'inactive'}`} />
                </div>
                <div className="integration-body">
                  <p><strong>Проект ID:</strong> {integration.projectId}</p>
                  <div className="config-preview">
                    <strong>Конфигурация:</strong>
                    <pre>{JSON.stringify(integration.config, null, 2)}</pre>
                  </div>
                </div>
                <div className="integration-footer">
                  <span className="integration-date">
                    {new Date(integration.createdAt).toLocaleDateString('ru-RU')}
                  </span>
                  <button
                    className="btn-danger-small"
                    onClick={() => handleDeleteIntegration(integration.id)}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Создать интеграцию</h2>
              <form onSubmit={handleCreateIntegration}>
                <div className="form-group">
                  <label>Тип интеграции</label>
                  <select
                    value={integrationType}
                    onChange={(e) => setIntegrationType(e.target.value)}
                    required
                  >
                    <option value="">Выберите тип</option>
                    <option value="email">Email</option>
                    <option value="telegram">Telegram</option>
                    <option value="github">GitHub</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Проект</label>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    required
                  >
                    <option value="">Выберите проект</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Конфигурация (JSON)</label>
                  <textarea
                    value={JSON.stringify(config, null, 2)}
                    onChange={(e) => {
                      try {
                        setConfig(JSON.parse(e.target.value));
                      } catch (err) {
                        // Игнорируем ошибки парсинга при вводе
                      }
                    }}
                    rows="6"
                    placeholder='{"email": "test@example.com"} или {"chat_id": "123456"}'
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                    Отмена
                  </button>
                  <button type="submit" className="btn-primary">
                    Создать
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
