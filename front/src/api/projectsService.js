import { projectsAPI } from './axios';

export const projectsService = {
  async createProject(projectData) {
    const response = await projectsAPI.post('/projects', projectData);
    return response.data;
  },

  async getProjects() {
    const response = await projectsAPI.get('/projects');
    return response.data;
  },

  async getProject(projectId) {
    const response = await projectsAPI.get(`/projects/${projectId}`);
    return response.data;
  },

  async updateProject(projectId, projectData) {
    const response = await projectsAPI.put(`/projects/${projectId}`, projectData);
    return response.data;
  },

  async deleteProject(projectId) {
    const response = await projectsAPI.delete(`/projects/${projectId}`);
    return response.data;
  },

  async addMember(projectId, userId) {
    const response = await projectsAPI.post(`/projects/${projectId}/members`, { userId });
    return response.data;
  },

  async getMembers(projectId) {
    const response = await projectsAPI.get(`/projects/${projectId}/members`);
    return response.data;
  },

  async removeMember(projectId, userId) {
    const response = await projectsAPI.delete(`/projects/${projectId}/members/${userId}`);
    return response.data;
  }
};
