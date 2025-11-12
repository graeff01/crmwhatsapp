import React from 'react';
import '../styles/components/NotificationCenter.css';

/**
 * Centro de Notificações - Painel completo de notificações
 * @param {Object} props
 * @param {Array} props.notifications - Lista de notificações
 * @param {Function} props.onMarkAsRead - Callback para marcar como lida
 * @param {Function} props.onMarkAllAsRead - Callback para marcar todas como lidas
 * @param {Function} props.onClearAll - Callback para limpar todas
 * @param {Function} props.onRemove - Callback para remover notificação
 * @param {Function} props.onClose - Callback para fechar o centro
 * @param {boolean} props.soundEnabled - Se o som está habilitado
 * @param {Function} props.onToggleSound - Callback para toggle do som
 */
const NotificationCenter = ({
  notifications = [],
  onMarkAsRead,
  onMarkAllAsRead,
  onClearAll,
  onRemove,
  onClose,
  soundEnabled = true,
  onToggleSound
}) => {
  
  // Ícones por tipo de notificação
  const getIcon = (type) => {
    const icons = {
      'novo_lead': '🆕',
      'nova_mensagem': '💬',
      'sla_alerta': '⚠️',
      'status_mudou': '✅',
      'lead_atribuido': '📞',
      'lead_transferido': '🔄'
    };
    return icons[type] || '🔔';
  };

  // Cor por prioridade
  const getPriorityColor = (priority) => {
    const colors = {
      'low': '#10b981',
      'medium': '#3b82f6',
      'high': '#f59e0b',
      'urgent': '#ef4444'
    };
    return colors[priority] || '#6b7280';
  };

  // Formatar timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // diferença em segundos

    if (diff < 60) return 'Agora';
    if (diff < 3600) return `${Math.floor(diff / 60)}m atrás`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="notification-center">
      {/* Header */}
      <div className="notification-header">
        <div className="notification-header-left">
          <h3>Notificações</h3>
          {unreadCount > 0 && (
            <span className="unread-badge">{unreadCount}</span>
          )}
        </div>
        
        <div className="notification-header-actions">
          {/* Toggle de som */}
          <button
            className="icon-button"
            onClick={onToggleSound}
            title={soundEnabled ? 'Desativar sons' : 'Ativar sons'}
          >
            {soundEnabled ? '🔊' : '🔇'}
          </button>

          {/* Marcar todas como lidas */}
          {unreadCount > 0 && (
            <button
              className="icon-button"
              onClick={onMarkAllAsRead}
              title="Marcar todas como lidas"
            >
              ✓✓
            </button>
          )}

          {/* Limpar todas */}
          {notifications.length > 0 && (
            <button
              className="icon-button"
              onClick={onClearAll}
              title="Limpar todas"
            >
              🗑️
            </button>
          )}

          {/* Fechar */}
          <button
            className="icon-button"
            onClick={onClose}
            title="Fechar"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Lista de notificações */}
      <div className="notification-list">
        {notifications.length === 0 ? (
          <div className="notification-empty">
            <span className="empty-icon">🔔</span>
            <p>Nenhuma notificação</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${!notification.read ? 'unread' : ''}`}
              style={{ borderLeftColor: getPriorityColor(notification.priority) }}
            >
              {/* Indicador de não lida */}
              {!notification.read && <div className="unread-indicator"></div>}

              {/* Conteúdo */}
              <div className="notification-content">
                <div className="notification-icon">
                  {getIcon(notification.type)}
                </div>

                <div className="notification-body">
                  <div className="notification-title">
                    {notification.title}
                  </div>
                  <div className="notification-message">
                    {notification.message}
                  </div>
                  <div className="notification-time">
                    {formatTime(notification.timestamp)}
                  </div>
                </div>

                {/* Ações */}
                <div className="notification-actions">
                  {!notification.read && (
                    <button
                      className="action-button"
                      onClick={() => onMarkAsRead(notification.id)}
                      title="Marcar como lida"
                    >
                      ✓
                    </button>
                  )}
                  <button
                    className="action-button"
                    onClick={() => onRemove(notification.id)}
                    title="Remover"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;