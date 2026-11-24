# Procesador de IDs y hojas de equipo en un servidor (Railway u otro): SPEC-B22.
# El token y la base llegan como variables del servidor; nunca se copian a la imagen
# (`.dockerignore` deja fuera todo `.env`).
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# El chequeo de salud de Railway llega con este nombre (SPEC-B22 DP-07). Si el servidor define
# su propia variable, la pisa y debe incluirlo.
ENV APP_ALLOWED_HOSTS=healthcheck.railway.app,localhost,127.0.0.1

# Zona horaria de Obs (America/Lima) y certificados para la API de Smartsheet.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/backend
COPY backend/requirements.lock ./
RUN pip install -r requirements.lock

# Mismo orden de carpetas que el repo: las migraciones se buscan en ../servicios/ids/sql.
COPY servicios/ids/sql /srv/servicios/ids/sql
COPY backend/app ./app

RUN useradd --create-home --uid 10001 servicio
USER servicio

EXPOSE 8710
CMD ["python", "-m", "app.serve"]
