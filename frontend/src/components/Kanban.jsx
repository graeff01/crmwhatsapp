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

  const stages = [
    { key: 'novo', label: 'Novo' },
    { key: 'em_atendimento', label: 'Em atendimento' },
    { key: 'qualificado', label: 'Qualificado' },
    { key: 'ganho', label: 'Ganho' },
    { key: 'perdido', label: 'Perdido' },
  ];

  // ==========================
  // 🔁 Carrega leads do servidor
  // ==========================
  const loadLeads = async () => {
    try {
      setLoading(true);
      const data = await api.getLeads();
      setAllLeads(data);

      // 🔒 Filtra conforme o papel do usuário
      let filtered = data;

      if (user.role === 'vendedor') {
        // Vendedor: apenas os próprios leads
        filtered = data.filter((l) => l.assigned_to === user.id);
      } else if (user.role === 'gestor') {
        // Gestor: apenas leads da equipe (usa team_id se houver)
        filtered = data.filter((l) => l.team_id === user.team_id);
      }
      setLeads(filtered);
    } catch (err) {
      console.error('Erro ao carregar leads:', err);
      toast.error('❌ Erro ao carregar leads');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, []);

  // ==========================
  // 🎯 Arrastar e soltar
  // ==========================
  const handleDragStart = (lead) => setDraggedLead(lead);

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = async (status) => {
    if (!draggedLead || draggedLead.status === status) return;

    // 🚫 Vendedor não pode mover leads que não são dele
    if (user.role === 'vendedor' && draggedLead.assigned_to !== user.id) {
      toast.warn('🚫 Você não pode mover leads de outros vendedores.');
      return;
    }

    try {
      await api.updateLeadStatus(draggedLead.id, status);
      setLeads((prev) =>
        prev.map((l) => (l.id === draggedLead.id ? { ...l, status } : l))
      );
      toast.success(`✅ Lead movido para ${status}`);
    } catch (err) {
      console.error('Erro ao atualizar status:', err);
      toast.error('❌ Erro ao mover lead');
    } finally {
      setDraggedLead(null);
    }
  };

  // ==========================
  // 📦 Renderiza colunas
  // ==========================
  const renderColumn = (stage) => {
    const stageLeads = leads.filter((lead) => lead.status === stage.key);

    return (
      <div
        key={stage.key}
        className="kanban-column"
        onDragOver={handleDragOver}
        onDrop={() => handleDrop(stage.key)}
      >
        <div className="kanban-column-header">
          <span>{stage.label}</span>
          <span>{stageLeads.length}</span>
        </div>

        <div className="kanban-list">
          {loading ? (
            <p style={{ color: '#8696a0', padding: '10px' }}>Carregando...</p>
          ) : stageLeads.length === 0 ? (
            <div className="empty">Nenhum lead</div>
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
  // 🧱 Render principal
  // ==========================
  return (
    <div className="kanban-board">
      {stages.map(renderColumn)}

      {selectedLead && (
        <LeadModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onOpenChat={(lead) => {
            setSelectedLead(null);
            console.log('🟢 Abrir lead no chat:', lead);
          }}
        />
      )}
    </div>
  );
}

// ==============================
// 💳 Componente LeadCard
// ==============================
function LeadCard({ lead, onDragStart, onSelect, user }) {
  const isDraggable = user.role !== 'vendedor' || lead.assigned_to === user.id;

  return (
    <div
      className={`kanban-card ${!isDraggable ? 'blocked' : ''}`}
      draggable={isDraggable}
      onDragStart={isDraggable ? onDragStart : undefined}
      onClick={() => onSelect(lead)}
      title={
        !isDraggable
          ? 'Este lead pertence a outro vendedor.'
          : 'Arraste para mudar o status.'
      }
    >
      <div className="lead-card-header">
        <span className="lead-id">#{lead.id}</span>
        <span className={`status-badge ${lead.status}`}>{lead.status}</span>
      </div>

      <div className="lead-card-body">
        <strong>{lead.name || lead.phone}</strong>
        <p>{lead.phone}</p>
        {lead.city && <small>📍 {lead.city}</small>}
      </div>
    </div>
  );
}
