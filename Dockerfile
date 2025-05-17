FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && echo "VERIFYING PROMETHEUS_FLASK_EXPORTER VERSION:" \
    && python -c "import prometheus_flask_exporter; print(prometheus_flask_exporter.__version__)" \
    && echo "---"

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "--timeout", "60", "main:app"]