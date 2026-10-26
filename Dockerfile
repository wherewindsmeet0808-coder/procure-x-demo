FROM python:3.11-slim

# Install Node.js 20 and pnpm (required for Vite frontend)
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire repository (including frontend source)
COPY . .

# Ensure Python can import packages under backend
ENV PYTHONPATH=/app/backend

# Build the frontend (Vite) and copy built assets to a static folder
WORKDIR /app/frontend
RUN pnpm install && pnpm run build && \
    mkdir -p /app/frontend_dist && cp -r dist/* /app/frontend_dist/

# Return to the app root for the server start
WORKDIR /app

EXPOSE 8000

# Start FastAPI with uvicorn (using the correct import path)
CMD ["python3","-m","uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
