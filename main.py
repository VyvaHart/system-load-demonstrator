from flask import Flask, request, jsonify, render_template, current_app
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
import time
import hashlib
import os
import tempfile


app = Flask(__name__)
print(f"DEV_DEBUG: Flask app object before metrics: {app}")
metrics = PrometheusMetrics(app)
print(f"DEV_DEBUG: PrometheusMetrics object: {metrics}")
print(f"DEV_DEBUG: App's registered view functions: {app.view_functions}")
if 'prometheus_metrics' in app.view_functions:
    print(f"DEV_DEBUG: '/metrics' rule found, mapped to: {app.view_functions['prometheus_metrics']}")
else:
    print("DEV_DEBUG: '/metrics' rule NOT FOUND in app.view_functions!")
print(f"DEV_DEBUG: Full URL Map:\n{str(app.url_map)}")

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
    # Create a large list of random strings (or numbers)
    # I use strings of 'x' for simplicity.
    num_chars = size_mb * 1024 * 1024
    large_string = 'x' * num_chars
    # Return to keep it in memory during the request
    return large_string


# --- I/O Operations ---
def perform_io(size_mb, iterations):
    data_chunk = os.urandom(1024 * 1024) # 1MB chunk
    bytes_to_write = size_mb * 1024 * 1024
    written_bytes = 0
    read_bytes_total = 0

    for _ in range(iterations): # Multiple read/write cycless
        fd, temp_path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as tmp:
                current_written = 0
                while current_written < bytes_to_write:
                    write_size = min(len(data_chunk), bytes_to_write - current_written)
                    tmp.write(data_chunk[:write_size])
                    current_written += write_size
            written_bytes += current_written

            with open(temp_path, 'rb') as tmp_read:
                while True:
                    chunk = tmp_read.read(1024 * 1024) # Read in 1MB chunks
                    if not chunk:
                        break
                    read_bytes_total += len(chunk)
        finally:
            os.remove(temp_path)
    return f"Wrote {written_bytes / (1024*1024):.2f} MB, Read {read_bytes_total / (1024*1024):.2f} MB"


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

    # Handle checkbox values for overrides
    force_cpu = request.args.get('force_cpu') == 'true'
    force_memory = request.args.get('force_memory') == 'true'
    force_io = request.args.get('force_io') == 'true'

    results = {}
    start_time = time.time()
    allocated_memory_holder = None

    # --- Memory Allocation ---
    if mode == 'memory_heavy' or force_memory or (mode == 'balanced' and not (force_cpu or force_io)):
        try:
            allocated_memory_holder = consume_memory(data_size_mb)
            results['memory_info'] = f"Allocated approx {data_size_mb}MB. String length: {len(allocated_memory_holder)}"
        except MemoryError:
            results['memory_info'] = f"MemoryError: Could not allocate {data_size_mb}MB."
        except Exception as e:
            results['memory_info'] = f"Error during memory allocation: {str(e)}"


    # --- CPU Work ---
    if mode == 'cpu_heavy' or force_cpu or (mode == 'balanced' and not (force_memory or force_io)):
        cpu_result = "CPU task not run or no algorithm selected."
        try:
            if cpu_algorithm == 'fibonacci':
                fib_val = "N/A"
                if cpu_task_scale > 38 and iterations > 1: # Heuristic for switching to iterative for very high N combined with general iterations
                    # Use general iterations for iterative, cpu_task_scale is N
                    temp_fib_results = []
                    for i in range(iterations):
                        temp_fib_results.append(fibonacci_iterative(cpu_task_scale + i)) # Vary N slightly
                    fib_val = f"Iterative results for N around {cpu_task_scale} (last: {temp_fib_results[-1] if temp_fib_results else 'N/A'})"
                else: # Use recursive for smaller N or single iteration focus
                    fib_val = fibonacci_recursive(cpu_task_scale)
                cpu_result = f"Fibonacci({cpu_task_scale}): {fib_val}"
            elif cpu_algorithm == 'prime_factorization':
                factors_summary = []
                for i in range(iterations): # Factorize 'iterations' numbers
                    num_to_factor = cpu_task_scale + i # Vary the number slightly
                    factors = prime_factorization(num_to_factor)
                    if i == iterations -1 : # Only store last for summary to save space in response
                         factors_summary.append({num_to_factor: factors})
                cpu_result = f"Prime factorization for {iterations} numbers around {cpu_task_scale}. Last: {factors_summary}"
            elif cpu_algorithm == 'hashing':
                # Create some data to hash based on data_size_mb but don't hold it (focus on CPU)
                # Use a smaller amount of data but hash it many times
                sample_data_for_hash = "s" * (1024 * 256) # 256KB of 's'
                actual_hash_iterations = iterations * (data_size_mb * 4 if data_size_mb > 0 else 100) # Scale hash iterations
                hash_val = perform_hashing(sample_data_for_hash, actual_hash_iterations)
                cpu_result = f"Hashed {len(sample_data_for_hash)/1024}KB data {actual_hash_iterations} times. Hash: ...{hash_val[-8:]}"
            elif cpu_algorithm == 'noop':
                time.sleep(0.001 * iterations)
                cpu_result = "No-op CPU work."
        except Exception as e:
            cpu_result = f"Error during CPU task ({cpu_algorithm}): {str(e)}"
        results['cpu_work'] = cpu_result

    # --- I/O Work ---
    if mode == 'io_heavy' or force_io or (mode == 'balanced' and not (force_cpu or force_memory)):
        try:
            # Use 'iterations' to control number of read/write cycles for the 'data_size_mb' file
            io_info = perform_io(data_size_mb, iterations)
            results['io_info'] = io_info
        except Exception as e:
            results['io_info'] = f"Error during I/O task: {str(e)}"


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
    print("DEV_DEBUG: /manual_metrics_test endpoint hit!")
    try:
        registry_to_use = getattr(metrics, 'registry', CollectorRegistry())
        if hasattr(metrics,'registry'):
            print(f"DEV_DEBUG: Using exporter's registry: {metrics.registry}")
        else:
             print(f"DEV_DEBUG: Exporter's registry not found, using default prometheus_client.REGISTRY")
             registry_to_use = CollectorRegistry()
        output = generate_latest(CollectorRegistry(auto_describe=True))

        print(f"DEV_DEBUG: Generated metrics output length: {len(output)}")
        return Response(output, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        print(f"DEV_DEBUG: Error in /manual_metrics_test: {e}")
        return f"Error generating metrics: {e}", 500

from flask import Response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)