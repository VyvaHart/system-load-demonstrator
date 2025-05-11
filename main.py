import hashlib
import os
import tempfile

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
    for _ in range(iterations):
        s.update(data.encode('utf-8') if isinstance(data, str) else data)
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

print(perform_io(20, 40))