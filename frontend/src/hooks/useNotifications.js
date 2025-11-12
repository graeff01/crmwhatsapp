import { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';

/**
 * Hook customizado para gerenciar notificações em tempo real
 * @returns {Object} Estado e funções de notificações
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [socket, setSocket] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Conectar ao Socket.IO
  useEffect(() => {
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('🔔 Conectado ao serviço de notificações');
      // Entrar na sala de gestores (ou sala específica do usuário)
      newSocket.emit('join_room', { room: 'gestores' });
    });

    newSocket.on('notification', (notification) => {
      console.log('🔔 Nova notificação recebida:', notification);
      addNotification(notification);
    });

    newSocket.on('disconnect', () => {
      console.log('🔌 Desconectado do serviço de notificações');
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  // Adicionar nova notificação
  const addNotification = useCallback((notification) => {
    setNotifications((prev) => [notification, ...prev]);
    
    // Incrementar contador de não lidas
    if (!notification.read) {
      setUnreadCount((prev) => prev + 1);
    }

    // Tocar som se habilitado
    if (soundEnabled) {
      playNotificationSound(notification.sound);
    }

    // Mostrar notificação do navegador se permitido
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.id
      });
    }
  }, [soundEnabled]);

 // Tocar som de notificação
const playNotificationSound = (soundType = 'default') => {
  try {
    // Usa o beep do navegador como fallback
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.value = 0.3;
    
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.1);
  } catch (error) {
    console.log('Erro ao tocar som:', error);
  }
};

  // Marcar notificação como lida
  const markAsRead = useCallback((notificationId) => {
    setNotifications((prev) =>
      prev.map((notif) =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );

    // Decrementar contador
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  // Marcar todas como lidas
  const markAllAsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.map((notif) => ({ ...notif, read: true }))
    );
    setUnreadCount(0);
  }, []);

  // Limpar todas as notificações
  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // Remover notificação específica
  const removeNotification = useCallback((notificationId) => {
    setNotifications((prev) => {
      const notification = prev.find(n => n.id === notificationId);
      if (notification && !notification.read) {
        setUnreadCount((count) => Math.max(0, count - 1));
      }
      return prev.filter((notif) => notif.id !== notificationId);
    });
  }, []);

  // Toggle som
  const toggleSound = useCallback(() => {
    setSoundEnabled((prev) => !prev);
  }, []);

  // Solicitar permissão para notificações do navegador
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }, []);

  return {
    notifications,
    unreadCount,
    soundEnabled,
    markAsRead,
    markAllAsRead,
    clearAll,
    removeNotification,
    toggleSound,
    requestNotificationPermission
  };
};

export default useNotifications;