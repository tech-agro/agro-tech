# Agro Tech

Setup inicial com Streamlit + PostgreSQL e migrações SQL versionadas.

## Subir tudo com Docker

1. Ajuste o `.env` (ou copie do exemplo):

```bash
cp .env.example .env
```

1. Suba os containers:

```bash
docker compose up --build
```

O fluxo de inicialização é:

- `db`: sobe o PostgreSQL
- `migrator`: aplica as migrações em `migrations/` na ordem
- `app`: sobe o Streamlit após migração concluída
- `pgadmin`: interface web para acessar o PostgreSQL

Para recriar o banco do zero:

```bash
docker compose down -v
docker compose up -d --build
```

## Acessar aplicação

- Streamlit: [http://localhost:8501](http://localhost:8501)
- pgAdmin: [http://localhost:5050](http://localhost:5050)

Login no pgAdmin (valores do `.env`):

- Email: `admin@agrotech.com`
- Senha: `admin123`

O servidor **Agro Tech** já vem pré-cadastrado (via `config/pgadmin/servers.json`).
Após login, expanda no painel esquerdo:

`Servers → Agro Tech → Databases → agro_tech → Schemas → public → Tables`

Se o servidor não aparecer (volume antigo do pgAdmin), recrie só o pgAdmin:

```bash
docker compose rm -sf pgadmin
docker volume rm agro-tech_pgadmin_data
docker compose up -d pgadmin
```



## Acessar PostgreSQL

- Host: `localhost`
- Porta: `5432`
- Banco: valor de `POSTGRES_DB` no `.env`
- Usuário: valor de `POSTGRES_USER` no `.env`
- Senha: valor de `POSTGRES_PASSWORD` no `.env`

Via terminal local:

```bash
psql -h localhost -p 5432 -U postgres -d agro_tech
```

Via container:

```bash
docker compose exec db psql -U postgres -d agro_tech
```



## Migrações

- As migrações SQL ficam em `migrations/`
- Cada arquivo `.sql` é incremental e versionado
- O controle de execução fica na tabela `schema_migrations`
- A evolução do schema deve ser feita apenas por novas migrações

