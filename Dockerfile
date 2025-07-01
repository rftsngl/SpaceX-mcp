FROM python:3.13-alpine
WORKDIR /app
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && adduser -D app \
    && chown -R app:app /app
USER app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python","server.py"]
