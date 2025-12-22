import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsService } from '../api/projectsService';
import { notificationsService } from '../api/notificationsService';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import './Dashboard.css';

export const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', status: 'PLANNING' });
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [projectsData, notificationsData] = await Promise.all([
        projectsService.getProjects(),
        user?.id ? notificationsService.getUserNotifications(user.id) : []
      ]);

      setProjects(projectsData);
      setNotifications(notificationsData.slice(0, 5));
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      await projectsService.createProject(newProject);
      setShowCreateModal(false);
      setNewProject({ name: '', description: '', status: 'PLANNING' });
      loadDashboardData();
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Ошибка создания проекта');
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationsService.markAsRead(notificationId);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, isRead: true } : n
      ));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
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
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Панель управления</h1>
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            + Создать проект
          </button>
        </div>

        {/* Статистика убрана вместе с аналитикой */}

        <div className="dashboard-content">
          <div className="projects-section">
            <h2>Мои проекты</h2>
            {projects.length === 0 ? (
              <div className="empty-state">
                <p>У вас пока нет проектов</p>
                <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
                  Создать первый проект
                </button>
              </div>
            ) : (
              <div className="projects-grid">
                {projects.map(project => (
                  <div
                    key={project.id}
                    className="project-card"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <div className="project-header">
                      <h3>{project.name}</h3>
                      <span className={`status-badge status-${project.status.toLowerCase()}`}>
                        {project.status}
                      </span>
                    </div>
                    <p className="project-description">{project.description}</p>
                    <div className="project-footer">
                      <span className="project-date">
                        {new Date(project.createdAt).toLocaleDateString('ru-RU')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="notifications-section">
            <h2>Последние уведомления</h2>
            {notifications.length === 0 ? (
              <p className="empty-notifications">Нет новых уведомлений</p>
            ) : (
              <div className="notifications-list">
                {notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`notification-item ${notification.isRead ? 'read' : 'unread'}`}
                    onClick={() => !notification.isRead && handleMarkAsRead(notification.id)}
                  >
                    <div className="notification-icon">
                      {notification.type === 'task_assigned' && '✅'}
                      {notification.type === 'project_created' && '📁'}
                      {notification.type === 'member_added' && '👥'}
                      {notification.type === 'comment_added' && '💬'}
                    </div>
                    <div className="notification-content">
                      <p>{notification.message}</p>
                      <span className="notification-time">
                        {new Date(notification.createdAt).toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button
              className="btn-secondary"
              onClick={() => navigate('/notifications')}
            >
              Все уведомления
            </button>
          </div>
        </div>

        {showCreateModal && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Создать проект</h2>
              <form onSubmit={handleCreateProject}>
                <div className="form-group">
                  <label>Название проекта</label>
                  <input
                    type="text"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    required
                    placeholder="Введите название"
                  />
                </div>
                <div className="form-group">
                  <label>Описание</label>
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    placeholder="Описание проекта"
                    rows="4"
                  />
                </div>
                <div className="form-group">
                  <label>Статус</label>
                  <select
                    value={newProject.status}
                    onChange={(e) => setNewProject({ ...newProject, status: e.target.value })}
                  >
                    <option value="PLANNING">Планирование</option>
                    <option value="ACTIVE">Активный</option>
                    <option value="ON_HOLD">Приостановлен</option>
                    <option value="COMPLETED">Завершен</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
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
