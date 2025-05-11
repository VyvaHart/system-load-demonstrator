import hashlib

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

print(fibonacci_iterative(10))