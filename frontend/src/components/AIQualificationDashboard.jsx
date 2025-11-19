/**
 * Dashboard de Monitoramento de Qualificação por IA
 *
 * Exibe conversas ativas, estatísticas e permite intervenção manual
 */

import React, { useState, useEffect } from 'react';
import {
  Phone, MessageCircle, TrendingUp, Users,
  CheckCircle, XCircle, AlertCircle, Clock
} from 'lucide-react';
import api from '../api';
import { toast } from './Toast';
import '../styles/components/AIQualificationDashboard.css';

const AIQualificationDashboard = () => {
  const [stats, setStats] = useState(null);
  const [activeConversations, setActiveConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);

  // Carrega dados
  useEffect(() => {
    loadDashboardData();

    // Atualiza a cada 10 segundos
    const interval = setInterval(loadDashboardData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // Carrega estatísticas
      const statsData = await api.getAIStats();
      setStats(statsData.stats);

      // Carrega conversas ativas
      const convsData = await api.getAIActiveConversations();
      setActiveConversations(convsData.conversations);

      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      toast.error('Erro ao carregar dados do dashboard');
    }
  };

  const handleEscalate = async (phone) => {
    if (!confirm('Deseja escalar esta conversa para atendimento humano?')) return;

    try {
      await api.escalateAIConversation(phone);
      toast.success('Conversa escalada com sucesso!');
      loadDashboardData();
    } catch (error) {
      toast.error('Erro ao escalar conversa');
    }
  };

  const handleEndConversation = async (phone) => {
    if (!confirm('Deseja encerrar esta conversa?')) return;

    try {
      await api.endAIConversation(phone, 'Manual');
      toast.success('Conversa encerrada');
      loadDashboardData();
    } catch (error) {
      toast.error('Erro ao encerrar conversa');
    }
  };

  const viewConversationDetails = async (phone) => {
    try {
      const data = await api.getAIConversation(phone);
      setSelectedConversation(data.conversation);
    } catch (error) {
      toast.error('Erro ao carregar detalhes');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Carregando dashboard...</div>
      </div>
    );
  }

  return (
    <div className="ai-dashboard">
      <div className="ai-dashboard-container">
        {/* Header */}
        <div className="ai-dashboard-header">
          <h1>
            <MessageCircle size={32} />
            Qualificação Inteligente de Leads
          </h1>
          <p>
            Monitoramento em tempo real do sistema de IA
          </p>
        </div>

        {/* KPIs */}
        {stats && (
          <div className="kpi-grid">
            <KPICard
              icon={<Users size={24} />}
              title="Total de Conversas"
              value={stats.total_conversations}
              color="blue"
            />
            <KPICard
              icon={<CheckCircle size={24} />}
              title="Leads Qualificados"
              value={stats.qualified_leads}
              subtitle={`${stats.conversion_rate?.toFixed(1)}% conversão`}
              color="green"
            />
            <KPICard
              icon={<AlertCircle size={24} />}
              title="Escalados"
              value={stats.escalated_to_human}
              color="orange"
            />
            <KPICard
              icon={<Clock size={24} />}
              title="Em Andamento"
              value={stats.active_conversations}
              color="purple"
            />
          </div>
        )}

        {/* Conversas Ativas */}
        <div className="conversations-section">
          <div className="conversations-header">
            <h2>
              <MessageCircle size={20} />
              Conversas Ativas
              <span className="conversations-count">{activeConversations.length}</span>
            </h2>
          </div>

          <div className="conversations-list">
            {activeConversations.length === 0 ? (
              <div className="conversations-empty">
                Nenhuma conversa ativa no momento
              </div>
            ) : (
              activeConversations.map((conv) => (
                <ConversationCard
                  key={conv.phone}
                  conversation={conv}
                  onView={() => viewConversationDetails(conv.phone)}
                  onEscalate={() => handleEscalate(conv.phone)}
                  onEnd={() => handleEndConversation(conv.phone)}
                />
              ))
            )}
          </div>
        </div>

        {/* Modal de Detalhes */}
        {selectedConversation && (
          <ConversationModal
            conversation={selectedConversation}
            onClose={() => setSelectedConversation(null)}
          />
        )}
      </div>
    </div>
  );
};

// Componente de KPI Card
const KPICard = ({ icon, title, value, subtitle, color }) => {
  return (
    <div className="kpi-card">
      <div className={`kpi-icon-wrapper ${color}`}>
        {icon}
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-title">{title}</div>
      {subtitle && (
        <div className="kpi-subtitle">{subtitle}</div>
      )}
    </div>
  );
};

// Componente de Card de Conversa
const ConversationCard = ({ conversation, onView, onEscalate, onEnd }) => {
  const getScoreClass = (score) => {
    if (score >= 70) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  const getStatusBadge = (status) => {
    const badges = {
      in_progress: { text: 'Em Progresso', class: 'in-progress' },
      qualified: { text: 'Qualificado', class: 'qualified' },
      disqualified: { text: 'Desqualificado', class: 'disqualified' },
      needs_human: { text: 'Precisa Humano', class: 'needs-human' }
    };

    const badge = badges[status] || badges.in_progress;
    return (
      <span className={`status-badge ${badge.class}`}>
        {badge.text}
      </span>
    );
  };

  return (
    <div className="conversation-card">
      <div className="conversation-card-header">
        <div className="conversation-contact">
          <div className="conversation-avatar">
            <Phone size={20} />
          </div>
          <div className="conversation-info">
            <h3>{conversation.collected_data?.name || 'Nome não coletado'}</h3>
            <div className="conversation-phone">{conversation.phone}</div>
            <div className="conversation-badges">
              {getStatusBadge(conversation.status)}
              <span className={`score-badge ${getScoreClass(conversation.score)}`}>
                Score: {conversation.score}
              </span>
            </div>
          </div>
        </div>

        <div className="conversation-meta">
          <div>{conversation.messages_count} mensagens</div>
          <div>{conversation.attempts} tentativas</div>
        </div>
      </div>

      {/* Dados Coletados */}
      {Object.keys(conversation.collected_data || {}).length > 0 && (
        <div className="collected-data">
          <div className="collected-data-title">Dados Coletados:</div>
          <div className="collected-data-grid">
            {Object.entries(conversation.collected_data).map(([key, value]) => (
              value && (
                <div key={key} className="collected-data-item">
                  <span className="collected-data-key">{key}:</span> {value}
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Ações */}
      <div className="conversation-actions">
        <button onClick={onView} className="action-btn view">
          Ver Detalhes
        </button>
        <button onClick={onEscalate} className="action-btn escalate">
          Escalar
        </button>
        <button onClick={onEnd} className="action-btn end">
          Encerrar
        </button>
      </div>
    </div>
  );
};

// Modal de Detalhes da Conversa
const ConversationModal = ({ conversation, onClose }) => {
  return (
    <div className="conversation-modal-overlay">
      <div className="conversation-modal">
        <div className="modal-header">
          <h3>Detalhes da Conversa</h3>
          <button onClick={onClose} className="modal-close-btn">
            ✕
          </button>
        </div>

        <div className="modal-content">
          {/* Histórico de Mensagens */}
          <div className="modal-section">
            <h4>Histórico</h4>
            <div className="messages-history">
              {conversation.messages?.map((msg, idx) => (
                <div
                  key={idx}
                  className={`message-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}
                >
                  <div className="message-header">
                    {msg.role === 'user' ? '👤 Cliente' : '🤖 IA'} • {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Notas */}
          {conversation.notes && conversation.notes.length > 0 && (
            <div className="modal-section">
              <h4>Notas</h4>
              <div className="notes-container">
                <div className="notes-list">
                  {conversation.notes.map((note, idx) => (
                    <div key={idx} className="note-item">{note}</div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIQualificationDashboard;