FROM python:3.13-slim
WORKDIR /app

# Sadece gerekli paketleri kur ve temizle
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Kullanıcı oluştur
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python","server.py"]
