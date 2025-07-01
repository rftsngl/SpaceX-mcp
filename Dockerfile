FROM python:3.13-slim
WORKDIR /app

# Kullanıcı oluştur
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# PORT environment variable için expose
EXPOSE $PORT

CMD ["python", "server.py"]
