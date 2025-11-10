FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# Copiar requirements primeiro
COPY requirements.txt .

# Instalar dependências do sistema e Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Criar usuário e configurar permissões
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser "$APP_HOME"

USER appuser

EXPOSE 8000

CMD ["uvicorn", "controller:app", "--host", "0.0.0.0", "--port", "8000"]