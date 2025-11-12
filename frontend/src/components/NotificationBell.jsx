import React, { useState } from 'react';
import '../styles/components/NotificationBell.css';
/**
 * Componente de sino de notificações com badge
 * @param {Object} props
 * @param {number} props.count - Número de notificações não lidas
 * @param {Function} props.onClick - Callback ao clicar no sino
 */
const NotificationBell = ({ count = 0, onClick }) => {
  const [isAnimating, setIsAnimating] = useState(false);

  // Animar sino quando houver novas notificações
  React.useEffect(() => {
    if (count > 0) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [count]);

  return (
    <div className="notification-bell-container">
      <button
        className={`notification-bell ${isAnimating ? 'bell-ring' : ''}`}
        onClick={onClick}
        aria-label={`${count} notificações não lidas`}
      >
        {/* Ícone de sino */}
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>

        {/* Badge com contador */}
        {count > 0 && (
          <span className="notification-badge">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>
    </div>
  );
};

export default NotificationBell;