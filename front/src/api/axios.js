import axios from 'axios';

const API_BASE_URL = 'http://localhost';

// Создаем инстансы для каждого сервиса
export const authAPI = axios.create({
  baseURL: `${API_BASE_URL}:8000`,
});

export const projectsAPI = axios.create({
  baseURL: `${API_BASE_URL}:8001`,
});

export const tasksAPI = axios.create({
  baseURL: `${API_BASE_URL}:8002`,
});

export const notificationsAPI = axios.create({
  baseURL: `${API_BASE_URL}:8003`,
});

export const analyticsAPI = axios.create({
  baseURL: `${API_BASE_URL}:8004`,
});

export const integrationsAPI = axios.create({
  baseURL: `${API_BASE_URL}:8005`,
});

// Интерсептор для добавления токена ко всем запросам
const addAuthToken = (config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

// Добавляем интерсептор ко всем API
[projectsAPI, tasksAPI, notificationsAPI, analyticsAPI, integrationsAPI].forEach(api => {
  api.interceptors.request.use(addAuthToken);
  
  // Интерсептор для обработки ошибок авторизации
  api.interceptors.response.use(
    response => response,
    async error => {
      if (error.response?.status === 401) {
        // Пробуем обновить токен
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try {
            const response = await authAPI.post('/auth/refresh', {
              refresh_token: refreshToken
            });
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
            
            // Повторяем оригинальный запрос
            error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
            return api.request(error.config);
          } catch (refreshError) {
            // Если обновление токена не удалось, очищаем хранилище и редиректим
            localStorage.clear();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        } else {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );
});

export default {
  authAPI,
  projectsAPI,
  tasksAPI,
  notificationsAPI,
  analyticsAPI,
  integrationsAPI,
};
