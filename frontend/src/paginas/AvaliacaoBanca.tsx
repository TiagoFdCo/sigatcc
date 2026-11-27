import { useState } from 'react';
import type { FormEvent } from 'react';
import Alerta from '../componentes/Alerta';
import { useCarregar } from '../hooks/useCarregar';
import { clienteApi } from '../servicos/api';

export interface DadosBancaAvaliacao {
  bancaId: number;
  tituloTcc: string;
  autorNome: string;
  orientadorNome: string;
  dataHoraInicio: string;
  tipoLocal: 'PRESENCIAL' | 'REMOTO';
  localInfo: string;
}

export interface AvaliacaoMembroPayload {
  bancaId: number;
  nota: number | null;
  parecer: string;
  isRascunho: boolean;
}

// Mock inicial até a integração final da rota de detalhe da banca
const BANCA_MOCK: DadosBancaAvaliacao = {
  bancaId: 1,
  tituloTcc: 'Desenvolvimento e Validação do Sistema SIGATCC',
  autorNome: 'Anggelo Cardozo',
  orientadorNome: 'Prof. Dr. Otávio Rios',
  dataHoraInicio: '2026-11-27T14:00:00Z',
  tipoLocal: 'PRESENCIAL',
  localInfo: 'Escola Superior de Tecnologia (EST) - Bloco A, Sala 102',
};

export default function AvaliacaoBanca() {
  const [nota, setNota] = useState<string>('');
  const [parecer, setParecer] = useState<string>('');
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [erroForm, setErroForm] = useState<string | null>(null);

  const { carregando, erro: erroCarregamento } = useCarregar(async () => {
    // Futuro: const resposta = await clienteApi.get(`/bancas/${id}`);
    return BANCA_MOCK;
  }, []);

  const validarNota = (): boolean => {
    const valorNota = parseFloat(nota);
    if (isNaN(valorNota) || valorNota < 0 || valorNota > 10) {
      setErroForm('Informe uma nota válida entre 0,0 e 10,0.');
      return false;
    }
    setErroForm(null);
    return true;
  };

  const handleSubmit = async (isRascunho: boolean, e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!isRascunho && !validarNota()) return;

    const valorNota = parseFloat(nota);
    const payload: AvaliacaoMembroPayload = {
      bancaId: BANCA_MOCK.bancaId,
      nota: isNaN(valorNota) ? null : valorNota,
      parecer,
      isRascunho,
    };

    try {
      // Futuro: await clienteApi.post(`/bancas/${BANCA_MOCK.bancaId}/avaliacoes`, payload);
      console.log('Submetendo avaliação:', payload);

      setMensagemSucesso(
        isRascunho
          ? 'Rascunho da avaliação salvo com sucesso!'
          : 'Avaliação da banca registrada com sucesso!'
      );
    } catch {
      setErroForm('Erro ao salvar a avaliação. Tente novamente.');
    }
  };

  if (carregando) {
    return <div className="container">Carregando dados da banca...</div>;
  }

  return (
    <div className="container">
      <h1>Avaliação da Banca Examinadora</h1>

      {erroCarregamento && <Alerta tipo="erro" mensagem={erroCarregamento} />}
      {erroForm && <Alerta tipo="erro" mensagem={erroForm} />}
      {mensagemSucesso && <Alerta tipo="sucesso" mensagem={mensagemSucesso} />}

      {/* Resumo do TCC e da Banca */}
      <div className="card">
        <h2>{BANCA_MOCK.tituloTcc}</h2>
        <div className="grid-2-col">
          <p>
            <strong>Autor(a):</strong> {BANCA_MOCK.autorNome}
          </p>
          <p>
            <strong>Orientador(a):</strong> {BANCA_MOCK.orientadorNome}
          </p>
          <p>
            <strong>Data/Hora:</strong>{' '}
            {new Date(BANCA_MOCK.dataHoraInicio).toLocaleString('pt-BR')}
          </p>
          <p>
            <strong>Local:</strong> {BANCA_MOCK.localInfo}
          </p>
        </div>
      </div>

      {/* Formulário de Avaliação */}
      <div className="card">
        <h3>Formulário de Lançamento de Nota</h3>

        <form onSubmit={(e) => handleSubmit(false, e)}>
          <div className="campo-form">
            <label htmlFor="input-nota">
              Nota Final da Defesa (0,0 a 10,0) <span className="obrigatorio">*</span>
            </label>
            <input
              id="input-nota"
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              placeholder="Ex: 9.5"
              className="input-texto"
            />
          </div>

          <div className="campo-form">
            <label htmlFor="textarea-parecer">
              Parecer Descritivo / Considerações do Avaliador
            </label>
            <textarea
              id="textarea-parecer"
              rows={5}
              value={parecer}
              onChange={(e) => setParecer(e.target.value)}
              placeholder="Digite aqui as considerações sobre o trabalho e a apresentação..."
              className="input-textarea"
            />
          </div>

          <div className="acoes-form">
            <button
              type="button"
              className="btn-secundario"
              onClick={() => handleSubmit(true)}
            >
              Salvar Rascunho
            </button>
            <button type="submit" className="btn-primario">
              Finalizar Avaliação
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
