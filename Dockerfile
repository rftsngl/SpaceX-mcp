FROM python:3.13-slim
WORKDIR /app

# Güvenlik ve kullanıcı oluşturma
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos '' app \
    && chown -R app:app /app

USER app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python","server.py"]
