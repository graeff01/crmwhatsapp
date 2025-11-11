import React from 'react';
import '../styles/components/TagBadge.css';

/**
 * Badge de tag com cor personalizada
 */
const TagBadge = ({ tag, onRemove, small = false }) => {
  return (
    <span 
      className={`tag-badge ${small ? 'tag-badge-small' : ''}`}
      style={{ 
        backgroundColor: tag.color,
        borderColor: tag.color
      }}
    >
      {tag.icon && <span className="tag-icon">{tag.icon}</span>}
      <span className="tag-name">{tag.name}</span>
      {onRemove && (
        <button
          className="tag-remove"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(tag.id);
          }}
          title="Remover tag"
        >
          ×
        </button>
      )}
    </span>
  );
};

export default TagBadge;