import { useCallback, useEffect, useState } from "react";

import { ErroApi } from "../api/cliente";

/** Busca dados ao montar (e quando `deps` mudam), com estado de carga e erro. */
export function useCarregar<T>(buscar: () => Promise<T>, deps: readonly unknown[]) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState<ErroApi | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [versao, setVersao] = useState(0);

  // `deps` decide quando buscar de novo (a funcao muda a cada render)
  const buscarMemo = useCallback(buscar, deps);

  useEffect(() => {
    let ativo = true;
    setCarregando(true);
    setErro(null);
    buscarMemo()
      .then((resultado) => {
        if (ativo) setDados(resultado);
      })
      .catch((e: unknown) => {
        if (ativo) setErro(e instanceof ErroApi ? e : new ErroApi(0, null));
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [buscarMemo, versao]);

  const recarregar = useCallback(() => setVersao((v) => v + 1), []);
  return { dados, setDados, erro, carregando, recarregar };
}
