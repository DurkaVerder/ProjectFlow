import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tasksService } from '../api/tasksService';
import { authService } from '../api/authService';
import { Navbar } from '../components/Navbar';
import './TaskDetail.css';

export const TaskDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [assignee, setAssignee] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentAuthors, setCommentAuthors] = useState({});
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTask, setEditedTask] = useState({});
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  // Загрузка пользователей для выбора исполнителя
  useEffect(() => {
    if (isEditing) {
      loadUsers();
    }
  }, [isEditing]);

  useEffect(() => {
    if (isEditing) {
      if (userSearch) {
        const timer = setTimeout(() => {
          loadUsers(userSearch);
        }, 300);
        return () => clearTimeout(timer);
      } else {
        loadUsers();
      }
    }
  }, [userSearch, isEditing]);

  const loadUsers = async (search = '') => {
    try {
      const usersData = await authService.searchUsers(search);
      setUsers(usersData);
    } catch (error) {
      // ignore
    }
  };

  useEffect(() => {
    loadTask();
  }, [id]);

  const loadTask = async () => {
    try {
      const taskData = await tasksService.getTask(id);
      setTask(taskData);
      setEditedTask(taskData);
      
      if (taskData.assigneeId) {
        try {
          const userData = await authService.getUser(taskData.assigneeId);
          setAssignee(userData);
        } catch (error) {
          console.error('Failed to load assignee:', error);
        }
      }

      // Загрузка комментариев
      try {
        const commentsData = await tasksService.getComments(id);
        setComments(commentsData);
        
        // Загрузка авторов комментариев
        const authors = {};
        for (const comment of commentsData) {
          if (!authors[comment.authorId]) {
            try {
              const userData = await authService.getUser(comment.authorId);
              authors[comment.authorId] = userData.name;
            } catch (error) {
              console.error('Failed to load comment author:', error);
              authors[comment.authorId] = 'Неизвестный пользователь';
            }
          }
        }
        setCommentAuthors(authors);
      } catch (error) {
        console.error('Failed to load comments:', error);
      }
    } catch (error) {
      console.error('Failed to load task:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        title: editedTask.title,
        description: editedTask.description,
        status: editedTask.status,
        priority: editedTask.priority,
        assigneeId: editedTask.assigneeId || null,
        startDate: editedTask.startDate || null,
        dueDate: editedTask.dueDate || null
      };
      await tasksService.updateTask(id, updateData);
      setIsEditing(false);
      loadTask();
    } catch (error) {
      console.error('Failed to update task:', error);
      alert('Ошибка обновления задачи');
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Вы уверены, что хотите удалить задачу?')) {
      try {
        await tasksService.deleteTask(id);
        navigate('/tasks');
      } catch (error) {
        console.error('Failed to delete task:', error);
        alert('Ошибка удаления задачи');
      }
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await tasksService.addComment(id, newComment);
      setNewComment('');
      // Перезагрузка комментариев с авторами
      const commentsData = await tasksService.getComments(id);
      setComments(commentsData);
      
      // Загрузка новых авторов
      const authors = { ...commentAuthors };
      for (const comment of commentsData) {
        if (!authors[comment.authorId]) {
          try {
            const userData = await authService.getUser(comment.authorId);
            authors[comment.authorId] = userData.name;
          } catch (error) {
            console.error('Failed to load comment author:', error);
            authors[comment.authorId] = 'Неизвестный пользователь';
          }
        }
      }
      setCommentAuthors(authors);
    } catch (error) {
      console.error('Failed to add comment:', error);
      alert('Ошибка добавления комментария');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Не указано';
    return new Date(dateString).toLocaleString('ru-RU');
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="loading-container">Загрузка...</div>
      </>
    );
  }

  if (!task) {
    return (
      <>
        <Navbar />
        <div className="error-container">Задача не найдена</div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="task-detail-container">
        <div className="task-header">
          <button className="btn-back" onClick={() => navigate(-1)}>
            ← Назад
          </button>
          <div className="task-actions">
            {!isEditing ? (
              <>
                <button className="btn-edit" onClick={() => setIsEditing(true)}>
                  Редактировать
                </button>
                <button className="btn-danger" onClick={handleDelete}>
                  Удалить
                </button>
              </>
            ) : (
              <button className="btn-secondary" onClick={() => setIsEditing(false)}>
                Отмена
              </button>
            )}
          </div>
        </div>

        {!isEditing ? (
          <div className="task-content">
            <div className="task-main">
              <h1>{task.title}</h1>
              <p className="task-description">{task.description}</p>

              <div className="task-meta-grid">
                <div className="meta-item">
                  <span className="meta-label">Статус:</span>
                  <span className={`status-badge status-${task.status.toLowerCase()}`}>
                    {task.status === 'TODO' ? 'К выполнению' : 
                     task.status === 'IN_PROGRESS' ? 'В работе' : 'Выполнено'}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Приоритет:</span>
                  <span className={`priority-badge priority-${task.priority.toLowerCase()}`}>
                    {task.priority === 'LOW' ? 'Низкий' : 
                     task.priority === 'MEDIUM' ? 'Средний' : 'Высокий'}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Исполнитель:</span>
                  <span>{assignee ? assignee.name : 'Не назначен'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Создано:</span>
                  <span>{formatDate(task.createdAt)}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Начало:</span>
                  <span>{formatDate(task.startDate)}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Завершение:</span>
                  <span>{formatDate(task.dueDate)}</span>
                </div>
              </div>

              <div className="task-comments">
                <h2>Комментарии ({comments.length})</h2>
                <form onSubmit={handleAddComment} className="comment-form">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Добавить комментарий..."
                    rows="3"
                    required
                  />
                  <button type="submit" className="btn-primary">
                    Добавить комментарий
                  </button>
                </form>
                <div className="comments-list">
                  {comments.length === 0 ? (
                    <p className="empty-message">Нет комментариев</p>
                  ) : (
                    comments.map(comment => (
                      <div key={comment.id} className="comment-item">
                        <div className="comment-header">
                          <span className="comment-author">
                            {commentAuthors[comment.authorId] || 'Загрузка...'}
                          </span>
                          <span className="comment-date">
                            {formatDate(comment.createdAt)}
                          </span>
                        </div>
                        <div className="comment-content">{comment.content}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="task-edit-form">
            <form onSubmit={handleUpdate}>
              <div className="form-group">
                <label>Название</label>
                <input
                  type="text"
                  value={editedTask.title}
                  onChange={(e) => setEditedTask({ ...editedTask, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea
                  value={editedTask.description}
                  onChange={(e) => setEditedTask({ ...editedTask, description: e.target.value })}
                  rows="6"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Исполнитель (поиск по имени)</label>
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
                          className={`user-option ${editedTask.assigneeId === user.id ? 'selected' : ''}`}
                          onClick={() => {
                            setEditedTask({ ...editedTask, assigneeId: user.id });
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
                <div className="form-group">
                  <label>Статус</label>
                  <select
                    value={editedTask.status}
                    onChange={(e) => setEditedTask({ ...editedTask, status: e.target.value })}
                  >
                    <option value="TODO">К выполнению</option>
                    <option value="IN_PROGRESS">В работе</option>
                    <option value="DONE">Выполнено</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Приоритет</label>
                  <select
                    value={editedTask.priority}
                    onChange={(e) => setEditedTask({ ...editedTask, priority: e.target.value })}
                  >
                    <option value="LOW">Низкий</option>
                    <option value="MEDIUM">Средний</option>
                    <option value="HIGH">Высокий</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Дата начала</label>
                  <input
                    type="datetime-local"
                    value={editedTask.startDate ? new Date(editedTask.startDate).toISOString().slice(0, 16) : ''}
                    onChange={(e) => setEditedTask({ ...editedTask, startDate: e.target.value || null })}
                  />
                </div>
                <div className="form-group">
                  <label>Дата завершения</label>
                  <input
                    type="datetime-local"
                    value={editedTask.dueDate ? new Date(editedTask.dueDate).toISOString().slice(0, 16) : ''}
                    onChange={(e) => setEditedTask({ ...editedTask, dueDate: e.target.value || null })}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary">
                  Сохранить изменения
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </>
  );
};
