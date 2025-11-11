import { useEffect, useState } from "react";
import {
  X,
  MessageSquare,
  CheckCircle2,
  XCircle,
  Loader2,
  Sparkles,
  Phone,
  Mail,
  MapPin,
  Tag,
  Calendar,
  Clock,
} from "lucide-react";
import api from "../api";
import TagBadge from "./TagBadge";
import TagManager from "./TagManager";
import { toast } from "./Toast";
import "../styles/components/LeadModal.css";

export default function LeadModal({ lead, onClose, onOpenChat }) {
  const [messages, setMessages] = useState([]);
  const [logs, setLogs] = useState([]);
  const [tags, setTags] = useState([]);
  const [sla, setSla] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(lead.status);
  const [updating, setUpdating] = useState(false);
  const [showTagManager, setShowTagManager] = useState(false);

  useEffect(() => {
    if (lead?.id) loadData();
  }, [lead]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Mensagens
      const msgData = await api.getMessages(lead.id);
      const msgs = msgData.items || msgData;
      setMessages(Array.isArray(msgs) ? msgs.slice(-5) : []);
    } catch {
      setMessages([]);
    }

    try {
      // Tags
      const tagsData = await api.getLeadTags(lead.id);
      setTags(tagsData || []);
    } catch {
      setTags([]);
    }

    try {
      // Logs
      const logsData = await api.getLeadLogs(lead.id);
      const filteredLogs = Array.isArray(logsData)
        ? logsData.filter((l) => l.user_name !== "Sistema").slice(-5)
        : [];
      setLogs(filteredLogs);
    } catch {
      setLogs([]);
    }

    try {
      // SLA
      const slaData = await api.getLeadSLA(lead.id);
      setSla(slaData);
    } catch {
      setSla(null);
    }

    setLoading(false);
  };

  const handleChangeStatus = async (newStatus) => {
    if (updating) return;
    setUpdating(true);
    try {
      await api.updateLeadStatus(lead.id, newStatus);
      setStatus(newStatus);
      toast.success(`✅ Status alterado para: ${getStatusLabel(newStatus)}`);
    } catch {
      toast.error("❌ Erro ao atualizar status do lead.");
    } finally {
      setUpdating(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  const getStatusBadgeClass = (st) => {
    const statusMap = {
      novo: "status-novo",
      em_atendimento: "status-atendimento",
      qualificado: "status-qualificado",
      negociacao: "status-negociacao",
      ganho: "status-ganho",
      perdido: "status-perdido",
    };
    return statusMap[st] || "status-default";
  };

  const getStatusLabel = (st) => {
    const labels = {
      novo: "Novo",
      em_atendimento: "Em Atendimento",
      qualificado: "Qualificado",
      negociacao: "Negociação",
      ganho: "Ganho",
      perdido: "Perdido",
    };
    return labels[st] || st;
  };

  return (
    <>
      <div className="lead-modal-overlay" onClick={onClose}></div>
      <div className="lead-modal-popup">
        {/* ===== HEADER ===== */}
        <div className="lead-modal-header">
          <h2>👤 Detalhes do Lead</h2>
          <button onClick={onClose} className="lead-modal-close" title="Fechar">
            <X size={22} />
          </button>
        </div>

        {/* ===== STATUS BAR ===== */}
        <div className={`status-bar ${getStatusBadgeClass(status)}`}></div>

        {/* ===== CONTEÚDO ===== */}
        <div className="lead-modal-content">
          {/* === INFORMAÇÕES === */}
          <div className="lead-modal-section">
            <h3>
              <Calendar size={14} /> Informações
            </h3>
            <div className="lead-info-grid">
              <div className="lead-info-item">
                <span className="lead-info-label">Nome</span>
                <span className="lead-info-value">
                  {lead.name || "Não informado"}
                </span>
              </div>

              <div className="lead-info-item">
                <span className="lead-info-label">
                  <Phone size={14} /> Telefone
                </span>
                <span className="lead-info-value">{lead.phone}</span>
              </div>

              {lead.email && (
                <div className="lead-info-item">
                  <span className="lead-info-label">
                    <Mail size={14} /> Email
                  </span>
                  <span className="lead-info-value">{lead.email}</span>
                </div>
              )}

              {lead.city && (
                <div className="lead-info-item">
                  <span className="lead-info-label">
                    <MapPin size={14} /> Cidade
                  </span>
                  <span className="lead-info-value">{lead.city}</span>
                </div>
              )}

              <div className="lead-info-item">
                <span className="lead-info-label">Status</span>
                <span className={`status-badge ${getStatusBadgeClass(status)}`}>
                  {getStatusLabel(status)}
                </span>
              </div>

              {lead.created_at && (
                <div className="lead-info-item">
                  <span className="lead-info-label">
                    <Calendar size={14} /> Criado em
                  </span>
                  <span className="lead-info-value">
                    {formatDate(lead.created_at)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* === TAGS === */}
          <div className="lead-modal-section">
            <div className="lead-modal-section-header">
              <h3>
                <Tag size={14} /> Tags
              </h3>
              <button
                className="btn-add-tag"
                onClick={() => setShowTagManager(true)}
              >
                Gerenciar
              </button>
            </div>
            {tags.length > 0 ? (
              <div className="tags-container">
                {tags.map((tag) => (
                  <TagBadge key={tag.id} tag={tag} />
                ))}
              </div>
            ) : (
              <p className="empty-state">Nenhuma tag adicionada</p>
            )}
          </div>

          {/* === SLA === */}
          {sla &&
            (sla.first_response_time_formatted ||
              sla.avg_response_time_formatted) && (
              <div className="lead-modal-section">
                <h3>
                  <Clock size={14} /> Tempo de Resposta
                </h3>
                <div className="sla-info">
                  {sla.first_response_time_formatted && (
                    <div className="sla-item">
                      <span className="sla-label">Primeira resposta</span>
                      <span className="sla-value">
                        {sla.first_response_time_formatted}
                      </span>
                    </div>
                  )}
                  {sla.avg_response_time_formatted && (
                    <div className="sla-item">
                      <span className="sla-label">Tempo médio</span>
                      <span className="sla-value">
                        {sla.avg_response_time_formatted}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

          {/* === ÚLTIMAS MENSAGENS === */}
          <div className="lead-modal-section">
            <h3>
              <MessageSquare size={14} /> Conversas Recentes
            </h3>
            {loading ? (
              <div className="loading-state">
                <Loader2 className="spin" size={20} />
                <span>Carregando...</span>
              </div>
            ) : messages.length === 0 ? (
              <p className="empty-state">Nenhuma mensagem ainda</p>
            ) : (
              <div className="messages-preview">
                {messages.map((msg, i) => (
                  <div key={i} className={`message-item from-${msg.sender_type}`}>
                    <div className="message-sender">
                      {msg.sender_name || msg.sender_type}
                    </div>
                    <div className="message-content">{msg.content}</div>
                    <div className="message-time">
                      {formatDate(msg.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* === INTELIGÊNCIA === */}
          <div className="lead-modal-section">
            <h3>
              <Sparkles size={14} /> Análise Inteligente
            </h3>
            <div className="ai-preview">
              <p>
                🚀 Em breve, a IA da Veloce vai gerar insights automáticos sobre
                cada lead.
              </p>
            </div>
          </div>
        </div>

        {/* ===== RODAPÉ ===== */}
        <div className="lead-modal-actions">
          <button
            className="lead-modal-btn btn-success"
            onClick={() => handleChangeStatus("ganho")}
            disabled={updating}
          >
            {updating ? (
              <Loader2 size={16} className="spin" />
            ) : (
              <CheckCircle2 size={16} />
            )}
            {updating ? " Salvando..." : " Ganho"}
          </button>

          <button
            className="lead-modal-btn btn-danger"
            onClick={() => handleChangeStatus("perdido")}
            disabled={updating}
          >
            {updating ? (
              <Loader2 size={16} className="spin" />
            ) : (
              <XCircle size={16} />
            )}
            {updating ? " Salvando..." : " Perdido"}
          </button>

          <button
            className="lead-modal-btn btn-primary"
            onClick={() => {
              onOpenChat(lead);
              onClose();
            }}
          >
            <MessageSquare size={16} /> Abrir no Chat
          </button>
        </div>
      </div>

      {/* === MODAL DE TAGS === */}
      {showTagManager && (
        <TagManager
          leadId={lead.id}
          isOpen={showTagManager}
          onClose={() => setShowTagManager(false)}
          onTagsUpdated={loadData}
        />
      )}
    </>
  );
}
