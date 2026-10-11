FROM ghcr.io/astral-sh/uv:0.8.22 AS uv
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/backend/.venv/bin:$PATH" \
    STORAGE_PATH=/var/lib/agritrade

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-impress \
       bubblewrap \
       util-linux \
       fonts-dejavu-core \
       fonts-crosextra-carlito \
       fonts-crosextra-caladea \
       fonts-liberation2 \
       fonts-noto-core \
       fonts-khmeros \
       fontconfig \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /opt/backend

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project \
    && groupadd --gid 10001 agritrade \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin agritrade \
    && mkdir -p /var/lib/agritrade /run/agritrade-converter /var/cache/fontconfig \
    && chown -R 10001:10001 /var/lib/agritrade /run/agritrade-converter /var/cache/fontconfig \
    && chmod 700 /run/agritrade-converter

COPY --chown=10001:10001 app ./app
COPY --chown=10001:10001 alembic ./alembic
COPY --chown=10001:10001 alembic.ini ./alembic.ini
COPY --chown=10001:10001 seed_admin.py ./seed_admin.py
RUN cp app/assets/fonts-local.conf /etc/fonts/local.conf && fc-cache -f

USER 10001:10001
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
