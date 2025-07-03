FROM python:3.13-slim
WORKDIR /app

# Bağımlılıkları kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyala
COPY . .

# Gerekli data dosyalarını kopyala
COPY mcp_latest_launch.json ./

# MCP server'ı STDIO üzerinden çalıştır
CMD ["python", "server.py"]
