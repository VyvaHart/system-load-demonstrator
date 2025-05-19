FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV prometheus_multiproc_dir=/tmp/prometheus_multiproc_dir

RUN mkdir -p /tmp/prometheus_multiproc_dir

EXPOSE 5000

CMD ["sh", "-c", "rm -rf /tmp/prometheus_multiproc_dir/* && gunicorn main:app --bind 0.0.0.0:5000 --workers 2 --threads 4 --worker-class gthread --timeout 120 --log-level debug"]
