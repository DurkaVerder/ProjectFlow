import { integrationsAPI } from './axios';

export const integrationsService = {
  // CRUD интеграций
  async createIntegration(integrationData) {
    const response = await integrationsAPI.post('/integrations', integrationData);
    return response.data;
  },

  async getIntegrations() {
    const response = await integrationsAPI.get('/integrations');
    return response.data;
  },

  async getIntegration(integrationId) {
    const response = await integrationsAPI.get(`/integrations/${integrationId}`);
    return response.data;
  },

  async updateIntegration(integrationId, integrationData) {
    const response = await integrationsAPI.put(`/integrations/${integrationId}`, integrationData);
    return response.data;
  },

  async deleteIntegration(integrationId) {
    const response = await integrationsAPI.delete(`/integrations/${integrationId}`);
    return response.data;
  },

  async getIntegrationLogs(integrationId, limit = 50) {
    const response = await integrationsAPI.get(`/integrations/${integrationId}/logs?limit=${limit}`);
    return response.data;
  },

  // Email
  async sendEmail(to, subject, body) {
    const response = await integrationsAPI.post('/integrations/email/send', { to, subject, body });
    return response.data;
  },

  // Telegram
  async connectTelegram() {
    const response = await integrationsAPI.post('/integrations/telegram/connect');
    return response.data;
  },

  async checkTelegramStatus(connectionToken) {
    const response = await integrationsAPI.get(`/integrations/telegram/status/${connectionToken}`);
    return response.data;
  },

  async sendTelegram(chatId, message) {
    const response = await integrationsAPI.post('/integrations/telegram/send', { chatId, message });
    return response.data;
  },

  // GitHub
  async addGitHubRepository(repoData) {
    const response = await integrationsAPI.post('/integrations/github/repositories', repoData);
    return response.data;
  },

  async getGitHubRepositories(projectId) {
    const response = await integrationsAPI.get(`/integrations/github/repositories/${projectId}`);
    return response.data;
  },

  async createGitHubIssue(issueData) {
    const response = await integrationsAPI.post('/integrations/github/issues', issueData);
    return response.data;
  },

  async getGitHubIssues(repoOwner, repoName, accessToken) {
    const response = await integrationsAPI.get(`/integrations/github/issues/${repoOwner}/${repoName}?access_token=${accessToken}`);
    return response.data;
  }
};
