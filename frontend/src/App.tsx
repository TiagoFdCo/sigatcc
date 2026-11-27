import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import DashboardCoordenador from './paginas/DashboardCoordenador';
import DashboardDocente from './paginas/DashboardDocente';
import DashboardAluno from './paginas/DashboardAluno';
import FormularioTcc from './paginas/FormularioTcc';
import DetalheTcc from './paginas/DetalheTcc';
import BancasRelatorio from './paginas/BancasRelatorio';
import FormularioBanca from './paginas/FormularioBanca';
import MinhasBancasDocente from './paginas/MinhasBancasDocente';
import { Convites } from './paginas/Convites';
import { Login } from './paginas/Login';
import Solicitacoes from './paginas/Solicitacoes';
import Perfil from './paginas/Perfil';
import { ResponderConvite } from './paginas/ResponderConvite';
import { NaoEncontrada } from './paginas/NaoEncontrada';
import Relatorios from './paginas/Relatorios';
import { Auditoria } from './paginas/Auditoria';
import AvaliacaoBanca from './paginas/AvaliacaoBanca';

import { useAuth } from './contextos/AuthContexto';

function RedirecionarInicio() {
  const { usuario } = useAuth();
  return <Navigate to={usuario?.perfil ? `/${usuario.perfil}` : '/login'} replace />;
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/convites/responder" element={<ResponderConvite />} />

        <Route path="/" element={<RedirecionarInicio />} />
        <Route path="/aluno" element={<DashboardAluno />} />
        <Route path="/docente" element={<DashboardDocente />} />
        <Route path="/coordenador" element={<DashboardCoordenador />} />
        <Route path="/solicitacoes" element={<Solicitacoes />} />
        <Route path="/tccs/novo" element={<FormularioTcc />} />
        <Route path="/tccs/:id" element={<DetalheTcc />} />
        <Route path="/bancas" element={<BancasRelatorio />} />
        <Route path="/bancas/nova" element={<FormularioBanca />} />
        <Route path="/bancas/minhas" element={<MinhasBancasDocente />} />
        <Route path="/bancas/avaliacao" element={<AvaliacaoBanca />} />
        <Route path="/convites" element={<Convites />} />
        <Route path="/perfil" element={<Perfil />} />
        <Route path="/relatorios" element={<Relatorios />} />
        <Route path="/auditoria" element={<Auditoria />} />
        <Route path="*" element={<NaoEncontrada />} />
      </Routes>
    </BrowserRouter>
  );
}
