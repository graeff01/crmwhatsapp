import React, { useState, useEffect } from 'react';
import api from '../api';
import '../styles/components/AlertsPanel.css';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, []);

  const loadAlerts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/alerts', {
        credentials: 'include'
      });
      const data = await response.json();
      setAlerts(data.alerts);
      setStats(data.stats);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar alertas:', error);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      await fetch(`http://localhost:5000/api/alerts/${alertId}/resolve`, {
        method: 'POST',
        credentials: 'include'
      });
      loadAlerts();
    } catch (error) {
      console.error('Erro ao resolver alerta:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ef4444',
      danger: '#f59e0b',
      warning: '#eab308'
    };
    return colors[severity] || '#6b7280';
  };

  const getSeverityEmoji = (severity) => {
    const emojis = {
      critical: '🚨',
      danger: '⚠️',
      warning: '⚡'
    };
    return emojis[severity] || '📢';
  };

  const getAlertIcon = (alertType) => {
    const icons = {
      'sla_primeira_resposta': '⏰',
      'lead_assumido_sem_resposta': '⚠️',
      'lead_abandonado': '🔴',
      'performance_baixa': '📉',
      'system_alert': '🚨'
    };
    return icons[alertType] || '📢';
  };

  if (loading) {
    return <div className="alerts-loading">Carregando alertas...</div>;
  }

  return (
    <div className="alerts-panel">
      <div className="alerts-header">
        <h2>🚨 Alertas do Sistema</h2>
        
        <div className="alerts-stats">
          <span className="stat critical">
            {stats.by_severity?.critical || 0} críticos
          </span>
          <span className="stat danger">
            {stats.by_severity?.danger || 0} urgentes
          </span>
          <span className="stat warning">
            {stats.by_severity?.warning || 0} avisos
          </span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="no-alerts">
          <span className="emoji">✅</span>
          <h3>Nenhum alerta ativo</h3>
          <p>Todos os leads estão sendo bem atendidos!</p>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-item ${alert.severity}`}
              style={{ borderLeftColor: getSeverityColor(alert.severity) }}
            >
              <div className="alert-icon">
                {getAlertIcon(alert.alert_type)}
              </div>
              
              <div className="alert-content">
                <h4>{alert.title}</h4>
                <p>{alert.message}</p>
                
                {alert.data && (
                  <div className="alert-details">
                    {alert.data.vendedor_name && (
                      <span>👤 {alert.data.vendedor_name}</span>
                    )}
                    {alert.data.lead_name && (
                      <span> • 📱 {alert.data.lead_name}</span>
                    )}
                    {alert.data.action_suggestion && (
                      <span className="suggestion">
                        💡 {alert.data.action_suggestion}
                      </span>
                    )}
                  </div>
                )}
                
                <div className="alert-time">
                  {new Date(alert.created_at).toLocaleString('pt-BR')}
                </div>
              </div>
              
              <div className="alert-actions">
                <button
                  className="btn-resolve"
                  onClick={() => resolveAlert(alert.id)}
                >
                  ✓ Resolver
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}