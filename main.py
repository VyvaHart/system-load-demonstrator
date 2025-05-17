from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

print("DEBUG: --- Top of main.py ---")
print(f"DEBUG: prometheus_flask_exporter version according to its __version__ attribute: {PrometheusMetrics.VERSION if hasattr(PrometheusMetrics, 'VERSION') else 'VERSION attr not found'}")
print(f"DEBUG: Location of PrometheusMetrics module: {PrometheusMetrics.__module__} from {PrometheusMetrics.__file__ if hasattr(PrometheusMetrics, '__file__') else 'No file attr'}")

try:
    print("DEBUG: Attempting: metrics_obj = PrometheusMetrics(register_app_info=False)")
    metrics_obj = PrometheusMetrics(register_app_info=False)
    print(f"DEBUG: SUCCESS - PrometheusMetrics() without app instance created: {metrics_obj}")

    app_instance_for_init = Flask("test_app_for_init")
    metrics_obj.init_app(app_instance_for_init)
    print(f"DEBUG: SUCCESS - metrics_obj.init_app(app_instance_for_init) called")

except TypeError as te:
    print(f"DEBUG: CAUGHT TypeError as expected: {te}")
    import sys
    import traceback
    print("DEBUG: Full traceback for TypeError:")
    traceback.print_exc(file=sys.stdout)
except Exception as e:
    print(f"DEBUG: CAUGHT other Exception: {e}")
    import sys
    import traceback
    print("DEBUG: Full traceback for other Exception:")
    traceback.print_exc(file=sys.stdout)


app = Flask("dummy_gunicorn_app")
@app.route('/')
def dummy_route():
    return "Dummy app for Gunicorn after metrics test."

print("DEBUG: --- End of main.py ---")