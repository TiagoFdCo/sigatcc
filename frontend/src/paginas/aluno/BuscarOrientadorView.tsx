import React, { useEffect, useState } from 'react';
import { DocenteItem, AreaInteresse } from '../../api/tipos';
import { buscarDocentes, getAreasInteresse, solicitarOrientacao } from '../../api/orientacaoService';
import { DocenteCard } from '../../componentes/DocenteCard';

export const BuscarOrientadorView: React.FC = () => {
  const [docentes, setDocentes] = useState<DocenteItem[]>([]);
  const [areas, setAreas] = useState<AreaInteresse[]>([]);
  const [selectedArea, setSelectedArea] = useState('');
  const [busca, setBusca] = useState('');
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
      const data = await buscarDocentes(selectedArea, busca);
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
      alert(err?.message || 'Erro ao enviar solicitação.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="conteudo-principal">
      <header className="cabecalho-pagina">
        <h1>Buscar Orientador (C3a)</h1>
        <p>Pesquise professores por área de interesse e solicite orientação</p>
      </header>

      <div className="filtros-bar">
        <input
          type="text"
          placeholder="Nome do docente..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="campo-texto"
        />
        <select
          value={selectedArea}
          onChange={(e) => setSelectedArea(e.target.value)}
          className="campo-selecao"
        >
          <option value="">Todas as Áreas</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.nome}</option>
          ))}
        </select>
        <button onClick={handleSearch} className="botao">Pesquisar</button>
      </div>

      {loading ? (
        <div className="carregando">Buscando orientadores...</div>
      ) : (
        <div className="grid-cards">
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
        <div className="modal-fundo">
          <div className="modal-conteudo">
            <h2>Solicitar Orientação — {selectedDocente.nome}</h2>
            <form onSubmit={handleEnviarProposta}>
              <div className="campo-grupo">
                <label>Mensagem (Opcional)</label>
                <textarea
                  rows={4}
                  value={mensagem}
                  onChange={(e) => setMensagem(e.target.value)}
                  placeholder="Escreva uma mensagem de introdução ao professor..."
                  className="campo-texto"
                />
              </div>

              <div className="modal-acoes">
                <button type="button" onClick={() => setSelectedDocente(null)} className="botao-secundario">
                  Cancelar
                </button>
                <button type="submit" disabled={submitting} className="botao">
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
