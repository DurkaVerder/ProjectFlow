import { authAPI } from './axios';

export const authService = {
  async register(userData) {
    const response = await authAPI.post('/auth/register', userData);
    return response.data;
  },

  async login(email, password) {
    const response = await authAPI.post('/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  },

  async logout() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await authAPI.post('/auth/logout', { refresh_token: refreshToken }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    localStorage.clear();
  },

  async validateToken() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      const response = await authAPI.get('/auth/validate', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      localStorage.clear();
      return null;
    }
  },

  async searchUsers(name = '') {
    const response = await authAPI.get('/auth/users/search', {
      params: { name }
    });
    return response.data;
  },

  async getUser(userId) {
    const response = await authAPI.get(`/auth/users/${userId}`);
    return response.data;
  },

  async updateUser(userId, userData) {
    const response = await authAPI.put(`/auth/users/${userId}`, userData);
    return response.data;
  },

  async deleteUser(userId) {
    const response = await authAPI.delete(`/auth/users/${userId}`);
    return response.data;
  },

  async getRoles() {
    const response = await authAPI.get('/auth/roles');
    return response.data;
  },

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  }
};
