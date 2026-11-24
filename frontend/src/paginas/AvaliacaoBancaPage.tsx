import React, { useState } from 'react';
import { AvaliacaoMembroPayload, DadosBancaAvaliacao } from '../types/avaliacao';

// Mock de dados até a rota de detalhe da banca estar integrada
const BANCA_MOCK: DadosBancaAvaliacao = {
  bancaId: 1,
  tituloTcc: 'Desenvolvimento e Validação do Sistema SIGATCC',
  autorNome: 'Anggelo Cardozo',
  orientadorNome: 'Prof. Dr. Otávio Rios',
  dataHoraInicio: '2026-11-25T14:00:00Z',
  tipoLocal: 'PRESENCIAL',
  localInfo: 'Escola Superior de Tecnologia (EST) - Bloco A, Sala 102',
};

export const AvaliacaoBancaPage: React.FC = () => {
  const [notaApresentacao, setNotaApresentacao] = useState<string>('');
  const [notaEscrita, setNotaEscrita] = useState<string>('');
  const [parecer, setParecer] = useState<string>('');
  const [erro, setErro] = useState<string | null>(null);

  // Média simples do membro (Apresentação + Escrita) / 2
  const numApres = parseFloat(notaApresentacao);
  const numEscrita = parseFloat(notaEscrita);
  const mediaValida = !isNaN(numApres) && !isNaN(numEscrita) && numApres >= 0 && numApres <= 10 && numEscrita >= 0 && numEscrita <= 10;
  const mediaMembro = mediaValida ? ((numApres + numEscrita) / 2).toFixed(2) : '--';

  const validarCampos = (): boolean => {
    if (!mediaValida) {
      setErro('Insira notas válidas entre 0.0 e 10.0 para ambos os critérios.');
      return false;
    }
    setErro(null);
    return true;
  };

  const handleSubmit = (isRascunho: boolean) => {
    if (!isRascunho && !validarCampos()) return;

    const payload: AvaliacaoMembroPayload = {
      bancaId: BANCA_MOCK.bancaId,
      notaApresentacao: isNaN(numApres) ? null : numApres,
      notaEscrita: isNaN(numEscrita) ? null : numEscrita,
      parecer,
      isRascunho,
    };

    console.log(isRascunho ? 'Salvando rascunho...' : 'Submetendo avaliação...', payload);
    alert(isRascunho ? 'Rascunho salvo com sucesso!' : 'Avaliação enviada com sucesso!');
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-2xl font-bold mb-4">Avaliação da Banca Examinadora (7.2)</h1>

      {/* Header com dados do TCC */}
      <div className="bg-white shadow rounded-lg p-6 mb-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800">{BANCA_MOCK.tituloTcc}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-sm text-gray-600">
          <p><strong>Autor(a):</strong> {BANCA_MOCK.autorNome}</p>
          <p><strong>Orientador(a):</strong> {BANCA_MOCK.orientadorNome}</p>
          <p><strong>Data/Hora:</strong> {new Date(BANCA_MOCK.dataHoraInicio).toLocaleString('pt-BR')}</p>
          <p><strong>Local:</strong> {BANCA_MOCK.localInfo}</p>
        </div>
      </div>

      {/* Formutário de Notas */}
      <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Lançamento de Notas</h3>

        {erro && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
            {erro}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nota da Apresentação Oral (0.0 a 10.0)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={notaApresentacao}
              onChange={(e) => setNotaApresentacao(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: 9.5"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nota do Trabalho Escrito (0.0 a 10.0)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={notaEscrita}
              onChange={(e) => setNotaEscrita(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: 9.0"
            />
          </div>
        </div>

        {/* Parecer Descritivo */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Parecer / Considerações do Avaliador
          </label>
          <textarea
            rows={4}
            value={parecer}
            onChange={(e) => setParecer(e.target.value)}
            className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Digite aqui as considerações sobre a defesa e o documento..."
          />
        </div>

        {/* Resumo da Média do Membro */}
        <div className="bg-gray-50 p-4 rounded-md mb-6 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Sua Média Individual Calculada:</span>
          <span className="text-2xl font-bold text-blue-600">{mediaMembro}</span>
        </div>

        {/* Botões de Ação */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => handleSubmit(true)}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Salvar Rascunho
          </button>
          <button
            type="button"
            onClick={() => handleSubmit(false)}
            className="px-4 py-2 bg-blue-600 rounded-md text-sm font-medium text-white hover:bg-blue-700"
          >
            Finalizar Avaliação
          </button>
        </div>
      </div>
    </div>
  );
};
