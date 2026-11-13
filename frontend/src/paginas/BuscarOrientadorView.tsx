import React, { useEffect, useState } from 'react';
import { DocenteItem, AreaInteresse } from '../../types/orientacao';
import { buscarDocentes, getAreasInteresse, solicitarOrientacao } from '../../services/orientacaoService';
import { DocenteCard } from '../../components/orientacao/DocenteCard';

export const BuscarOrientadorView: React.FC = () => {
  const [docentes, setDocentes] = useState<DocenteItem[]>([]);
  const [areas, setAreas] = useState<AreaInteresse[]>([]);
  const [selectedArea, setSelectedArea] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const [selectedDocente, setSelectedDocente] = useState<DocenteItem | null>(null);
  const [mensagem, setMensagem] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getAreasInteresse().then(setAreas).catch(console.error);
    handleSearch();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await buscarDocentes(selectedArea, search);
      setDocentes(data);
    } catch (err) {
      console.error('Erro ao buscar orientadores:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnviarProposta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocente) return;

    setSubmitting(true);
    try {
      await solicitarOrientacao(selectedDocente.id, mensagem);
      alert('Solicitação de orientação enviada com sucesso!');
      setSelectedDocente(null);
      setMensagem('');
    } catch (err: any) {
      alert(err?.message || 'Erro ao enviar solicitação de orientação.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container-pagina">
      <header className="header-pagina">
        <h1>Buscar Orientador (C3a)</h1>
        <p>Pesquise professores por área de interesse e solicite orientação</p>
      </header>

      <div className="filtros-bar">
        <input
          type="text"
          placeholder="Nome do docente..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="input-search"
        />
        <select
          value={selectedArea}
          onChange={(e) => setSelectedArea(e.target.value)}
          className="select-filtro"
        >
          <option value="">Todas as Áreas</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.nome}</option>
          ))}
        </select>
        <button onClick={handleSearch} className="btn-primary">Pesquisar</button>
      </div>

      {loading ? (
        <div className="loading">Buscando orientadores...</div>
      ) : (
        <div className="grid-docentes">
          {docentes.map((docente) => (
            <DocenteCard
              key={docente.id}
              docente={docente}
              onSolicitar={(d) => setSelectedDocente(d)}
            />
          ))}
        </div>
      )}

      {selectedDocente && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Solicitar Orientação — {selectedDocente.nome}</h2>
            <form onSubmit={handleEnviarProposta}>
              <div className="form-group">
                <label>Mensagem (Opcional)</label>
                <textarea
                  rows={4}
                  value={mensagem}
                  onChange={(e) => setMensagem(e.target.value)}
                  placeholder="Escreva uma breve mensagem de introdução ao professor..."
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setSelectedDocente(null)} className="btn-secondary">
                  Cancelar
                </button>
                <button type="submit" disabled={submitting} className="btn-primary">
                  {submitting ? 'Enviando...' : 'Enviar Solicitação'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
