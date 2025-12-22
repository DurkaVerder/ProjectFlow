import React, { useState, useEffect } from 'react';
import { notificationsService } from '../api/notificationsService';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import './Notifications.css';

export const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    if (!user?.id) return;
    
    try {
      const data = await notificationsService.getUserNotifications(user.id);
      setNotifications(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationsService.markAsRead(notificationId);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, isRead: true } : n
      ));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.isRead);
    
    try {
      await Promise.all(
        unreadNotifications.map(n => notificationsService.markAsRead(n.id))
      );
      setNotifications(notifications.map(n => ({ ...n, isRead: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
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
          <h1>Уведомления</h1>
          {notifications.some(n => !n.isRead) && (
            <button className="btn-secondary" onClick={handleMarkAllAsRead}>
              Отметить все прочитанными
            </button>
          )}
        </div>

        <div className="notifications-container">
          {notifications.length === 0 ? (
            <div className="empty-state">
              <p>У вас пока нет уведомлений</p>
            </div>
          ) : (
            <div className="notifications-list-page">
              {notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`notification-card ${notification.isRead ? 'read' : 'unread'}`}
                  onClick={() => !notification.isRead && handleMarkAsRead(notification.id)}
                >
                  <div className="notification-icon-large">
                    {notification.type === 'task_assigned' && '✅'}
                    {notification.type === 'project_created' && '📁'}
                    {notification.type === 'member_added' && '👥'}
                    {notification.type === 'comment_added' && '💬'}
                    {!['task_assigned', 'project_created', 'member_added', 'comment_added'].includes(notification.type) && '🔔'}
                  </div>
                  <div className="notification-body">
                    <div className="notification-header">
                      <span className="notification-type">{notification.type}</span>
                      {!notification.isRead && <span className="unread-indicator">Новое</span>}
                    </div>
                    <p className="notification-message">{notification.message}</p>
                    <span className="notification-timestamp">
                      {new Date(notification.createdAt).toLocaleString('ru-RU')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
};
