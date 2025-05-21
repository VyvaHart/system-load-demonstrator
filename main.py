import os
if 'prometheus_multiproc_dir' not in os.environ:
    os.environ['prometheus_multiproc_dir'] = '/tmp'

from flask import Flask, request, jsonify, render_template, Response
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, Gauge, multiprocess

import time
import hashlib
import tempfile
import logging


def clear_prometheus_multiproc_dir():
    dir_path = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc_dir")
    if os.path.exists(dir_path):
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

clear_prometheus_multiproc_dir()

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.logger.info(f"APP_LOGGER: Flask app object created: {app}")

try:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    app.logger.info("APP_LOGGER: Multiprocess CollectorRegistry initialized.")
except Exception as e:
    app.logger.error(f"APP_LOGGER: ERROR initializing multiprocess collector: {e}", exc_info=True)

try:
    metrics = PrometheusMetrics(app, group_by='url_rule', register_app_info=True, registry=registry)
    metrics.info('app_info_direct_final', 'System Load App - Direct Init Final', version='1.1.3-directfinal')
    app.logger.info(f"APP_LOGGER: PrometheusMetrics with multiprocess registry initialized.")
except Exception as e:
    app.logger.error(f"APP_LOGGER: ERROR initializing PrometheusMetrics: {e}", exc_info=True)

REQUESTS_COUNTER = Counter('custom_requests_total_app_direct', 'Total custom requests (direct_init)', ['path'])
REQUEST_DURATION_HISTOGRAM = Histogram('custom_request_duration_seconds_app_direct', 'Custom request duration (direct_init)', ['path'])
IO_WRITE_MB = Gauge('app_io_written_mb', 'Disk written (MB) per /load request', ['path'])
IO_READ_MB = Gauge('app_io_read_mb', 'Disk read (MB) per /load request', ['path'])
CPU_TIME = Gauge('app_cpu_exec_time_seconds', 'CPU task execution time in seconds', ['path', 'algorithm'])
MEMORY_ALLOC_MB = Gauge('app_memory_allocated_mb', 'Memory allocated in MB per request', ['path'])

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
    data_chunk, bytes_to_write, written_bytes, read_bytes_total = os.urandom(1024*1024), size_mb*1024*1024, 0, 0
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
                    chunk = tmp_read.read(1024*1024)
                    if not chunk: break
                    read_bytes_total += len(chunk)
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
    return f"Wrote {written_bytes / (1024*1024):.2f} MB, Read {read_bytes_total / (1024*1024):.2f} MB in {io_iterations} cycle(s)."

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
    app.logger.info("APP_LOGGER: Route /load hit")
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
    
    MEMORY_ALLOC_MB.labels(path="/load").set(data_size_mb)

    if mode == 'memory_heavy' or force_memory or (mode == 'balanced' and not (force_cpu or force_io)):
        try:
            allocated_memory_holder = consume_memory(data_size_mb)
            memory_info_msg = f"Allocated approx {data_size_mb}MB. String length: {len(allocated_memory_holder)}"
        except Exception as e: memory_info_msg = f"Error memory: {str(e)}"
    results['memory_info'] = memory_info_msg

    if mode == 'cpu_heavy' or force_cpu or (mode == 'balanced' and not (force_memory or force_io)):
        try:
            cpu_start = time.time()
            if cpu_algorithm == 'fibonacci':
                fib_val = fibonacci_recursive(cpu_task_scale) if not(cpu_task_scale > 38 and iterations > 1) else \
                            [fibonacci_iterative(cpu_task_scale + i) for i in range(iterations)][-1]
                cpu_result_msg = f"Fibonacci({cpu_task_scale}): {fib_val}"
            elif cpu_algorithm == 'prime_factorization':
                last_factors = None 
                for i in range(iterations): 
                    num_to_factor = cpu_task_scale + i
                    current_factors = prime_factorization(num_to_factor)
                    if i == iterations -1 : 
                        last_factors = {num_to_factor: current_factors}
                cpu_result_msg = f"Prime factorization for {iterations} numbers around {cpu_task_scale}. Last: {last_factors}"
            elif cpu_algorithm == 'hashing':
                hash_val = perform_hashing("s"*(1024*256), iterations * (data_size_mb*4 if data_size_mb > 0 else 100))
                cpu_result_msg = f"Hashed data. Hash: ...{hash_val[-8:]}"
            elif cpu_algorithm == 'noop': time.sleep(0.001 * iterations); cpu_result_msg = "No-op CPU."
            cpu_exec_time = time.time() - cpu_start
            CPU_TIME.labels(path="/load", algorithm=cpu_algorithm).set(cpu_exec_time)
        except Exception as e: cpu_result_msg = f"Error CPU ({cpu_algorithm}): {str(e)}"
    results['cpu_work'] = cpu_result_msg

    if mode == 'io_heavy' or force_io or (mode == 'balanced' and not (force_cpu or force_memory)):
        try: io_info_msg = perform_io(data_size_mb, iterations)
        except Exception as e: results['io_info'] = f"Error I/O: {str(e)}"
    results['io_info'] = io_info_msg
    
    try:
        if "Wrote" in io_info_msg:
            parts = io_info_msg.split()
            written = float(parts[1])
            read = float(parts[4])
            IO_WRITE_MB.labels(path="/load").set(written)
            IO_READ_MB.labels(path="/load").set(read)
    except Exception as e:
        app.logger.warning(f"Failed to parse I/O metrics: {e}")

    internal_processing_duration = time.time() - internal_processing_start_time
    REQUEST_DURATION_HISTOGRAM.labels(path="/load").observe(internal_processing_duration)

    results['duration_seconds'] = round(time.time() - request_start_time, 4)
    results['parameters_used'] = {"mode":mode, "iterations":iterations, "data_size_mb":data_size_mb, \
                                    "cpu_algorithm":cpu_algorithm, "cpu_task_scale":cpu_task_scale, \
                                    "force_cpu":force_cpu, "force_memory":force_memory, "force_io":force_io}
    if allocated_memory_holder: del allocated_memory_holder
    return jsonify(results)

@app.route('/manual_metrics_test')
def manual_metrics_test():
    app.logger.info("APP_LOGGER: /manual_metrics_test endpoint hit!")
    try:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        output = generate_latest(registry)
        return Response(output, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        app.logger.error(f"APP_LOGGER: Error in /manual_metrics_test: {e}", exc_info=True)
        return f"Error generating metrics in /manual_metrics_test: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
