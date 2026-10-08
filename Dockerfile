FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des scripts d'initialisation
COPY app/ /app

CMD ["python", "init_db.py"]