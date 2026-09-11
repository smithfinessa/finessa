FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/finessa.db \
    JG_HOST=0.0.0.0 \
    PORT=5000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 finessa \
    && mkdir -p /data /app/storage \
    && chown -R finessa:finessa /data /app/storage
USER finessa
VOLUME ["/data"]
EXPOSE 5000
CMD ["gunicorn","--bind","0.0.0.0:5000","--workers","2","--access-logfile","-","app:app"]
