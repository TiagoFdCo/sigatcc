# SIGATCC · Frontend

SPA em React + TypeScript (Vite) que consome a API Django em `VITE_API_URL`.

## Rodar em desenvolvimento

Com Node 20 instalado:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev          # http://localhost:5173
```

Sem Node na máquina, pelo Docker (gera o mesmo `node_modules` e o `package-lock.json`):

```bash
docker run --rm -v "$PWD/frontend:/app" -w /app node:20-alpine npm install
docker compose --profile frontend up -d --build frontend   # http://localhost:5173
```

A API precisa estar no ar (`docker compose up -d backend`) e liberar a origem
`http://localhost:5173` em `CORS_ALLOWED_ORIGINS`.

## Scripts

| Comando | O que faz |
| --- | --- |
| `npm run dev` | Servidor de desenvolvimento com recarga automática |
| `npm run build` | Checa os tipos e gera `dist/` |
| `npx tsc --noEmit` | Só a checagem de tipos (a mesma do CI) |

## Organização

| Pasta | Conteúdo |
| --- | --- |
| `src/api/` | Cliente HTTP com JWT, tipos das respostas e leitura de erros do DRF |
| `src/auth/` | Contexto de sessão e rota protegida |
| `src/componentes/` | Layout e peças reutilizadas |
| `src/paginas/` | Uma tela por arquivo |
