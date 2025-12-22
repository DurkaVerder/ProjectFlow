import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsService } from '../api/projectsService';
import { tasksService } from '../api/tasksService';
import { authService } from '../api/authService';
import { Navbar } from '../components/Navbar';
import './ProjectDetail.css';

export const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    status: 'TODO',
    priority: 'MEDIUM',
    assigneeId: null,
    startDate: null,
    dueDate: null
  });
  const [newMemberId, setNewMemberId] = useState('');

  useEffect(() => {
    loadProjectData();
  }, [id]);

  useEffect(() => {
    if (showTaskModal) {
      loadUsers();
    }
  }, [showTaskModal]);

  useEffect(() => {
    if (userSearch) {
      const timer = setTimeout(() => {
        loadUsers(userSearch);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      loadUsers();
    }
  }, [userSearch]);

  const loadUsers = async (search = '') => {
    try {
      const usersData = await authService.searchUsers(search);
      setUsers(usersData);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const loadProjectData = async () => {
    try {
      const [projectData, tasksData, membersData] = await Promise.all([
        projectsService.getProject(id),
        tasksService.getTasks(id),
        projectsService.getMembers(id)
      ]);
      setProject(projectData);
      setTasks(tasksData);
      setMembers(membersData);
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      const taskData = {
        ...newTask,
        projectId: id,
        assigneeId: newTask.assigneeId || null,
        startDate: newTask.startDate || null,
        dueDate: newTask.dueDate || null
      };
      await tasksService.createTask(taskData);
      setShowTaskModal(false);
      setNewTask({
        title: '',
        description: '',
        status: 'TODO',
        priority: 'MEDIUM',
        assigneeId: null,
        startDate: null,
        dueDate: null
      });
      setUserSearch('');
      loadProjectData();
    } catch (error) {
      console.error('Failed to create task:', error);
      alert('Ошибка создания задачи');
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    try {
      await projectsService.addMember(id, newMemberId);
      setShowMemberModal(false);
      setNewMemberId('');
      loadProjectData();
    } catch (error) {
      console.error('Failed to add member:', error);
      alert('Ошибка добавления участника');
    }
  };

  const handleDeleteProject = async () => {
    if (window.confirm('Вы уверены, что хотите удалить проект?')) {
      try {
        await projectsService.deleteProject(id);
        navigate('/projects');
      } catch (error) {
        console.error('Failed to delete project:', error);
        alert('Ошибка удаления проекта');
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

  if (!project) {
    return (
      <>
        <Navbar />
        <div className="error-container">Проект не найден</div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="project-detail-container">
        <div className="project-header">
          <div>
            <h1>{project.name}</h1>
            <p className="project-description">{project.description}</p>
          </div>
          <div className="project-actions">
            <span className={`status-badge status-${project.status.toLowerCase()}`}>
              {project.status}
            </span>
            <button className="btn-danger" onClick={handleDeleteProject}>
              Удалить проект
            </button>
          </div>
        </div>

        <div className="project-content">
          <div className="tasks-section">
            <div className="section-header">
              <h2>Задачи ({tasks.length})</h2>
              <button className="btn-primary" onClick={() => setShowTaskModal(true)}>
                + Добавить задачу
              </button>
            </div>
            <div className="tasks-list">
              {tasks.length === 0 ? (
                <p className="empty-message">Нет задач в этом проекте</p>
              ) : (
                tasks.map(task => (
                  <div
                    key={task.id}
                    className="task-item"
                    onClick={() => navigate(`/tasks/${task.id}`)}
                  >
                    <div className="task-info">
                      <h3>{task.title}</h3>
                      <p>{task.description}</p>
                    </div>
                    <div className="task-meta">
                      <span className={`priority-badge priority-${task.priority.toLowerCase()}`}>
                        {task.priority}
                      </span>
                      <span className={`status-badge status-${task.status.toLowerCase()}`}>
                        {task.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="members-section">
            <div className="section-header">
              <h2>Участники ({members.length})</h2>
              <button className="btn-secondary" onClick={() => setShowMemberModal(true)}>
                + Добавить
              </button>
            </div>
            <div className="members-list">
              {members.map(member => (
                <div key={member.id} className="member-item">
                  <div className="member-avatar">
                    {member.userName?.charAt(0).toUpperCase() || '?'}
                  </div>
                  <div className="member-info">
                    <span className="member-name">{member.userName || 'Неизвестно'}</span>
                    <span className="member-date">
                      Добавлен {new Date(member.addedAt).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {showTaskModal && (
          <div className="modal-overlay" onClick={() => setShowTaskModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Создать задачу</h2>
              <form onSubmit={handleCreateTask}>
                <div className="form-group">
                  <label>Название</label>
                  <input
                    type="text"
                    value={newTask.title}
                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Описание</label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    rows="4"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Статус</label>
                    <select
                      value={newTask.status}
                      onChange={(e) => setNewTask({ ...newTask, status: e.target.value })}
                    >
                      <option value="TODO">К выполнению</option>
                      <option value="IN_PROGRESS">В работе</option>
                      <option value="DONE">Выполнено</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Приоритет</label>
                    <select
                      value={newTask.priority}
                      onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                    >
                      <option value="LOW">Низкий</option>
                      <option value="MEDIUM">Средний</option>
                      <option value="HIGH">Высокий</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label>Исполнитель (опционально)</label>
                  <input
                    type="text"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    placeholder="Поиск по имени..."
                  />
                  {users.length > 0 && (
                    <div className="user-dropdown">
                      {users.map(user => (
                        <div
                          key={user.id}
                          className={`user-option ${newTask.assigneeId === user.id ? 'selected' : ''}`}
                          onClick={() => {
                            setNewTask({ ...newTask, assigneeId: user.id });
                            setUserSearch(user.name);
                          }}
                        >
                          <div>{user.name}</div>
                          <div className="user-email">{user.email}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Дата начала (опционально)</label>
                    <input
                      type="datetime-local"
                      value={newTask.startDate || ''}
                      onChange={(e) => setNewTask({ ...newTask, startDate: e.target.value || null })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Дата завершения (опционально)</label>
                    <input
                      type="datetime-local"
                      value={newTask.dueDate || ''}
                      onChange={(e) => setNewTask({ ...newTask, dueDate: e.target.value || null })}
                    />
                  </div>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowTaskModal(false)}>
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

        {showMemberModal && (
          <div className="modal-overlay" onClick={() => setShowMemberModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Добавить участника</h2>
              <form onSubmit={handleAddMember}>
                <div className="form-group">
                  <label>ID пользователя</label>
                  <input
                    type="text"
                    value={newMemberId}
                    onChange={(e) => setNewMemberId(e.target.value)}
                    required
                    placeholder="UUID пользователя"
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowMemberModal(false)}>
                    Отмена
                  </button>
                  <button type="submit" className="btn-primary">
                    Добавить
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
