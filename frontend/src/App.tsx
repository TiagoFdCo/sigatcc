import { BrowserRouter, Route, Routes } from "react-router-dom";

import { ProvedorAuth } from "./auth/AuthContext";
import { RotaProtegida } from "./auth/RotaProtegida";
import { Layout } from "./componentes/Layout";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { NaoEncontrada } from "./paginas/NaoEncontrada";

export function App() {
  return (
    <ProvedorAuth>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Inicio />} />
              <Route path="*" element={<NaoEncontrada />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ProvedorAuth>
  );
}
