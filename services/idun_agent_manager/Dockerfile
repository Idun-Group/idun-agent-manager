FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install runtime deps
RUN pip install --no-cache-dir uvicorn fastapi "sqlalchemy>=2" "psycopg[binary]>=3" pydantic-settings PyYAML docker GitPython

# Copy manager service
COPY services/idun_agent_manager /app/services/idun_agent_manager

# Expose API
EXPOSE 8002

CMD ["uvicorn", "services.idun_agent_manager.main:app", "--host", "0.0.0.0", "--port", "8002"]
