import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import DashboardCoordenador from './pages/DashboardCoordenador';
import DashboardDocente from './pages/DashboardDocente';
import DashboardAluno from './pages/DashboardAluno';
import FormularioTcc from './pages/FormularioTcc';
import DetalheTcc from './pages/DetalheTcc';
import BancasRelatorio from './pages/BancasRelatorio';
import FormularioBanca from './pages/FormularioBanca';
import MinhasBancasDocente from './pages/MinhasBancasDocente';
import { Convites } from './pages/Convites';
import { Login } from './pages/Login';
import Solicitacoes from './pages/Solicitacoes';
import Perfil from './pages/Perfil';
import { ResponderConvite } from './pages/ResponderConvite';
import { NaoEncontrada } from './pages/NaoEncontrada';
import Relatorios from './pages/Relatorios';
import { Auditoria } from './pages/Auditoria';
import AvaliacaoBanca from './pages/AvaliacaoBanca';

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
