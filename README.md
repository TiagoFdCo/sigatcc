# SIGATCC: ambiente de desenvolvimento (B3 + B4)

Pacote com a infraestrutura do B3 (Git, CI, Docker) e o esquema do banco do B4
(models Django, migrations e testes). A estrutura do projeto Django ja esta criada.

## Estrutura

```
sigatcc/
├── .github/workflows/ci.yml        # lint, migrations em dia, testes (cobertura >= 70%)
├── backend/                        # Django + DRF
│   ├── core/models.py              # 20 tabelas do DER (B4)
│   ├── core/migrations/            # a 0001 e gerada no passo 5
│   ├── core/migrations_extra/      # 0002 (cursos) e 0003 (logs so de acrescimo)
│   ├── core/tests/                 # testes das restricoes do banco
│   ├── sigatcc/                    # settings, urls (/saude/), wsgi, asgi
│   ├── manage.py, pytest.ini, .coveragerc, conftest.py
│   ├── Dockerfile, requirements.txt
├── frontend/                       # React (Vite): ainda a criar
├── nginx/prod.conf                 # proxy reverso de producao
├── scripts/nova-branch.sh          # branch no padrao feature/<ID>-<descricao>
├── scripts/b4-migrations.sh        # gera e aplica as migrations do B4
├── docker-compose.yml              # base (producao, banco gerenciado)
├── docker-compose.override.yml     # desenvolvimento (banco local, runserver)
├── .pre-commit-config.yaml, .env.example, .gitignore
```

## Tutorial de execucao (desenvolvimento)

Pre-requisitos: Git, Docker com Docker Compose v2 (`docker compose version`) e uma conta no GitHub.

### 1. Configurar o ambiente

```bash
cd sigatcc
cp .env.example .env
```

Abra o `.env` e troque `DB_PASSWORD`, `DJANGO_SECRET_KEY` e `JWT_SIGNING_KEY` por valores seus.
Em desenvolvimento deixe `DJANGO_DEBUG=True`. O `.env` nunca vai para o Git.

### 2. Construir a imagem do backend

```bash
docker compose build backend
```

### 3. Subir o banco

```bash
docker compose up -d db
docker compose ps        # o servico db deve ficar "healthy"
```

### 4. Gerar e aplicar as migrations do B4

```bash
./scripts/b4-migrations.sh
```

O script faz, nesta ordem:
1. cria `backend/core/migrations/0001_initial.py` a partir dos models (as 20 tabelas e as restricoes);
2. copia `0002_seed_cursos.py` e `0003_logs_somente_acrescimo.py` de `migrations_extra/` para `migrations/`;
3. roda `migrate`.

A `0001` precisa existir antes da `0002` e da `0003`, porque elas dependem dela. Por isso as duas ficam
em `migrations_extra/` ate o passo 2 do script.

Se o Linux reclamar de permissao nos arquivos gerados (o container cria como root):
`sudo chown -R $USER:$USER backend/core/migrations`.

### 5. Conferir o banco

```bash
docker compose exec db psql -U sigatcc_user -d sigatcc -c '\dt'
docker compose exec db psql -U sigatcc_user -d sigatcc -c 'SELECT nome FROM curso;'
```

Use o `DB_USER` e o `DB_NAME` do seu `.env`. A primeira consulta deve listar as 20 tabelas do DER
(mais as do Django, como `django_migrations` e `auth_*`). A segunda deve mostrar os 3 cursos.

Para ver o trigger dos logs funcionando:

```bash
docker compose exec db psql -U sigatcc_user -d sigatcc -c "UPDATE log_acesso SET ip = '1.1.1.1';"
```

Com a tabela vazia o comando nao altera nada. Os testes do passo 7 cobrem o caso com dados.

### 6. Subir a API

```bash
docker compose up -d backend
curl http://localhost:8000/saude/        # {"status": "ok"}
docker compose logs -f backend           # para acompanhar
```

Criar o primeiro administrador:

```bash
docker compose exec backend python manage.py createsuperuser
```

O comando pergunta e-mail, nome completo, tipo de usuario (digite `ADMINISTRADOR`) e senha.

### 7. Rodar os testes

```bash
docker compose run --rm backend pytest --cov=. --cov-fail-under=70
```

Os testes verificam as restricoes do banco: um TCC ativo por aluno e curso, coorientador diferente
do orientador, motivos obrigatorios, uma banca por TCC, participante unico na banca, suplente que
substituiu, um token por membro externo e banca, e logs somente de acrescimo. Para rodar so um arquivo:
`docker compose run --rm backend pytest core/tests/test_modelo.py -v`.

### 8. Subir no GitHub

```bash
git init
git add .
git commit -m "chore: estrutura inicial, infraestrutura (B3) e esquema do banco (B4)"
git branch -M main
git remote add origin <url-do-repositorio>
git push -u origin main
```

Inclua `backend/core/migrations/0001_initial.py`, `0002` e `0003` no commit. O CI confere se as
migrations estao em dia com os models (`makemigrations --check`).

### 9. Hooks de pre-commit e branches

```bash
pip install pre-commit
pre-commit install
./scripts/nova-branch.sh B5 login-docente
```

O hook de testes precisa de um PostgreSQL acessivel e das variaveis do `.env` no ambiente da maquina.
Se atrapalhar, comente o hook `pytest-check` no `.pre-commit-config.yaml` e deixe os testes para o CI.

### 10. Criar o frontend (quando for a hora)

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

Defina no `package.json` o script `"test": "vitest run"` (instale o `vitest`) e o script `"lint"`.
O CI pula as etapas do frontend enquanto nao houver `frontend/package-lock.json`.
Para subir o frontend pelo Docker: `docker compose --profile frontend up -d --build`.

## Configurar o GitHub (uma vez, por quem administra o repositorio)

### Secrets (Settings → Secrets and variables → Actions)
O CI atual nao precisa de secrets: ele usa um PostgreSQL descartavel e chaves de teste.
Quando o deploy for automatizado, acrescente `RESEND_API_KEY`, `DJANGO_SECRET_KEY`,
`JWT_SIGNING_KEY` e a `DATABASE_URL` de producao.

### Branch protection (Settings → Branches → Add rule, para `main`)
- Require a pull request before merging
- Require approvals: 1
- Require status checks to pass before merging → `backend`, `frontend` e `docker-build-check`
  (so aparecem na lista depois que o workflow rodar uma vez)
- Require branches to be up to date before merging

Isso aplica o RNF11 (cobertura >= 70% e 100% dos PRs revisados) como regra tecnica.

## Producao (droplet DigitalOcean)

Em producao o banco e o PostgreSQL gerenciado da DigitalOcean, nao um container.

1. No droplet, crie o `.env` com `DJANGO_DEBUG=False`, a `DJANGO_SECRET_KEY` real,
   `DJANGO_ALLOWED_HOSTS=api.sigatcc.com.br`, `CORS_ALLOWED_ORIGINS=https://app.sigatcc.com.br`
   e a `DATABASE_URL` do banco gerenciado (com `?sslmode=require`).
2. Aplique as migrations:
   ```bash
   docker compose -f docker-compose.yml run --rm backend python manage.py migrate
   ```
3. Suba os servicos (o `-f docker-compose.yml` ignora o arquivo de desenvolvimento):
   ```bash
   docker compose -f docker-compose.yml --profile prod up -d --build
   ```
   Com o frontend criado, acrescente `--profile frontend`.
4. Ajuste `nginx/prod.conf` para os dominios reais. O TLS (certbot) entra depois que o DNS propagar.

O trigger da migration `0003` so existe em PostgreSQL. O banco gerenciado da DigitalOcean aceita
`CREATE FUNCTION` e `CREATE TRIGGER` para o usuario dono do banco.

## Problemas comuns

| Sintoma | Causa e solucao |
| --- | --- |
| `NodeNotFoundError ... 0001_initial` | `0002` ou `0003` esta em `migrations/` sem a `0001`. Mova-as para `migrations_extra/` e rode o script de novo. |
| `RuntimeError: Defina DJANGO_SECRET_KEY` | O `.env` esta sem a chave e `DJANGO_DEBUG` nao esta `True`. |
| `connection refused` ao conectar no banco | O `db` ainda nao esta `healthy`. Rode `docker compose ps` e aguarde. |
| `unexpected keyword argument 'condition'` | Django abaixo de 5.1. Confira `requirements.txt` e rode `docker compose build --no-cache backend`. |
| Trigger falha em ambiente de teste com SQLite | A `0003` e so para PostgreSQL. Rode os testes no PostgreSQL. |
