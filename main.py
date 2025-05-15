from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)