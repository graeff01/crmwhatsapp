import React, { useState } from 'react';
import NotificationBell from './NotificationBell';
import NotificationCenter from './NotificationCenter';
import useNotifications from '../hooks/useNotifications';

/**
 * Componente exemplo de uso do sistema de notificações
 * Integre este componente no seu Header/Navbar
 */
const NotificationsContainer = () => {
  const [showCenter, setShowCenter] = useState(false);

  const {
    notifications,
    unreadCount,
    soundEnabled,
    markAsRead,
    markAllAsRead,
    clearAll,
    removeNotification,
    toggleSound,
    requestNotificationPermission
  } = useNotifications();

  // Solicitar permissão ao montar
  React.useEffect(() => {
    requestNotificationPermission();
  }, [requestNotificationPermission]);

  // Fechar ao clicar fora
  const handleClickOutside = (e) => {
    if (e.target.closest('.notification-center') === null &&
        e.target.closest('.notification-bell') === null) {
      setShowCenter(false);
    }
  };

  React.useEffect(() => {
    if (showCenter) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showCenter]);

  return (
    <div style={{ position: 'relative' }}>
      {/* Sino de notificações */}
      <NotificationBell
        count={unreadCount}
        onClick={() => setShowCenter(!showCenter)}
      />

      {/* Centro de notificações */}
      {showCenter && (
        <NotificationCenter
          notifications={notifications}
          onMarkAsRead={markAsRead}
          onMarkAllAsRead={markAllAsRead}
          onClearAll={clearAll}
          onRemove={removeNotification}
          onClose={() => setShowCenter(false)}
          soundEnabled={soundEnabled}
          onToggleSound={toggleSound}
        />
      )}
    </div>
  );
};

export default NotificationsContainer;  // ← ADICIONE ESTA LINHA!