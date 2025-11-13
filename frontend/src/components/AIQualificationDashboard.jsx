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
      const statsRes = await fetch('/api/ai/stats');
      const statsData = await statsRes.json();
      setStats(statsData.stats);

      // Carrega conversas ativas
      const convsRes = await fetch('/api/ai/conversations/active');
      const convsData = await convsRes.json();
      setActiveConversations(convsData.conversations);

      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    }
  };

  const handleEscalate = async (phone) => {
    if (!confirm('Deseja escalar esta conversa para atendimento humano?')) return;

    try {
      const response = await fetch(`/api/ai/conversations/${phone}/escalate`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('Conversa escalada com sucesso!');
        loadDashboardData();
      }
    } catch (error) {
      alert('Erro ao escalar conversa');
    }
  };

  const handleEndConversation = async (phone) => {
    if (!confirm('Deseja encerrar esta conversa?')) return;

    try {
      const response = await fetch(`/api/ai/conversations/${phone}/end`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Manual' })
      });

      if (response.ok) {
        alert('Conversa encerrada');
        loadDashboardData();
      }
    } catch (error) {
      alert('Erro ao encerrar conversa');
    }
  };

  const viewConversationDetails = async (phone) => {
    try {
      const response = await fetch(`/api/ai/conversations/${phone}`);
      const data = await response.json();
      setSelectedConversation(data.conversation);
    } catch (error) {
      alert('Erro ao carregar detalhes');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <MessageCircle className="w-8 h-8 text-blue-600" />
            Qualificação Inteligente de Leads
          </h1>
          <p className="text-gray-600 mt-2">
            Monitoramento em tempo real do sistema de IA
          </p>
        </div>

        {/* KPIs */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard
              icon={<Users className="w-6 h-6" />}
              title="Total de Conversas"
              value={stats.total_conversations}
              color="blue"
            />
            <KPICard
              icon={<CheckCircle className="w-6 h-6" />}
              title="Leads Qualificados"
              value={stats.qualified_leads}
              subtitle={`${stats.conversion_rate?.toFixed(1)}% conversão`}
              color="green"
            />
            <KPICard
              icon={<AlertCircle className="w-6 h-6" />}
              title="Escalados"
              value={stats.escalated_to_human}
              color="orange"
            />
            <KPICard
              icon={<Clock className="w-6 h-6" />}
              title="Em Andamento"
              value={stats.active_conversations}
              color="purple"
            />
          </div>
        )}

        {/* Conversas Ativas */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              Conversas Ativas ({activeConversations.length})
            </h2>
          </div>

          <div className="divide-y divide-gray-200">
            {activeConversations.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
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
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className={`inline-flex p-3 rounded-lg ${colorClasses[color]} mb-4`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-600 mt-1">{title}</div>
      {subtitle && (
        <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
      )}
    </div>
  );
};

// Componente de Card de Conversa
const ConversationCard = ({ conversation, onView, onEscalate, onEnd }) => {
  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600 bg-green-50';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getStatusBadge = (status) => {
    const badges = {
      in_progress: { text: 'Em Progresso', color: 'blue' },
      qualified: { text: 'Qualificado', color: 'green' },
      disqualified: { text: 'Desqualificado', color: 'red' },
      needs_human: { text: 'Precisa Humano', color: 'orange' }
    };

    const badge = badges[status] || badges.in_progress;
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full bg-${badge.color}-50 text-${badge.color}-700`}>
        {badge.text}
      </span>
    );
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4">
          <div className="bg-blue-100 p-3 rounded-full">
            <Phone className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <div className="font-semibold text-gray-900">
              {conversation.collected_data?.name || 'Nome não coletado'}
            </div>
            <div className="text-sm text-gray-600">{conversation.phone}</div>
            <div className="flex items-center gap-2 mt-2">
              {getStatusBadge(conversation.status)}
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getScoreColor(conversation.score)}`}>
                Score: {conversation.score}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right text-sm text-gray-500">
          <div>{conversation.messages_count} mensagens</div>
          <div>{conversation.attempts} tentativas</div>
        </div>
      </div>

      {/* Dados Coletados */}
      {Object.keys(conversation.collected_data || {}).length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-xs font-medium text-gray-700 mb-2">Dados Coletados:</div>
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
            {Object.entries(conversation.collected_data).map(([key, value]) => (
              value && (
                <div key={key}>
                  <span className="font-medium">{key}:</span> {value}
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Ações */}
      <div className="flex gap-2">
        <button
          onClick={onView}
          className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          Ver Detalhes
        </button>
        <button
          onClick={onEscalate}
          className="px-4 py-2 text-sm font-medium text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
        >
          Escalar
        </button>
        <button
          onClick={onEnd}
          className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          Encerrar
        </button>
      </div>
    </div>
  );
};

// Modal de Detalhes da Conversa
const ConversationModal = ({ conversation, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Detalhes da Conversa</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Histórico de Mensagens */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Histórico</h4>
            <div className="space-y-3">
              {conversation.messages?.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user' 
                      ? 'bg-blue-50 ml-8' 
                      : 'bg-gray-50 mr-8'
                  }`}
                >
                  <div className="text-xs text-gray-500 mb-1">
                    {msg.role === 'user' ? '👤 Cliente' : '🤖 IA'} • {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="text-sm text-gray-700">{msg.content}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Notas */}
          {conversation.notes && conversation.notes.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Notas</h4>
              <div className="bg-yellow-50 p-3 rounded-lg space-y-1">
                {conversation.notes.map((note, idx) => (
                  <div key={idx} className="text-xs text-gray-600">• {note}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIQualificationDashboard;