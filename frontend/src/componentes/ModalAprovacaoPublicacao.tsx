import React, { useState } from 'react';
import { submeterAprovacaoPublicacao } from '../api/publicacaoService';

interface ModalAprovacaoPublicacaoProps {
  tccId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const ModalAprovacaoPublicacao: React.FC<ModalAprovacaoPublicacaoProps> = ({
  tccId,
  onClose,
  onSuccess,
}) => {
  const [linkPublicacao, setLinkPublicacao] = useState('');
  const [comprovante, setComprovante] = useState<File | null>(null);
  const [observacoes, setObservacoes] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!linkPublicacao && !comprovante) {
      setErro('Forneça ao menos o link da publicação ou um arquivo de comprovante (D15).');
      return;
    }

    setEnviando(true);
    setErro('');

    try {
      await submeterAprovacaoPublicacao({
        tcc_id: tccId,
        link_publicacao: linkPublicacao || undefined,
        comprovante_file: comprovante || undefined,
        observacoes: observacoes || undefined,
      });
      alert('Solicitação de aprovação por publicação enviada com sucesso!');
      onSuccess();
    } catch (err: any) {
      setErro(err?.message || 'Erro ao submeter comprovante de publicação.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="modal-fundo">
      <div className="modal-conteudo">
        <h2>Aprovação por Publicação (C1 / D15)</h2>
        <p className="subtitulo">Submeta o link ou o comprovante do artigo aceito para aprovação direta do TCC.</p>

        {erro && <div className="alerta alerta-perigo">{erro}</div>}

        <form onSubmit={handleSubmit}>
          <div className="campo-grupo">
            <label>Link da Publicação / Periódico (Opcional)</label>
            <input
              type="url"
              value={linkPublicacao}
              onChange={(e) => setLinkPublicacao(e.target.value)}
              placeholder="https://doi.org/10.xxxx/xxxx"
              className="campo-texto"
            />
          </div>

          <div className="campo-grupo">
            <label>Comprovante em PDF / Imagem (Opcional)</label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setComprovante(e.target.files?.[0] || null)}
              className="campo-texto"
            />
          </div>

          <div className="campo-grupo">
            <label>Observações Adicionais</label>
            <textarea
              rows={3}
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              placeholder="Informações sobre o congresso, revista ou aceite do artigo..."
              className="campo-texto"
            />
          </div>

          <div className="modal-acoes">
            <button type="button" onClick={onClose} className="botao-secundario">
              Cancelar
            </button>
            <button type="submit" disabled={enviando} className="botao">
              {enviando ? 'Submetendo...' : 'Solicitar Aprovação'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
