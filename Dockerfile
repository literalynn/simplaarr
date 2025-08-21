# ---------- Frontend build ----------
FROM node:18-slim AS webbuilder
WORKDIR /web
COPY frontend/package.json frontend/vite.config.js frontend/index.html ./
COPY frontend/src ./src
RUN npm ci && npm run build

# ---------- Backend ----------
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV SIMPLAARR_DB=/data/simplaarr.db SIMPLAARR_LOG=/logs/simplaarr.log SIMPLAARR_CONFIG=/config SIMPLAARR_STATIC=/app/static
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg pciutils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/app /app/app
COPY --from=webbuilder /web/dist /app/static
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
