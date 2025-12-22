import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/dashboard" className="navbar-logo">
          📊 ProjectFlow
        </Link>
        <div className="navbar-menu">
          <Link to="/dashboard" className="navbar-link">Панель</Link>
          <Link to="/projects" className="navbar-link">Проекты</Link>
          <Link to="/tasks" className="navbar-link">Задачи</Link>
          <Link to="/analytics" className="navbar-link">Аналитика</Link>
          <Link to="/integrations" className="navbar-link">Интеграции</Link>
          <Link to="/notifications" className="navbar-link">
            🔔 Уведомления
          </Link>
          <div className="navbar-user">
            <span className="user-name">{user?.name || 'Пользователь'}</span>
            <button onClick={handleLogout} className="btn-logout">
              Выйти
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
