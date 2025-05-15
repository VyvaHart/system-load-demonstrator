from flask import Flask, request, jsonify, render_template, Response
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time
import hashlib
import os
import tempfile

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'System Load Application', version='1.0.0-dev')

# --- CPU Algorithms ---
def fibonacci_recursive(n):
    if n <= 1:
        return n
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def prime_factorization(n):
    factors = []
    d = 2
    temp_n = n
    while d * d <= temp_n:
        while temp_n % d == 0:
            factors.append(d)
            temp_n //= d
        d += 1
    if temp_n > 1:
        factors.append(temp_n)
    return factors

def perform_hashing(data, iterations):
    s = hashlib.sha256()
    data_bytes = data.encode('utf-8') if isinstance(data, str) else data
    for _ in range(iterations):
        s.update(data_bytes)
    return s.hexdigest()

# --- Memory Operations ---
def consume_memory(size_mb):
    num_chars = size_mb * 1024 * 1024
    large_string = 'x' * num_chars
    return large_string

# --- I/O Operations ---
def perform_io(size_mb, iterations):
    data_chunk = os.urandom(1024 * 1024)
    bytes_to_write = size_mb * 1024 * 1024
    written_bytes = 0
    read_bytes_total = 0

    io_iterations = max(1, iterations)

    for _ in range(io_iterations):
        fd, temp_path = tempfile.mkstemp(prefix="loadapp_", suffix=".tmp")
        try:
            with os.fdopen(fd, 'wb') as tmp:
                current_written_for_file = 0
                while current_written_for_file < bytes_to_write:
                    write_size = min(len(data_chunk), bytes_to_write - current_written_for_file)
                    tmp.write(data_chunk[:write_size])
                    current_written_for_file += write_size
            written_bytes += current_written_for_file

            with open(temp_path, 'rb') as tmp_read:
                while True:
                    chunk = tmp_read.read(1024 * 1024)
                    if not chunk:
                        break
                    read_bytes_total += len(chunk)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return f"Wrote {written_bytes / (1024*1024):.2f} MB, Read {read_bytes_total / (1024*1024):.2f} MB in {io_iterations} cycle(s)."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load', methods=['GET'])
def generate_load():
    mode = request.args.get('mode', 'balanced')
    iterations = int(request.args.get('iterations', '10'))
    data_size_mb = int(request.args.get('data_size_mb', '1'))
    cpu_algorithm = request.args.get('cpu_algorithm', 'fibonacci')
    cpu_task_scale = int(request.args.get('cpu_task_scale', '30'))

    force_cpu = request.args.get('force_cpu') == 'true'
    force_memory = request.args.get('force_memory') == 'true'
    force_io = request.args.get('force_io') == 'true'

    results = {}
    start_time = time.time()
    allocated_memory_holder = None
    io_info_msg = "I/O task not run or no method selected."
    cpu_result_msg = "CPU task not run or no algorithm selected."
    memory_info_msg = "Memory allocation task not run."


    if mode == 'memory_heavy' or force_memory or (mode == 'balanced' and not (force_cpu or force_io)):
        try:
            allocated_memory_holder = consume_memory(data_size_mb)
            memory_info_msg = f"Allocated approx {data_size_mb}MB. String length: {len(allocated_memory_holder)}"
        except MemoryError:
            memory_info_msg = f"MemoryError: Could not allocate {data_size_mb}MB."
        except Exception as e:
            memory_info_msg = f"Error during memory allocation: {str(e)}"
    results['memory_info'] = memory_info_msg

    if mode == 'cpu_heavy' or force_cpu or (mode == 'balanced' and not (force_memory or force_io)):
        try:
            if cpu_algorithm == 'fibonacci':
                fib_val = "N/A"
                if cpu_task_scale > 38 and iterations > 1:
                    temp_fib_results = [fibonacci_iterative(cpu_task_scale + i) for i in range(iterations)]
                    fib_val = f"Iterative results for N around {cpu_task_scale} (last: {temp_fib_results[-1] if temp_fib_results else 'N/A'})"
                else:
                    fib_val = fibonacci_recursive(cpu_task_scale)
                cpu_result_msg = f"Fibonacci({cpu_task_scale}): {fib_val}"
            elif cpu_algorithm == 'prime_factorization':
                last_factors = None
                for i in range(iterations):
                    num_to_factor = cpu_task_scale + i
                    factors = prime_factorization(num_to_factor)
                    if i == iterations - 1:
                        last_factors = {num_to_factor: factors}
                cpu_result_msg = f"Prime factorization for {iterations} numbers around {cpu_task_scale}. Last: {last_factors}"
            elif cpu_algorithm == 'hashing':
                sample_data_for_hash = "s" * (1024 * 256)
                actual_hash_iterations = iterations * (data_size_mb * 4 if data_size_mb > 0 else 100)
                hash_val = perform_hashing(sample_data_for_hash, actual_hash_iterations)
                cpu_result_msg = f"Hashed {len(sample_data_for_hash)/1024}KB data {actual_hash_iterations} times. Hash: ...{hash_val[-8:]}"
            elif cpu_algorithm == 'noop':
                time.sleep(0.001 * iterations)
                cpu_result_msg = "No-op CPU work."
        except Exception as e:
            cpu_result_msg = f"Error during CPU task ({cpu_algorithm}): {str(e)}"
    results['cpu_work'] = cpu_result_msg

    if mode == 'io_heavy' or force_io or (mode == 'balanced' and not (force_cpu or force_memory)):
        try:
            io_info_msg = perform_io(data_size_mb, iterations)
        except Exception as e:
            io_info_msg = f"Error during I/O task: {str(e)}"
    results['io_info'] = io_info_msg

    end_time = time.time()
    results['duration_seconds'] = round(end_time - start_time, 4)
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
    try:
        from prometheus_client import REGISTRY
        output = generate_latest(REGISTRY)
        return Response(output, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        return f"Error generating metrics in /manual_metrics_test: {e}", 500

if __name__ == '__main__':
    # This block is for local development
    app.run(host='0.0.0.0', port=5000, debug=True)