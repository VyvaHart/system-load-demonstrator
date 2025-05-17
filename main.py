import sys
import traceback
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics, __version__ as pfe_version
import inspect

print(f"PFE_DEBUG: --- Top of main.py ---")
print(f"PFE_DEBUG: Imported prometheus_flask_exporter package version: {pfe_version}")

pfe_module = sys.modules.get('prometheus_flask_exporter')
if pfe_module and hasattr(pfe_module, '__file__'):
    print(f"PFE_DEBUG: Path of prometheus_flask_exporter module: {pfe_module.__file__}")
else:
    print(f"PFE_DEBUG: Could not determine file path for prometheus_flask_exporter module.")

try:
    print(f"PFE_DEBUG: Attempting: app_for_test = Flask('test_app_for_direct_init')")
    app_for_test = Flask("test_app_for_direct_init")
    print(f"PFE_DEBUG: app_for_test created: {app_for_test}")

    print(f"PFE_DEBUG: Attempting metrics_obj = PrometheusMetrics(app_for_test)")
    metrics_obj = PrometheusMetrics(app_for_test)
    print(f"PFE_DEBUG: SUCCESS - PrometheusMetrics(app_for_test) created: {metrics_obj}")
    print(f"PFE_DEBUG: URL map after direct init: {str(app_for_test.url_map)}")
    if '/metrics' in str(app_for_test.url_map):
        print("PFE_DEBUG: '/metrics' IS in app_for_test.url_map")
    else:
        print("PFE_DEBUG: '/metrics' IS NOT in app_for_test.url_map (This would be bad)")


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