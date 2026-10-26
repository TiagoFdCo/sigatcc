import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { aoExpirarSessao, api, guardarTokens, tokensAtuais } from "../api/cliente";
import type { RespostaLogin, UsuarioLogado } from "../api/tipos";

type ValorAuth = {
  usuario: UsuarioLogado | null;
  carregando: boolean;
  entrar: (login: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  /** Docente e administrador cadastram e editam; secretaria so le (RBN55). */
  podeEditar: boolean;
};

const ContextoAuth = createContext<ValorAuth | null>(null);

export function ProvedorAuth({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioLogado | null>(null);
  const [carregando, setCarregando] = useState(() => tokensAtuais() !== null);

  useEffect(() => {
    aoExpirarSessao(() => setUsuario(null));
    if (tokensAtuais()) {
      api<UsuarioLogado>("/auth/me/")
        .then(setUsuario)
        .catch(() => guardarTokens(null))
        .finally(() => setCarregando(false));
    }
    return () => aoExpirarSessao(null);
  }, []);

  const entrar = useCallback(async (login: string, senha: string) => {
    const resposta = await api<RespostaLogin>("/auth/login/", {
      metodo: "POST",
      corpo: { login, senha },
    });
    guardarTokens({ access: resposta.access, refresh: resposta.refresh });
    setUsuario(resposta.usuario);
  }, []);

  const sair = useCallback(async () => {
    const tokens = tokensAtuais();
    if (tokens) {
      await api("/auth/logout/", { metodo: "POST", corpo: { refresh: tokens.refresh } }).catch(() => undefined);
    }
    guardarTokens(null);
    setUsuario(null);
  }, []);

  const valor = useMemo<ValorAuth>(
    () => ({
      usuario,
      carregando,
      entrar,
      sair,
      podeEditar: usuario?.tipo_usuario === "DOCENTE" || usuario?.tipo_usuario === "ADMINISTRADOR",
    }),
    [usuario, carregando, entrar, sair],
  );

  return <ContextoAuth.Provider value={valor}>{children}</ContextoAuth.Provider>;
}

export function useAuth(): ValorAuth {
  const valor = useContext(ContextoAuth);
  if (!valor) throw new Error("useAuth precisa estar dentro de <ProvedorAuth>");
  return valor;
}
