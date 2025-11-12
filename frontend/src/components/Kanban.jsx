import { useEffect, useState } from 'react';
import api from '../api';
import LeadModal from './LeadModal';
import { toast } from './Toast';
import TagBadge from "./TagBadge";
import TagManager from "./TagManager";  
import '../styles/components/Kanban.css';

export default function Kanban({ user }) {
  const [allLeads, setAllLeads] = useState([]);
  const [leads, setLeads] = useState([]);
  const [draggedLead, setDraggedLead] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [stats, setStats] = useState({
    total: 0,
    novo: 0,
    em_atendimento: 0,
    qualificado: 0,
    ganho: 0,
    perdido: 0
  });

  const stages = [
    { key: 'novo', label: '🆕 Novo', color: '#3b82f6' },
    { key: 'em_atendimento', label: '💬 Em Atendimento', color: '#f59e0b' },
    { key: 'qualificado', label: '⭐ Qualificado', color: '#8b5cf6' },
    { key: 'ganho', label: '✅ Ganho', color: '#10b981' },
    { key: 'perdido', label: '❌ Perdido', color: '#ef4444' },
  ];

  // ==========================
  // 🔁 CARREGA LEADS DO SERVIDOR
  // ==========================
  const loadLeads = async () => {
    try {
      setLoading(true);
      const data = await api.getLeads();
      setAllLeads(data);

      // 🔒 FILTRA CONFORME O PAPEL DO USUÁRIO
      let filtered = data;

      if (user.role === 'vendedor') {
        // ✅ Vendedor: SOMENTE leads atribuídos a ele
        filtered = data.filter((l) => l.assigned_to === user.id);
        console.log(`🔐 Vendedor ${user.name} vê ${filtered.length} leads`);
        
      } else if (user.role === 'gestor') {
        // ✅ Gestor: leads da sua equipe
        filtered = data.filter((l) => l.team_id === user.team_id);
        console.log(`👔 Gestor ${user.name} vê ${filtered.length} leads da equipe`);
        
      } else if (user.role === 'admin' || user.role === 'administrador') {
        // ✅ Admin: TUDO
        filtered = data;
        console.log(`👑 Admin ${user.name} vê TODOS os ${filtered.length} leads`);
      }
      
      setLeads(filtered);
      calculateStats(filtered);
      
    } catch (err) {
      console.error('Erro ao carregar leads:', err);
      toast.error('❌ Erro ao carregar leads');
    } finally {
      setLoading(false);
    }
  };

  // ==========================
  // 📊 CALCULA ESTATÍSTICAS
  // ==========================
  const calculateStats = (leadsData) => {
    const stats = {
      total: leadsData.length,
      novo: leadsData.filter(l => l.status === 'novo').length,
      em_atendimento: leadsData.filter(l => l.status === 'em_atendimento').length,
      qualificado: leadsData.filter(l => l.status === 'qualificado').length,
      ganho: leadsData.filter(l => l.status === 'ganho').length,
      perdido: leadsData.filter(l => l.status === 'perdido').length,
    };
    setStats(stats);
  };

  useEffect(() => {
    loadLeads();
    
    // 🔄 Auto-refresh a cada 30 segundos
    const interval = setInterval(loadLeads, 30000);
    return () => clearInterval(interval);
  }, [user.id]);

  // ==========================
  // 🔍 FILTROS E BUSCA
  // ==========================
  const getFilteredLeads = () => {
    let filtered = leads;

    // Filtro por status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(l => l.status === filterStatus);
    }

    // Busca por nome ou telefone
    if (searchTerm) {
      filtered = filtered.filter(l => 
        l.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        l.phone?.includes(searchTerm)
      );
    }

    return filtered;
  };

  // ==========================
  // 🎯 ARRASTAR E SOLTAR
  // ==========================
  const handleDragStart = (lead) => {
    // 🚫 Vendedor não pode arrastar leads de outros
    if (user.role === 'vendedor' && lead.assigned_to !== user.id) {
      toast.warn('🚫 Você não pode mover leads de outros vendedores.');
      return;
    }
    setDraggedLead(lead);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = async (status, e) => {
    e.currentTarget.classList.remove('drag-over');
    
    if (!draggedLead || draggedLead.status === status) {
      setDraggedLead(null);
      return;
    }

    // 🚫 Validação extra de permissões
    if (user.role === 'vendedor' && draggedLead.assigned_to !== user.id) {
      toast.warn('🚫 Você não pode mover leads de outros vendedores.');
      setDraggedLead(null);
      return;
    }

    try {
      await api.updateLeadStatus(draggedLead.id, status);
      
      // Atualiza localmente
      setLeads((prev) =>
        prev.map((l) => (l.id === draggedLead.id ? { ...l, status } : l))
      );
      
      // Recalcula stats
      const updatedLeads = leads.map((l) => 
        l.id === draggedLead.id ? { ...l, status } : l
      );
      calculateStats(updatedLeads);
      
      toast.success(`✅ Lead movido para ${stages.find(s => s.key === status)?.label}`);
      
    } catch (err) {
      console.error('Erro ao atualizar status:', err);
      toast.error('❌ Erro ao mover lead');
    } finally {
      setDraggedLead(null);
    }
  };

  // ==========================
  // 📦 RENDERIZA COLUNAS
  // ==========================
  const renderColumn = (stage) => {
    const filteredLeads = getFilteredLeads();
    const stageLeads = filteredLeads.filter((lead) => lead.status === stage.key);

    return (
      <div
        key={stage.key}
        className="kanban-column"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(stage.key, e)}
      >
        <div 
          className="kanban-column-header"
          style={{ borderTopColor: stage.color }}
        >
          <div className="column-title">
            <span className="column-emoji">{stage.label.split(' ')[0]}</span>
            <span className="column-name">{stage.label.substring(stage.label.indexOf(' ') + 1)}</span>
          </div>
          <span 
            className="column-count"
            style={{ backgroundColor: stage.color }}
          >
            {stageLeads.length}
          </span>
        </div>

        <div className="kanban-list">
          {loading ? (
            <div className="column-loading">
              <div className="spinner"></div>
              <p>Carregando...</p>
            </div>
          ) : stageLeads.length === 0 ? (
            <div className="column-empty">
              <span className="empty-icon">📭</span>
              <p>Nenhum lead</p>
            </div>
          ) : (
            stageLeads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                user={user}
                onDragStart={() => handleDragStart(lead)}
                onSelect={setSelectedLead}
              />
            ))
          )}
        </div>
      </div>
    );
  };

  // ==========================
  // 🧱 RENDER PRINCIPAL
  // ==========================
  return (
    <>
      {/* TOOLBAR COM FILTROS */}
      <div className="kanban-toolbar">
        <div className="toolbar-left">
          <div className="kanban-stats-mini">
            <span className="stat-item">
              <strong>{stats.total}</strong> Total
            </span>
            <span className="stat-item success">
              <strong>{stats.ganho}</strong> Ganhos
            </span>
            <span className="stat-item danger">
              <strong>{stats.perdido}</strong> Perdidos
            </span>
          </div>
        </div>

        <div className="toolbar-right">
          {/* BUSCA */}
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Buscar lead..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            {searchTerm && (
              <button 
                className="clear-search"
                onClick={() => setSearchTerm('')}
              >
                ✕
              </button>
            )}
          </div>

          {/* FILTRO POR STATUS */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">Todos</option>
            {stages.map(stage => (
              <option key={stage.key} value={stage.key}>
                {stage.label}
              </option>
            ))}
          </select>

          {/* BOTÃO REFRESH */}
          <button 
            className="btn-refresh"
            onClick={loadLeads}
            disabled={loading}
          >
            🔄
          </button>
        </div>
      </div>

      {/* BOARD DO KANBAN */}
      <div className="kanban-board">
        {stages.map(renderColumn)}
      </div>

      {/* MODAL DE DETALHES */}
      {selectedLead && (
        <LeadModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onOpenChat={(lead) => {
            setSelectedLead(null);
            console.log('🟢 Abrir lead no chat:', lead);
          }}
          onUpdate={loadLeads}
        />
      )}
    </>
  );
}

// ==============================
// 💳 COMPONENTE LEADCARD
// ==============================
function LeadCard({ lead, onDragStart, onSelect, user }) {
  const isDraggable = user.role !== 'vendedor' || lead.assigned_to === user.id;
  const isOwner = lead.assigned_to === user.id;

  // 📅 Tempo desde última interação
  const getTimeAgo = (date) => {
    if (!date) return '';
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'agora';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    return `${diffDays}d`;
  };

  // 🎨 Cor do card baseada na urgência
  const getUrgencyClass = () => {
    if (!lead.last_interaction) return '';
    
    const hoursSinceInteraction = (new Date() - new Date(lead.last_interaction)) / (1000 * 60 * 60);
    
    if (hoursSinceInteraction > 48) return 'urgent-high';
    if (hoursSinceInteraction > 24) return 'urgent-medium';
    return '';
  };

  return (
    <div
      className={`kanban-card ${!isDraggable ? 'blocked' : ''} ${getUrgencyClass()} ${isOwner ? 'is-owner' : ''}`}
      draggable={isDraggable}
      onDragStart={isDraggable ? onDragStart : undefined}
      onClick={() => onSelect(lead)}
      title={
        !isDraggable
          ? '🔒 Este lead pertence a outro vendedor'
          : '👆 Clique para ver detalhes ou arraste para mudar status'
      }
    >
      {/* HEADER DO CARD */}
      <div className="lead-card-header">
        <span className="lead-id">#{lead.id}</span>
        {isOwner && <span className="owner-badge">👤 Meu</span>}
        {lead.last_interaction && (
          <span className="time-ago">{getTimeAgo(lead.last_interaction)}</span>
        )}
      </div>

      {/* CORPO DO CARD */}
      <div className="lead-card-body">
        <strong className="lead-name">
          {lead.name || 'Lead sem nome'}
        </strong>
        <p className="lead-phone">📱 {lead.phone}</p>
        {lead.city && (
          <small className="lead-location">📍 {lead.city}</small>
        )}
      </div>

      {/* TAGS */}
      {lead.tags && lead.tags.length > 0 && (
        <div className="lead-tags">
          {lead.tags.slice(0, 2).map((tag, idx) => (
            <TagBadge key={idx} tag={tag} />
          ))}
          {lead.tags.length > 2 && (
            <span className="more-tags">+{lead.tags.length - 2}</span>
          )}
        </div>
      )}

      {/* FOOTER DO CARD */}
      <div className="lead-card-footer">
        {lead.assigned_user_name && (
          <span className="assigned-to">
            👤 {lead.assigned_user_name}
          </span>
        )}
        {!isDraggable && (
          <span className="locked-icon" title="Bloqueado">🔒</span>
        )}
      </div>
    </div>
  );
}