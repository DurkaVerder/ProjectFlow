import React, { useState, useEffect } from 'react';
import { integrationsService } from '../api/integrationsService';
import { Navbar } from '../components/Navbar';
import './Integrations.css';

export const Integrations = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await integrationsService.getTelegramStatus();
      setStatus(res);
    } catch (e) {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectTelegram = async () => {
    setConnecting(true);
    try {
      const result = await integrationsService.connectTelegram();
      window.open(result.deep_link, '_blank');
      alert('Откройте Telegram и нажмите START в боте. После этого обновите страницу.');
    } catch (error) {
      alert('Ошибка подключения Telegram');
    } finally {
      setConnecting(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Интеграция с Telegram</h1>
        </div>
        <div className="telegram-integration-block">
          {loading ? (
            <div className="loading-container">Загрузка...</div>
          ) : status && status.connected ? (
            <div className="tg-status-connected">
              <span>✅ Telegram подключён!</span>
              <div className="tg-chat-id">Chat ID: {status.chat_id}</div>
            </div>
          ) : (
            <button className="btn-primary" onClick={handleConnectTelegram} disabled={connecting}>
              {connecting ? 'Ожидание...' : 'Подключить Telegram'}
            </button>
          )}
        </div>
      </div>
    </>
  );
};
