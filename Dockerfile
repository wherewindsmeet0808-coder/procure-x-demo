FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl gnupg && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs && npm install -g pnpm && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY . .
WORKDIR /app/frontend
RUN pnpm install && pnpm run build && mkdir -p /app/frontend_dist && cp -r dist/* /app/frontend_dist/
WORKDIR /app
EXPOSE 8000
CMD ["python3","-m","uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]