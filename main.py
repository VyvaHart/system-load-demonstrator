from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

print(f"DEBUG: Type of imported PrometheusMetrics: {type(PrometheusMetrics)}")
print(f"DEBUG: PrometheusMetrics MRO: {PrometheusMetrics.mro()}")
print(f"DEBUG: PrometheusMetrics __init__ signature (approx): {PrometheusMetrics.__init__.__text_signature__ if hasattr(PrometheusMetrics.__init__, '__text_signature__') else 'No text signature'}")

try:
    print("DEBUG: Attempting 'metrics = PrometheusMetrics(register_app_info=False)'")
    metrics_test_obj = PrometheusMetrics(register_app_info=False)
    print(f"DEBUG: Successfully created PrometheusMetrics object without app: {metrics_test_obj}")

    app_test = Flask("test_app")
    print(f"DEBUG: Created Flask app_test: {app_test}")
    metrics_test_obj.init_app(app_test)
    print(f"DEBUG: Successfully called init_app on metrics_test_obj with app_test")
    print(f"DEBUG: app_test.url_map after init_app: {str(app_test.url_map)}")

except TypeError as te:
    print(f"DEBUG: CAUGHT TypeError: {te}")
except Exception as e:
    print(f"DEBUG: CAUGHT Exception: {e}")

app = Flask("gunicorn_dummy_app")
@app.route('/')
def hello():
    return "Minimal app for Gunicorn test"

print("DEBUG: Minimal app defined for Gunicorn.")