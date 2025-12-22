import { notificationsAPI } from './axios';

export const notificationsService = {
  async getUserNotifications(userId) {
    const response = await notificationsAPI.get(`/notifications/user/${userId}`);
    return response.data;
  },

  async markAsRead(notificationId) {
    const response = await notificationsAPI.put(`/notifications/${notificationId}/read`);
    return response.data;
  }
};
