FROM python:3.13-slim
WORKDIR /app

# curl ve diğer gerekli paketleri kur
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Kullanıcı oluştur
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Smithery için port 8080'i expose et
EXPOSE 8080

# Health check ekle
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "server.py"]
