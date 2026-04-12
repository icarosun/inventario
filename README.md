# Inventario

Projeto Django para inventario interno de TI e Logistica.

## Desenvolvimento

1. Copie o arquivo de ambiente:

   ```bash
   cp .env.example .env
   ```

2. Suba apenas o banco PostgreSQL:

   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

3. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Instale as dependencias:

   ```bash
   pip install -r requirements.txt
   ```

5. Execute as migracoes e crie um usuario admin:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. Rode o Django localmente:

   ```bash
   python manage.py runserver
   ```

O Docker Compose de desenvolvimento inicia somente o banco de dados. A aplicacao roda no ambiente virtual local.
O PostgreSQL fica disponivel no host pela porta `5433`, para evitar conflito com bancos locais na porta `5432`.
