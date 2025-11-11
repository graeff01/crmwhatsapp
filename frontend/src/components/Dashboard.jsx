import { useState, useEffect, useRef } from 'react';
import { MessageCircle, Users, Send, LogOut } from 'lucide-react';
import api from '../api';
import io from 'socket.io-client';
import UserManagement from './UserManagement';
import Metrics from './Metrics';
import Kanban from './Kanban';
import { ToastManager, toast } from './Toast';
import LeadTimeline from "./LeadTimeline";
import '../styles/components/Kanban.css';
import '../styles/components/chat.css';





export default function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('meus-leads');
  const [leads, setLeads] = useState([]);
  const [queueLeads, setQueueLeads] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [socket, setSocket] = useState(null);
  const [fromKanbanLead, setFromKanbanLead] = useState(null);
  const [newLeadsCount, setNewLeadsCount] = useState(0);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const [activeLead, setActiveLead] = useState(null);
  const [currentView, setCurrentView] = useState("kanban"); // "kanban" | "chat" | "metrics"


  const newLeadSound = useRef(null);
  const newMessageSound = useRef(null);

  // ================= SOCKET.IO =================
  useEffect(() => {
    const newSocket = io('http://localhost:5000', { transports: ['websocket'] });
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('✅ Conectado ao Socket.io');
      if (user?.role === 'admin' || user?.role === 'gestor') {
        newSocket.emit('join_room', { room: 'gestores' });
      }
    });

    // 📩 Nova mensagem
    newSocket.on('new_message', (data) => {
      if (selectedLead && data.lead_id === selectedLead.id) {
        setMessages((prev) => [...prev, {
          content: data.content,
          sender_type: data.sender_type,
          timestamp: data.timestamp,
        }]);
      } else {
        setNewMessagesCount((c) => c + 1);
        playSound(newMessageSound);
        toast.info(`💬 Nova mensagem de ${data.lead_name || 'Lead desconhecido'}`);
      }
      refreshLeads();
    });

    // 👤 Novo lead
    newSocket.on('lead_assigned', (data) => {
      setNewLeadsCount((c) => c + 1);
      playSound(newLeadSound);
      toast.success(`👤 Novo lead atribuído: ${data.lead_name || 'Lead'}`);
      refreshLeads();
    });

    newSocket.on('disconnect', () => {
      toast.warn('⚠️ Desconectado do servidor');
    });

    return () => newSocket.disconnect();
  }, [user, selectedLead]);

  // ================= FUNÇÕES AUXILIARES =================
  const playSound = (ref) => {
    if (ref.current) {
      ref.current.currentTime = 0;
      ref.current.play().catch(() => {});
    }
  };

  const refreshLeads = async () => {
    try {
      const [dataLeads, dataQueue] = await Promise.all([
        api.getLeads(),
        api.getLeadsQueue(),
      ]);
      setLeads(dataLeads);
      setQueueLeads(dataQueue);
    } catch (error) {
      toast.error('❌ Erro ao atualizar leads');
    }
  };

  const loadMessages = async (leadId) => {
    try {
      const data = await api.getMessages(leadId);
      setMessages(data);
    } catch (error) {
      toast.error('❌ Erro ao carregar mensagens');
    }
  };

  useEffect(() => {
    refreshLeads();
    const interval = setInterval(refreshLeads, 10000);
    return () => clearInterval(interval);
  }, []);

  // ================= AÇÕES =================
  const handleSelectLead = (lead) => {
    setSelectedLead(lead);
    setNewMessagesCount(0); // zera badge
    loadMessages(lead.id);
  };

  const handleAssignLead = async (leadId) => {
    try {
      await api.assignLead(leadId);
      await refreshLeads();
      const lead = queueLeads.find((l) => l.id === leadId);
      if (lead) {
        handleSelectLead({ ...lead, assigned_to: user.id });
        toast.success(`✅ Você assumiu o lead ${lead.name || lead.phone}`);
        setNewLeadsCount((c) => Math.max(c - 1, 0));
      }
    } catch {
      toast.error('❌ Erro ao pegar lead');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedLead) return;

    try {
      await api.sendMessage(selectedLead.id, messageInput);
      setMessages((prev) => [...prev, {
        content: messageInput,
        sender_type: 'vendedor',
        sender_name: user.name,
        timestamp: new Date().toISOString(),
      }]);
      toast.success('✅ Mensagem enviada com sucesso!');
      setMessageInput('');
    } catch {
      toast.error('❌ Falha ao enviar mensagem');
    }
  };

  // ================= KANBAN → CHAT =================
  useEffect(() => {
    if (fromKanbanLead) {
      setActiveTab('meus-leads');
      setSelectedLead(fromKanbanLead);
      loadMessages(fromKanbanLead.id);
      toast.info(`📲 Conversa aberta com ${fromKanbanLead.name || fromKanbanLead.phone}`);
      setFromKanbanLead(null);
    }
  }, [fromKanbanLead]);

  // ================= FORMATADORES =================
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  // ================= RENDER LEADS =================
  const renderLeadsList = (list, showAssignButton = false) => {
    if (!list.length) {
      return <div className="empty">Nenhum lead aqui ainda</div>;
    }
    return list.map((lead) => (
      <div
        key={lead.id}
        className={`lead-item ${selectedLead?.id === lead.id ? 'active' : ''}`}
        onClick={() => !showAssignButton && handleSelectLead(lead)}
      >
        <div className="lead-item-header">
          <span className="lead-name">{lead.name || lead.phone}</span>
          <span className="lead-time">{formatTime(lead.updated_at)}</span>
        </div>
        <div className="lead-last-message">{lead.phone}</div>
        <div className="lead-footer">
          <span className={`lead-status status-${lead.status}`}>
            {lead.status.replace('_', ' ')}
          </span>
          {showAssignButton && (
            <button
              className="btn btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                handleAssignLead(lead.id);
              }}
            >
              Pegar Lead
            </button>
          )}
        </div>
      </div>
    ));
  };

  // ================= LAYOUT =================
  return (
    <div className="app-container">
      {/* ==== ÁUDIO ==== */}
      <audio ref={newLeadSound} src="/sounds/new_lead.mp3" preload="auto" />
      <audio ref={newMessageSound} src="/sounds/new_message.mp3" preload="auto" />

      {/* ==== MODO GERENCIAL ==== */}
      {['kanban', 'metricas', 'config'].includes(activeTab) ? (
  <div className="dashboard-layout">
    
    {/* ==== SIDEBAR FIXA ==== */}
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <h2>💬 CRM <span>WhatsApp</span></h2>
          <p className="sidebar-subtitle">
            {user.role === 'admin' ? 'Administrador' : user.role === 'gestor' ? 'Gestor' : 'Vendedor'}
          </p>
          <span className="sidebar-badge">{user.role.toUpperCase()}</span>
        </div>

        <nav className="sidebar-menu">
  {/* 🔙 Botão Voltar para o Início */}
  <button
    className={`sidebar-item ${activeTab === 'meus-leads' ? 'active' : ''}`}
    onClick={() => setActiveTab('meus-leads')}
  >
    🏠 Início
  </button>

  {(user.role === 'admin' || user.role === 'gestor') && (
    <>
      <button
        className={`sidebar-item ${activeTab === 'kanban' ? 'active' : ''}`}
        onClick={() => setActiveTab('kanban')}
      >
        🗂 Kanban
      </button>
      <button
        className={`sidebar-item ${activeTab === 'metricas' ? 'active' : ''}`}
        onClick={() => setActiveTab('metricas')}
      >
        📊 Métricas
      </button>
      <button
        className={`sidebar-item ${activeTab === 'config' ? 'active' : ''}`}
        onClick={() => setActiveTab('config')}
      >
        ⚙️ Config
      </button>
    </>
  )}

  <div className="sidebar-divider"></div>

  <button className="sidebar-item logout" onClick={onLogout}>
    <LogOut size={16} /> Sair
  </button>
</nav>

      </div>
    </aside>

    {/* ==== CONTEÚDO PRINCIPAL ==== */}
    <main className="main-content">
      {activeTab === 'kanban' && (
        <Kanban user={user} onOpenLead={(lead) => setFromKanbanLead(lead)} />
      )}
      {activeTab === 'metricas' && <Metrics currentUser={user} />}
      {activeTab === 'config' && <UserManagement currentUser={user} />}
    </main>

  </div>
) : (

        /* ==== MODO DE ATENDIMENTO ==== */
        <>
          <div className="sidebar">
            <div className="sidebar-header">
  <div className="sidebar-brand">
    <h2>💬 CRM <span>WhatsApp</span></h2>
    <p className="sidebar-subtitle">
      {user.role === 'admin' ? 'Administrador' : user.role === 'gestor' ? 'Gestor' : 'Vendedor'}
    </p>
    <span className="sidebar-badge">{user.role.toUpperCase()}</span>
  </div>

  <nav className="sidebar-menu">
    {(user.role === 'admin' || user.role === 'gestor') && (
      <>
        <button
          className={`sidebar-item ${activeTab === 'kanban' ? 'active' : ''}`}
          onClick={() => setActiveTab('kanban')}
        >
          🗂 Kanban
        </button>
        <button
          className={`sidebar-item ${activeTab === 'metricas' ? 'active' : ''}`}
          onClick={() => setActiveTab('metricas')}
        >
          📊 Métricas
        </button>
        <button
          className={`sidebar-item ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          ⚙️ Configurações
        </button>
      </>
    )}

    <div className="sidebar-divider"></div>

    <button className="sidebar-item logout" onClick={onLogout}>
      <LogOut size={16} /> Sair
    </button>
  </nav>
</div>


            <div className="sidebar-tabs">
              <button
                className={`tab ${activeTab === 'meus-leads' ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab('meus-leads');
                  setNewMessagesCount(0);
                }}
              >
                <MessageCircle size={18} /> Meus Leads
                {newMessagesCount > 0 && (
                  <span className="badge">{newMessagesCount}</span>
                )}
              </button>

              <button
                className={`tab ${activeTab === 'fila' ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab('fila');
                  setNewLeadsCount(0);
                }}
              >
                <Users size={18} /> Fila
                {newLeadsCount > 0 && <span className="badge">{newLeadsCount}</span>}
              </button>
            </div>

            {/* ===== LISTA DE LEADS (PREMIUM ORGANIZADO) ===== */}
<div className="leads-list">
  {activeTab === 'meus-leads' && (
    <>
      <div className="leads-header">
        <h3>📞 Meus Leads</h3>
        <span>{leads.length} ativos</span>
      </div>
      {renderLeadsList(leads)}
    </>
  )}

  {activeTab === 'fila' && (
    <>
      <div className="leads-header">
        <h3>📥 Fila de Leads</h3>
        <span>{queueLeads.length} disponíveis</span>
      </div>
      {renderLeadsList(queueLeads, true)}
    </>
  )}
</div>

          </div>

          <div className="chat-container">
            {selectedLead ? (
              <>
                <div className="chat-header">
                  <h3>{selectedLead.name || selectedLead.phone}</h3>
                  <p>{selectedLead.phone}</p>
                </div>

                <div className="chat-messages">
                  
              {messages && Array.isArray(messages) ? (
                messages.map((msg, i) => (
                  <div key={i} className={`message from-${msg.sender_type}`}>
                    <div className="message-bubble">
                      {msg.sender_type === 'vendedor' && (
                        <div className="message-sender">{msg.sender_name || 'Você'}</div>
                      )}
                      <div className="message-content">{msg.content}</div>
                      <div className="message-time">{formatTime(msg.timestamp)}</div>
                    </div>
                  </div>
                ))
              ) : messages?.items ? (
                messages.items.map((msg, i) => (
                  <div key={i} className={`message from-${msg.sender_type}`}>
                    <div className="message-bubble">
                      {msg.sender_type === 'vendedor' && (
                        <div className="message-sender">{msg.sender_name || 'Você'}</div>
                      )}
                      <div className="message-content">{msg.content}</div>
                      <div className="message-time">{formatTime(msg.timestamp)}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-messages">Nenhuma mensagem ainda</div>
              )}
            </div>

                {/* ===== TIMELINE DO LEAD ===== */}
                <div className="lead-timeline-wrapper">
                  <h4 style={{ margin: "15px 0 5px 10px", color: "#555" }}>Histórico do Lead</h4>
                  <LeadTimeline leadId={selectedLead?.id} />
                </div>


                <form onSubmit={handleSendMessage} className="chat-input-wrapper">
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder="Digite sua mensagem..."
                  />
                  <button type="submit"><Send size={18} /></button>
                </form>
              </>
            ) : (
              <div className="empty-state">
                <MessageCircle size={80} />
                <h3>Selecione um lead para começar</h3>
                <p>Escolha um lead da lista ou pegue um da fila</p>
              </div>
            )}
          </div>
        </>
      )}
      

      <ToastManager />
    </div>
  );
}
