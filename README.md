# SIGATCC — ambiente de desenvolvimento

Pacote de configuracao do B3 (Repositorio e Configuracao) da EAP: Git, CI e Docker.

## Estrutura

```
sigatcc/
├── .github/workflows/ci.yml   # pipeline de CI (lint + testes + cobertura >=70%)
├── backend/                   # Django + DRF
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                  # React (Vite)
│   ├── Dockerfile
│   └── nginx.conf
├── nginx/prod.conf            # proxy reverso de producao (CORS, origens separadas)
├── scripts/nova-branch.sh     # cria branch no padrao feature/<ID>-<descricao>
├── .pre-commit-config.yaml    # lint + testes rapidos antes de cada commit
├── .env.example                # variaveis necessarias (copiar para .env)
├── docker-compose.yml
└── .gitignore
```

## Primeiros passos

1. **Criar o repositorio no GitHub** (vazio, sem README) e dar push deste conteudo:
   ```bash
   cd sigatcc
   git init
   git add .
   git commit -m "chore: estrutura inicial do repositorio (B3)"
   git branch -M main
   git remote add origin <url-do-repositorio>
   git push -u origin main
   ```

2. **Criar os projetos Django e React dentro das pastas `backend/` e `frontend/`**
   (este pacote traz a configuracao de infraestrutura; o codigo das aplicacoes ainda
   precisa ser criado — `django-admin startproject sigatcc backend/` e
   `npm create vite@latest frontend -- --template react-ts`, por exemplo).

3. **Configurar o ambiente local:**
   ```bash
   cp .env.example .env
   # edite o .env com valores reais (nunca commitar esse arquivo)
   docker compose up --build
   ```
   - Backend em `http://localhost:8000`
   - Frontend em `http://localhost:5173`

4. **Instalar os hooks de pre-commit** (uma vez, por pessoa, apos clonar):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Criar uma branch nova para uma atividade da EAP:**
   ```bash
   ./scripts/nova-branch.sh B5 login-docente
   ```

## Configurar o GitHub (uma vez, por quem administra o repositorio)

### Secrets (Settings → Secrets and variables → Actions)
Nenhum secret e necessario so para o CI atual (ele usa um Postgres descartavel).
Quando o deploy for automatizado, adicionar: `RESEND_API_KEY`, `DJANGO_SECRET_KEY`,
`JWT_SIGNING_KEY`, `DB_PASSWORD` de producao.

### Branch protection (Settings → Branches → Add rule, aplicada a `main`)
- Require a pull request before merging
- Require approvals: 1
- Require status checks to pass before merging → selecionar `backend`, `frontend`
  e `docker-build-check` (so aparecem na lista depois que o workflow rodar ao
  menos uma vez no repositorio)
- Require branches to be up to date before merging (recomendado)

Isso implementa o RNF11 do plano de integracao (cobertura >=70%, 100% dos PRs
revisados) como regra tecnica, nao apenas combinada em texto.

## Producao (droplet DigitalOcean)

```bash
docker compose --profile prod up -d --build
```

O perfil `prod` tambem sobe o container `nginx`, que faz o proxy reverso para
`api.sigatcc.com.br` e `app.sigatcc.com.br` (editar `nginx/prod.conf` com os
dominios reais). TLS via certbot entra depois que o DNS estiver propagado.

## Mais contexto

O guia completo de GitHub Actions, com o workflow explicado linha a linha,
esta disponivel como documento a parte (gerado nesta mesma conversa).
