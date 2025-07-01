FROM python:3.13-slim
WORKDIR /app

# Gerekli paketleri kur
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Kullanıcı oluştur
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Bağımlılıkları kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyala
COPY . .

# Port expose et
EXPOSE 8080

# Sunucuyu başlat
CMD ["python", "server.py"]
