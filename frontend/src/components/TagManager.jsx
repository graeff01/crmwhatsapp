import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TagBadge from './TagBadge';
import '../styles/components/Tagmanager.css';

/**
 * Modal para adicionar/remover tags de um lead
 */
const TagManager = ({ leadId, isOpen, onClose, onTagsUpdated }) => {
  const [allTags, setAllTags] = useState([]);
  const [leadTags, setLeadTags] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && leadId) {
      loadData();
    }
  }, [isOpen, leadId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tagsRes, leadTagsRes] = await Promise.all([
        axios.get('http://localhost:5000/api/tags', { withCredentials: true }),
        axios.get(`http://localhost:5000/api/leads/${leadId}/tags`, { withCredentials: true })
      ]);

      setAllTags(tagsRes.data);
      setLeadTags(leadTagsRes.data);
    } catch (error) {
      console.error('Erro ao carregar tags:', error);
      alert('Erro ao carregar tags');
    } finally {
      setLoading(false);
    }
  };

  const addTag = async (tagId) => {
    try {
      await axios.post(
        `http://localhost:5000/api/leads/${leadId}/tags`,
        { tag_id: tagId },
        { withCredentials: true }
      );

      await loadData();
      if (onTagsUpdated) onTagsUpdated();
      
      console.log('✅ Tag adicionada com sucesso');
    } catch (error) {
      console.error('Erro ao adicionar tag:', error);
      alert(error.response?.data?.error || 'Erro ao adicionar tag');
    }
  };

  const removeTag = async (tagId) => {
    try {
      await axios.delete(
        `http://localhost:5000/api/leads/${leadId}/tags/${tagId}`,
        { withCredentials: true }
      );

      await loadData();
      if (onTagsUpdated) onTagsUpdated();
      
      console.log('✅ Tag removida com sucesso');
    } catch (error) {
      console.error('Erro ao remover tag:', error);
      alert('Erro ao remover tag');
    }
  };

  const hasTag = (tagId) => {
    return leadTags.some(lt => lt.id === tagId);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content tag-manager-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🏷️ Gerenciar Tags</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading">Carregando tags...</div>
          ) : (
            <>
              {/* Tags do Lead */}
              <div className="section">
                <h4>Tags Atuais ({leadTags.length})</h4>
                {leadTags.length > 0 ? (
                  <div className="tags-list">
                    {leadTags.map(tag => (
                      <TagBadge
                        key={tag.id}
                        tag={tag}
                        onRemove={removeTag}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="empty-state">Nenhuma tag adicionada ainda</p>
                )}
              </div>

              {/* Tags Disponíveis */}
              <div className="section">
                <h4>Adicionar Tag</h4>
                <div className="tags-grid">
                  {allTags
                    .filter(tag => !hasTag(tag.id))
                    .map(tag => (
                      <div
                        key={tag.id}
                        className="tag-option"
                        onClick={() => addTag(tag.id)}
                        style={{ borderColor: tag.color }}
                      >
                        <TagBadge tag={tag} />
                        <span className="tag-description">{tag.description}</span>
                        <span className="tag-count">
                          {tag.usage_count} {tag.usage_count === 1 ? 'lead' : 'leads'}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

export default TagManager;