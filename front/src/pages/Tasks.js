import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { tasksService } from '../api/tasksService';
import { Navbar } from '../components/Navbar';
import './Tasks.css';

export const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const data = await tasksService.getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    return task.status === filter;
  });

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
          <h1>Все задачи</h1>
          <div className="filter-buttons">
            <button
              className={filter === 'all' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilter('all')}
            >
              Все ({tasks.length})
            </button>
            <button
              className={filter === 'TODO' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilter('TODO')}
            >
              К выполнению ({tasks.filter(t => t.status === 'TODO').length})
            </button>
            <button
              className={filter === 'IN_PROGRESS' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilter('IN_PROGRESS')}
            >
              В работе ({tasks.filter(t => t.status === 'IN_PROGRESS').length})
            </button>
            <button
              className={filter === 'DONE' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilter('DONE')}
            >
              Выполнено ({tasks.filter(t => t.status === 'DONE').length})
            </button>
          </div>
        </div>

        <div className="tasks-list">
          {filteredTasks.length === 0 ? (
            <div className="empty-state">
              <p>Нет задач с выбранным фильтром</p>
            </div>
          ) : (
            filteredTasks.map(task => (
              <div
                key={task.id}
                className="task-card"
                onClick={() => navigate(`/tasks/${task.id}`)}
              >
                <div className="task-header">
                  <h3>{task.title}</h3>
                  <div className="task-badges">
                    <span className={`priority-badge priority-${task.priority.toLowerCase()}`}>
                      {task.priority}
                    </span>
                    <span className={`status-badge status-${task.status.toLowerCase()}`}>
                      {task.status}
                    </span>
                  </div>
                </div>
                <p className="task-description">{task.description}</p>
                <div className="task-meta">
                  <span>📁 Проект: {task.projectId}</span>
                  {task.dueDate && (
                    <span>📅 {new Date(task.dueDate).toLocaleDateString('ru-RU')}</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};
