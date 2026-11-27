import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProvedorAuth, useAuth } from "./auth/AuthContext";
import { RotaProtegida } from "./auth/RotaProtegida";
import { Layout } from "./componentes/Layout";
import { AcessoExterno } from "./paginas/AcessoExterno";
import { Auditoria } from "./paginas/Auditoria";
import { BancaFormulario } from "./paginas/BancaFormulario";
import { BuscarOrientador } from "./paginas/BuscarOrientador";
import { Convites } from "./paginas/Convites";
import { DashboardIndicadoresView } from "./paginas/DashboardIndicadoresView";
import { Login } from "./paginas/Login";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { PerfilAluno } from "./paginas/PerfilAluno";
import { ResponderConvite } from "./paginas/ResponderConvite";
import { Solicitacoes } from "./paginas/Solicitacoes";
import { TccDetalhe } from "./paginas/TccDetalhe";
import { TccFormulario } from "./paginas/TccFormulario";
import { TccLista } from "./paginas/TccLista";
import { rotaInicial } from "./util/rotas";
import AvaliacaoBanca from './paginas/AvaliacaoBanca';

/** Pagina inicial depende do perfil: o aluno abre o proprio perfil (C2a). */
function Inicio() {
  const { usuario } = useAuth();
  return <Navigate to={rotaInicial(usuario?.tipo_usuario)} replace />;
}

export function App() {
  return (
    <ProvedorAuth>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* C6: rota publica do link do convite (o membro externo nao tem login) */}
          <Route path="/convites/responder" element={<ResponderConvite />} />
          {/* C16: leitura do TCC pelo membro externo, pelo token do e-mail */}
          <Route path="/acesso-externo/:token" element={<AcessoExterno />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Inicio />} />
              <Route path="/meu-perfil" element={<PerfilAluno />} />
              <Route path="/tccs" element={<TccLista />} />
              <Route path="/indicadores" element={<DashboardIndicadoresView />} />
              <Route path="/tccs/novo" element={<TccFormulario />} />
              <Route path="/tccs/:id" element={<TccDetalhe />} />
              <Route path="/tccs/:id/editar" element={<TccFormulario />} />
              <Route path="/tccs/:id/banca/nova" element={<BancaFormulario />} />
              <Route path="/orientadores" element={<BuscarOrientador />} />
              <Route path="/solicitacoes" element={<Solicitacoes />} />
              <Route path="/convites" element={<Convites />} />
              <Route path="/auditoria" element={<Auditoria />} />
              <Route path="*" element={<NaoEncontrada />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ProvedorAuth>
  );
}
