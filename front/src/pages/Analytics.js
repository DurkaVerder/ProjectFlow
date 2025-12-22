import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api/analyticsService';
import { Navbar } from '../components/Navbar';
import './Analytics.css';

export const Analytics = () => {
  const [projectStats, setProjectStats] = useState(null);
  const [taskStats, setTaskStats] = useState(null);
  const [projectEvents, setProjectEvents] = useState([]);
  const [taskEvents, setTaskEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [pStats, tStats, pEvents, tEvents] = await Promise.all([
        analyticsService.getProjectStats(),
        analyticsService.getTaskStats(),
        analyticsService.getProjectEvents(20),
        analyticsService.getTaskEvents(20)
      ]);
      setProjectStats(pStats);
      setTaskStats(tStats);
      setProjectEvents(pEvents);
      setTaskEvents(tEvents);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
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
        <h1>Аналитика</h1>

        <div className="stats-grid">
          <div className="stat-card">
            <h3>📁 Статистика проектов</h3>
            <div className="stat-list">
              <div className="stat-item">
                <span>Всего проектов:</span>
                <strong>{projectStats?.totalProjects || 0}</strong>
              </div>
              <div className="stat-item">
                <span>Участников:</span>
                <strong>{projectStats?.totalMembers || 0}</strong>
              </div>
              <div className="stat-item">
                <span>За неделю:</span>
                <strong className="text-success">+{projectStats?.projectsThisWeek || 0}</strong>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <h3>✅ Статистика задач</h3>
            <div className="stat-list">
              <div className="stat-item">
                <span>Всего задач:</span>
                <strong>{taskStats?.totalTasks || 0}</strong>
              </div>
              <div className="stat-item">
                <span>Назначено:</span>
                <strong>{taskStats?.assignedTasks || 0}</strong>
              </div>
              <div className="stat-item">
                <span>За неделю:</span>
                <strong className="text-success">+{taskStats?.tasksThisWeek || 0}</strong>
              </div>
              <div className="stat-item">
                <span>Комментариев (неделя):</span>
                <strong>{taskStats?.commentsThisWeek || 0}</strong>
              </div>
            </div>
          </div>
        </div>

        <div className="events-container">
          <div className="events-section">
            <h2>📊 События проектов</h2>
            <div className="events-list">
              {projectEvents.length === 0 ? (
                <p className="empty-message">Нет событий</p>
              ) : (
                projectEvents.map(event => (
                  <div key={event.id} className="event-item">
                    <div className="event-icon">📁</div>
                    <div className="event-content">
                      <strong>{event.eventType}</strong>
                      <p>Проект ID: {event.projectId}</p>
                      <span className="event-time">
                        {new Date(event.createdAt).toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="events-section">
            <h2>✅ События задач</h2>
            <div className="events-list">
              {taskEvents.length === 0 ? (
                <p className="empty-message">Нет событий</p>
              ) : (
                taskEvents.map(event => (
                  <div key={event.id} className="event-item">
                    <div className="event-icon">✅</div>
                    <div className="event-content">
                      <strong>{event.eventType}</strong>
                      <p>Задача ID: {event.taskId}</p>
                      <span className="event-time">
                        {new Date(event.createdAt).toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
