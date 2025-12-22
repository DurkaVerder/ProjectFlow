import { tasksAPI } from './axios';

export const tasksService = {
  async createTask(taskData) {
    const response = await tasksAPI.post('/tasks', taskData);
    return response.data;
  },

  async getTasks(projectId = null) {
    const url = projectId ? `/tasks?project=${projectId}` : '/tasks';
    const response = await tasksAPI.get(url);
    return response.data;
  },

  async getTask(taskId) {
    const response = await tasksAPI.get(`/tasks/${taskId}`);
    return response.data;
  },

  async updateTask(taskId, taskData) {
    const response = await tasksAPI.put(`/tasks/${taskId}`, taskData);
    return response.data;
  },

  async deleteTask(taskId) {
    const response = await tasksAPI.delete(`/tasks/${taskId}`);
    return response.data;
  },

  async getComments(taskId) {
    const response = await tasksAPI.get(`/tasks/${taskId}/comments`);
    return response.data;
  },

  async addComment(taskId, content) {
    const response = await tasksAPI.post(`/tasks/${taskId}/comments`, { content });
    return response.data;
  }
};
