import { analyticsAPI } from './axios';

export const analyticsService = {
  async getProjectStats() {
    const response = await analyticsAPI.get('/analytics/projects/stats');
    return response.data;
  },

  async getTaskStats() {
    const response = await analyticsAPI.get('/analytics/tasks/stats');
    return response.data;
  },

  async getUserActivity(userId) {
    const response = await analyticsAPI.get(`/analytics/user/${userId}/activity`);
    return response.data;
  },

  async getProjectEvents(limit = 50) {
    const response = await analyticsAPI.get(`/analytics/projects/events?limit=${limit}`);
    return response.data;
  },

  async getTaskEvents(limit = 50) {
    const response = await analyticsAPI.get(`/analytics/tasks/events?limit=${limit}`);
    return response.data;
  },

  async getProjectActivity(projectId) {
    const response = await analyticsAPI.get(`/analytics/projects/${projectId}/activity`);
    return response.data;
  },

  async getTaskActivity(taskId) {
    const response = await analyticsAPI.get(`/analytics/tasks/${taskId}/activity`);
    return response.data;
  }
};
