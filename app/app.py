from flask import Flask, Response, render_template, jsonify, request, g
from lib_version.version_util import VersionUtil
import requests
import os
import time
from prometheus_client import Counter, Gauge, generate_latest, Histogram

app = Flask(__name__)
MODEL_URL = os.environ.get('MODEL_SERVICE_URL', 'http://model-service:5001')

http_reqs = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method','endpoint','status']
)
in_flight = Gauge(
    'in_flight_requests',
    'Number of in-flight requests'
)
request_latency = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint', 'status']
)

@app.before_request
def before_request():
    in_flight.inc()
    g.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    # label by method, path, status code
    http_reqs.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    request_latency.labels(method=request.method, endpoint=request.path, status=response.status_code).observe(duration)
    in_flight.dec()
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sentiment', methods=['POST'])
def sentiment():
    text = request.form['text']
    resp = requests.get(f"{MODEL_URL}/predict", params={'text': text})
    data = resp.json()
    return jsonify(sentiment=data['sentiment'])

@app.route('/version')
def version():
    return jsonify(app_version=VersionUtil.get_version())

@app.route('/version/modelversion')
def modelversion():
    # proxy to model-service
    resp = requests.get(f"{MODEL_URL}/version")
    data = resp.json()
    return jsonify(model_service_version=data.get('service_version'))

@app.route('/check_health')
def check_health():
	return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
