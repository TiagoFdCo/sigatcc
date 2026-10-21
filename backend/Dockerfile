FROM python:3.12-slim

# Evita .pyc e garante logs sem buffer (aparecem na hora no `docker compose logs`)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias de sistema minimas para compilar psycopg2 e afins
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# collectstatic roda em build de producao real; aqui fica comentado
# porque depende das settings do projeto Django, que a equipe ainda vai criar.
# RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "sigatcc.wsgi:application", "--bind", "0.0.0.0:8000"]
