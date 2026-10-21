import os

# Valores minimos para os testes rodarem sem .env. O banco vem de DATABASE_URL.
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "chave-de-teste")
