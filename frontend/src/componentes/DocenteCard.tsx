import React from 'react';
import { DocenteItem } from '../api/tipos';

interface DocenteCardProps {
  docente: DocenteItem;
  onSolicitar: (docente: DocenteItem) => void;
}

export const DocenteCard: React.FC<DocenteCardProps> = ({ docente, onSolicitar }) => {
  return (
    <div className="card-docente">
      <div className="card-header">
        <div>
          <h3>{docente.nome}</h3>
          <p className="subtext">{docente.departamento} — {docente.email}</p>
        </div>
        <span className={`tag ${docente.aceita_orientacoes ? 'tag-sucesso' : 'tag-perigo'}`}>
          {docente.aceita_orientacoes ? `${docente.qtd_orientacoes} orientandos` : 'Sem vagas'}
        </span>
      </div>

      {docente.areas && docente.areas.length > 0 && (
        <div className="areas-container">
          <p className="label">Áreas de Interesse:</p>
          <div className="tags">
            {docente.areas.map((area) => (
              <span key={area.id} className="tag">{area.nome}</span>
            ))}
          </div>
        </div>
      )}

      <div className="card-actions">
        <button
          onClick={() => onSolicitar(docente)}
          disabled={!docente.aceita_orientacoes}
          className="botao"
        >
          Solicitar Orientação
        </button>
      </div>
    </div>
  );
};
