FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV prometheus_multiproc_dir=/tmp/prometheus_multiproc_dir

RUN mkdir -p /tmp/prometheus_multiproc_dir

EXPOSE 5000
CMD ["sh", "-c", "rm -rf /tmp/prometheus_multiproc_dir/* && gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 60 --log-level debug main:app"]
