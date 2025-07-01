FROM python:3.13-slim
WORKDIR /app

# Bağımlılıkları kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyala
COPY . .

# Port expose et
EXPOSE 8080

# Flask'ı direkt çalıştır
ENV PORT=8080
CMD ["python", "server.py"]
