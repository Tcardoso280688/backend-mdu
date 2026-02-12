
# Backend MDU (Flask API)

API em **Python/Flask** para gestão de projetos MDU com autenticação **JWT**, logs de movimentação, workflow e camadas **técnica/comercial/admin**.

## Endpoints principais

Autenticação (JSON):
- `POST /api/auth/login` → `{ email, senha }` → `{ access_token }`
- `GET  /api/auth/me` (autenticado)

Usuários (admin):
- `POST /api/users` → cria usuário (admin/tecnico/comercial)
- `GET  /api/users`  → lista usuários

Projetos:
- `GET  /api/projects` → lista (filtros por status)
- `POST /api/projects` → cria
- `GET  /api/projects/<id>` → detalhes
- `PUT  /api/projects/<id>` → atualiza
- `DELETE /api/projects/<id>` → remove (admin)
- `POST /api/projects/<id>/transition` → muda status e gera log (workflow)

Logs:
- `GET /api/logs?project_id=<id>` → lista logs

## Como rodar local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env se quiser
python wsgi.py
```
Abra: http://localhost:5000/health  (deve retornar `ok`).

Faça login:
- email: `admin@mdu.com`
- senha: `123456`

## Deploy no Railway

1. Crie um repositório no GitHub e envie estes arquivos.
2. Em [Railway.app](https://railway.app), **New → Deploy from GitHub**.
3. Em **Variables**, configure (copie de `.env.example`):
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`
   - `DATABASE_URL` (Supabase com `?sslmode=require`)
   - `NETLIFY_ORIGIN` (ex.: `https://quebrarsc.netlify.app`)
   - `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_ROLE`
4. Railway detecta o `Procfile` e roda o `gunicorn` (porta é fornecida pela variável `PORT`).
5. Teste: `GET https://<sua-app>.up.railway.app/health`

## Banco (Supabase)

Use a connection string do Supabase (Postgres), ex:
```
postgresql://USER:PASSWORD@HOST:6543/postgres?sslmode=require
```
As tabelas são criadas automaticamente no primeiro start (SQLAlchemy `create_all`).

## CORS

O CORS libera `NETLIFY_ORIGIN` (do `.env`) para o frontend no Netlify.

