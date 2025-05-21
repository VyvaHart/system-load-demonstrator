import os
import time
import hashlib
import tempfile
import logging

if 'PROMETHEUS_MULTIPROC_DIR' not in os.environ:
    # Create the directory if prometheus_client doesn't create
    prom_dir = '/tmp/prometheus_multiproc_dir'
    os.makedirs(prom_dir, exist_ok=True)
    os.environ['PROMETHEUS_MULTIPROC_DIR'] = prom_dir
    print(f"MAIN_PY_SETUP: PROMETHEUS_MULTIPROC_DIR set to {os.environ['PROMETHEUS_MULTIPROC_DIR']}")

from flask import Flask, request, jsonify, render_template, Response
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, Gauge, multiprocess

# --- Application Setup ---
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.logger.info("APP_LOGGER: Flask application starting up.")

# --- Prometheus Metrics Setup ---
# Clear stale metrics from multiproc_dir from previous runs
try:
    prom_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if prom_multiproc_dir and os.path.exists(prom_multiproc_dir):
        app.logger.info(f"APP_LOGGER: Clearing old metrics from {prom_multiproc_dir}")
        for filename in os.listdir(prom_multiproc_dir):
            file_path = os.path.join(prom_multiproc_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                app.logger.debug(f"APP_LOGGER: Deleted {file_path}")
            except Exception as e:
                app.logger.warning(f"APP_LOGGER: Error deleting {file_path}: {e}")
    else:
        app.logger.warning(f"APP_LOGGER: PROMETHEUS_MULTIPROC_DIR ({prom_multiproc_dir}) not found or not set, skipping clear.")
except Exception as e:
    app.logger.error(f"APP_LOGGER: Error during prometheus_multiproc_dir cleanup: {e}", exc_info=True)


# Initialize a registry for multiprocess collection
try:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    app.logger.info("APP_LOGGER: Multiprocess CollectorRegistry initialized for Prometheus.")
except Exception as e:
    app.logger.error(f"APP_LOGGER: ERROR initializing multiprocess collector: {e}", exc_info=True)
    registry = CollectorRegistry()
    app.logger.warning("APP_LOGGER: Falling back to default CollectorRegistry due to multiprocess init error.")

# Initialize PrometheusMetrics with the app and the multiprocess registry
try:
    metrics = PrometheusMetrics(app, group_by='url_rule', registry=registry)
    metrics.info('app_info', 'System Load Application', version='1.1.4-multiprocess') # Changed version slightly
    app.logger.info("APP_LOGGER: PrometheusMetrics with custom multiprocess registry initialized.")
    app.logger.info(f"APP_LOGGER: app.url_map after metrics init: {str(app.url_map)}")
except Exception as e:
    app.logger.error(f"APP_LOGGER: ERROR initializing PrometheusMetrics: {e}", exc_info=True)

# Custom Metrics (used by prometheus_flask_exporter)
REQUESTS_COUNTER = Counter('custom_requests_total', 'Total custom requests', ['path'], registry=registry)
REQUEST_DURATION_HISTOGRAM = Histogram('custom_request_duration_seconds', 'Custom request duration', ['path'], registry=registry)
IO_WRITE_MB = Gauge('app_io_written_mb', 'Disk written (MB) per /load request', ['path'], registry=registry)
IO_READ_MB = Gauge('app_io_read_mb', 'Disk read (MB) per /load request', ['path'], registry=registry)
CPU_TIME = Gauge('app_cpu_exec_time_seconds', 'CPU task execution time in seconds', ['path', 'algorithm'], registry=registry)
MEMORY_ALLOC_MB = Gauge('app_memory_allocated_mb', 'Memory allocated in MB per request', ['path'], registry=registry)


# --- Helper Functions for Load Generation ---
def fibonacci_recursive(n):
    if n <= 1: return n
    else: return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b
    return a

def prime_factorization(n):
    factors, d, temp_n = [], 2, n
    while d * d <= temp_n:
        while temp_n % d == 0: factors.append(d); temp_n //= d
        d += 1
    if temp_n > 1: factors.append(temp_n)
    return factors

def perform_hashing(data, iterations):
    s, data_bytes = hashlib.sha256(), data.encode('utf-8') if isinstance(data, str) else data
    for _ in range(iterations): s.update(data_bytes)
    return s.hexdigest()

def consume_memory(size_mb):
    return 'x' * (size_mb * 1024 * 1024)

def perform_io(size_mb, iterations):
    data_chunk = os.urandom(1024 * 1024)
    bytes_to_write = size_mb * 1024 * 1024
    written_bytes, read_bytes_total = 0, 0
    io_iterations = max(1, iterations)
    for _ in range(io_iterations):
        fd, temp_path = tempfile.mkstemp(prefix="loadapp_", suffix=".tmp")
        try:
            with os.fdopen(fd, 'wb') as tmp:
                current_written_for_file = 0
                while current_written_for_file < bytes_to_write:
                    write_size = min(len(data_chunk), bytes_to_write - current_written_for_file)
                    tmp.write(data_chunk[:write_size]); current_written_for_file += write_size
                written_bytes += current_written_for_file
            with open(temp_path, 'rb') as tmp_read:
                while True:
                    chunk = tmp_read.read(1024 * 1024)
                    if not chunk: break
                    read_bytes_total += len(chunk)
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
    return f"Wrote {written_bytes / (1024*1024):.2f} MB, Read {read_bytes_total / (1024*1024):.2f} MB in {io_iterations} cycle(s)."

# --- Flask Routes ---
@app.route('/')
def index():
    REQUESTS_COUNTER.labels(path="/").inc()
    with REQUEST_DURATION_HISTOGRAM.labels(path="/").time():
        pass
    app.logger.info("APP_LOGGER: Route / hit")
    return render_template('index.html')

@app.route('/load', methods=['GET'])
def generate_load():
    REQUESTS_COUNTER.labels(path="/load").inc()
    request_start_time = time.time()
    app.logger.info(f"APP_LOGGER: Route /load hit with params: {request.args}")

    mode = request.args.get('mode', 'balanced')
    iterations = int(request.args.get('iterations', '10'))
    data_size_mb = int(request.args.get('data_size_mb', '1'))
    cpu_algorithm = request.args.get('cpu_algorithm', 'fibonacci')
    cpu_task_scale = int(request.args.get('cpu_task_scale', '30'))
    force_cpu = request.args.get('force_cpu') == 'true'
    force_memory = request.args.get('force_memory') == 'true'
    force_io = request.args.get('force_io') == 'true'

    results = {}
    internal_processing_start_time = time.time()
    allocated_memory_holder = None
    io_info_msg = "I/O task not run."
    cpu_result_msg = "CPU task not run."
    memory_info_msg = "Memory task not run."

    MEMORY_ALLOC_MB.labels(path="/load").set(float(data_size_mb))

    if mode == 'memory_heavy' or force_memory or (mode == 'balanced' and not (force_cpu or force_io)):
        try:
            allocated_memory_holder = consume_memory(data_size_mb)
            memory_info_msg = f"Allocated approx {data_size_mb}MB. String length: {len(allocated_memory_holder)}"
        except MemoryError as me:
            memory_info_msg = f"MemoryError: Could not allocate {data_size_mb}MB. Error: {me}"
            app.logger.error(f"APP_LOGGER: MemoryError in /load: {me}", exc_info=True)
        except Exception as e:
            memory_info_msg = f"Error during memory allocation: {str(e)}"
            app.logger.error(f"APP_LOGGER: Exception in memory allocation: {e}", exc_info=True)
    results['memory_info'] = memory_info_msg

    if mode == 'cpu_heavy' or force_cpu or (mode == 'balanced' and not (force_memory or force_io)):
        try:
            cpu_task_start_time = time.time()
            if cpu_algorithm == 'fibonacci':
                fib_val = "N/A"
                if cpu_task_scale > 38 and iterations > 1:
                    temp_fib_results = [fibonacci_iterative(cpu_task_scale + i) for i in range(iterations)]
                    fib_val = temp_fib_results[-1] if temp_fib_results else "N/A"
                else:
                    fib_val = fibonacci_recursive(cpu_task_scale)
                cpu_result_msg = f"Fibonacci({cpu_task_scale}): {fib_val}"
            elif cpu_algorithm == 'prime_factorization':
                last_factors = None
                for i in range(max(1, iterations)):
                    num_to_factor = cpu_task_scale + i
                    factors = prime_factorization(num_to_factor)
                    if i == max(1, iterations) - 1:
                        last_factors = {num_to_factor: factors}
                cpu_result_msg = f"Prime factorization for {max(1, iterations)} numbers around {cpu_task_scale}. Last: {last_factors}"
            elif cpu_algorithm == 'hashing':
                sample_data_for_hash = "s" * (1024 * 256)
                actual_hash_iterations = iterations * (data_size_mb * 4 if data_size_mb > 0 else 100)
                hash_val = perform_hashing(sample_data_for_hash, actual_hash_iterations)
                cpu_result_msg = f"Hashed {len(sample_data_for_hash)/1024}KB data {actual_hash_iterations} times. Hash: ...{hash_val[-8:]}"
            elif cpu_algorithm == 'noop':
                time.sleep(0.001 * iterations)
                cpu_result_msg = "No-op CPU work."
            CPU_TIME.labels(path="/load", algorithm=cpu_algorithm).set(time.time() - cpu_task_start_time)
        except Exception as e:
            cpu_result_msg = f"Error during CPU task ({cpu_algorithm}): {str(e)}"
            app.logger.error(f"APP_LOGGER: Exception in CPU task: {e}", exc_info=True)
    results['cpu_work'] = cpu_result_msg

    if mode == 'io_heavy' or force_io or (mode == 'balanced' and not (force_cpu or force_memory)):
        try:
            io_info_msg = perform_io(data_size_mb, iterations)
            if "Wrote" in io_info_msg:
                parts = io_info_msg.split()
                written_mb = float(parts[1])
                read_mb = float(parts[4])
                IO_WRITE_MB.labels(path="/load").set(written_mb)
                IO_READ_MB.labels(path="/load").set(read_mb)
        except Exception as e:
            io_info_msg = f"Error during I/O task: {str(e)}"
            app.logger.error(f"APP_LOGGER: Exception in I/O task: {e}", exc_info=True)
    results['io_info'] = io_info_msg

    REQUEST_DURATION_HISTOGRAM.labels(path="/load").observe(time.time() - internal_processing_start_time)
    results['duration_seconds'] = round(time.time() - request_start_time, 4)
    results['parameters_used'] = {
        "mode": mode, "iterations": iterations, "data_size_mb": data_size_mb,
        "cpu_algorithm": cpu_algorithm, "cpu_task_scale": cpu_task_scale,
        "force_cpu": force_cpu, "force_memory": force_memory, "force_io": force_io
    }

    if allocated_memory_holder:
        del allocated_memory_holder
    return jsonify(results)

@app.route('/manual_metrics_test')
def manual_metrics_test():
    app.logger.info("APP_LOGGER: /manual_metrics_test endpoint hit!")
    try:
        output = generate_latest(registry)
        return Response(output, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        app.logger.error(f"APP_LOGGER: Error in /manual_metrics_test: {e}", exc_info=True)
        return f"Error generating metrics in /manual_metrics_test: {e}", 500

# For local development only
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)