import sys
import traceback
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics, __version__ as pfe_version

print(f"PFE_DEBUG: --- Top of main.py ---")
print(f"PFE_DEBUG: Imported prometheus_flask_exporter version: {pfe_version}")
print(f"PFE_DEBUG: Path of imported PrometheusMetrics: {PrometheusMetrics.__module__} from {PrometheusMetrics.__file__}")

try:
    print(f"PFE_DEBUG: Attempting direct app = Flask('test_app')")
    app_for_test = Flask("test_app_for_direct_init")
    print(f"PFE_DEBUG: app_for_test created: {app_for_test}")

    print(f"PFE_DEBUG: Attempting metrics_obj = PrometheusMetrics(app_for_test)")
    metrics_obj = PrometheusMetrics(app_for_test)
    print(f"PFE_DEBUG: SUCCESS - PrometheusMetrics(app_for_test) created: {metrics_obj}")
    print(f"PFE_DEBUG: URL map after direct init: {str(app_for_test.url_map)}")

except TypeError as te:
    print(f"PFE_DEBUG: CAUGHT TypeError during PrometheusMetrics(app_for_test): {te}")
    print("PFE_DEBUG: Full traceback for TypeError:")
    traceback.print_exc(file=sys.stdout)
except Exception as e:
    print(f"PFE_DEBUG: CAUGHT other Exception during PrometheusMetrics(app_for_test): {e}")
    print("PFE_DEBUG: Full traceback for other Exception:")
    traceback.print_exc(file=sys.stdout)

app = Flask("gunicorn_dummy_app_final_test")
@app.route('/')
def dummy_route_final():
    return "Dummy app for Gunicorn after final metrics init test."

print(f"PFE_DEBUG: --- End of main.py (dummy app for Gunicorn is '{app.name}') ---")