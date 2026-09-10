FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/init_db.py
ENV JG_HOST=0.0.0.0 PORT=5000
CMD ["gunicorn","-b","0.0.0.0:5000","app:app"]
