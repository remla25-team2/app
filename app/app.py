from flask import Flask, Response, render_template, jsonify, request, g
from lib_version.version_util import VersionUtil
import requests
import os
import time
import uuid
from datetime import datetime
from prometheus_client import Counter, Gauge, generate_latest, Histogram


app = Flask(__name__)
app_version = os.environ.get('VERSION', 'v1')
MODEL_URL = os.environ.get('MODEL_SERVICE_URL', 'http://model-service:5001')

http_reqs = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'version']
)
in_flight = Gauge(
    'in_flight_requests',
    'Number of in-flight requests'
)

prediction_feedback = Counter(
    'prediction_feedback_total',
    'Total feedback received on predictions',
    ['original_prediction', 'user_feedback', 'version']
)
prediction_confidence = Histogram(
    'prediction_confidence_distribution',
    'Distribution of prediction confidence scores',
    ['prediction', 'version']
)
user_corrections = Counter(
    'user_corrections_total',
    'Total user corrections by prediction type',
    ['original_prediction', 'corrected_prediction', 'version']
)

model_service_errors = Counter(
    'model_service_errors_total',
    'Total errors from model service',
    ['error_type', 'version']
)

model_service_warnings = Counter(
    'model_service_warnings_total', 
    'Total warnings from model service',
    ['warning_type', 'version']
)

active_users = Gauge(
    'active_users',
    'Number of active users currently using the app'
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint', 'status', 'version']
)

# in-memory store for predictions and scores
predictions_store = {}

@app.before_request
def before_request():
    in_flight.inc()
    g.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    # label by method, path, status code, and version
    http_reqs.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code,
        version=app_version
    ).inc()
    request_latency.labels(
        method=request.method, 
        endpoint=request.path, 
        status=response.status_code,
        version=app_version
    ).observe(duration)
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
    
    # Generate unique prediction ID
    prediction_id = str(uuid.uuid4())
    
    try:
        # Get prediction from model service
        resp = requests.get(f"{MODEL_URL}/predict", params={'text': text})
        
        # Handle model service errors
        if resp.status_code != 200:
            model_service_errors.labels(
                error_type='http_error',
                version=app_version
            ).inc()
            return jsonify(
                error='Model service error',
                message='Failed to get prediction from model service'
            ), 500
        
        data = resp.json()
        
        # Check if model service returned an error
        if 'error' in data:
            model_service_errors.labels(
                error_type='prediction_error',
                version=app_version
            ).inc()
            return jsonify(
                error='Model prediction failed',
                message=data['error']
            ), 500
        
        sentiment_value = data['sentiment']
        confidence = data.get('confidence', 0.5)
        warning = data.get('warning')
        debug_info = data.get('debug_info', {})
        
        # Record warning metrics if present
        if warning:
            model_service_warnings.labels(
                warning_type='vocabulary_mismatch' if 'vocabulary' in warning else 'other',
                version=app_version
            ).inc()
        
        # Store prediction for later feedback
        predictions_store[prediction_id] = {
            'text': text,
            'prediction': sentiment_value,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'warning': warning,
            'debug_info': debug_info
        }
        
        # Record metrics
        prediction_confidence.labels(
            prediction='positive' if sentiment_value == 1 else 'negative',
            version=app_version
        ).observe(confidence)
        
        response_data = {
            'sentiment': sentiment_value,
            'confidence': confidence,
            'prediction_id': prediction_id
        }
        
        # Include warning if present
        if warning:
            response_data['warning'] = warning
        
        if debug_info:
            response_data['debug_info'] = debug_info
        
        return jsonify(response_data)
        
    except requests.exceptions.RequestException as e:
        model_service_errors.labels(
            error_type='connection_error',
            version=app_version
        ).inc()
        return jsonify(
            error='Model service unavailable',
            message=f'Failed to connect to model service: {str(e)}'
        ), 503
    except Exception as e:
        model_service_errors.labels(
            error_type='unexpected_error',
            version=app_version
        ).inc()
        return jsonify(
            error='Internal server error',
            message=f'Unexpected error: {str(e)}'
        ), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    """Handle user feedback on predictions"""
    prediction_id = request.form.get('prediction_id')
    user_feedback = request.form.get('feedback')  # 'correct', 'incorrect', 'positive', 'negative'
    user_correction = request.form.get('correction')  # Optional: what it should be
    
    if not prediction_id or prediction_id not in predictions_store:
        return jsonify(error='Invalid prediction ID'), 400
    
    prediction = predictions_store[prediction_id]
    original_prediction = 'positive' if prediction['prediction'] == 1 else 'negative'
    
    # Record feedback metrics
    if user_feedback in ['correct', 'incorrect']:
        prediction_feedback.labels(
            original_prediction=original_prediction,
            user_feedback=user_feedback,
            version=app_version
        ).inc()
    
    # Record corrections
    if user_correction and user_correction != original_prediction:
        user_corrections.labels(
            original_prediction=original_prediction,
            corrected_prediction=user_correction,
            version=app_version
        ).inc()
        
        # Store correction for potential model retraining
        prediction['user_correction'] = user_correction
        prediction['feedback_timestamp'] = datetime.now().isoformat()
    
    return jsonify(success=True, message='Feedback recorded')

@app.route('/flag', methods=['POST'])
def flag_prediction():
    """Allow users to flag problematic predictions"""
    prediction_id = request.form.get('prediction_id')
    flag_reason = request.form.get('reason')  # 'inappropriate', 'wrong_context', 'other'
    
    if not prediction_id or prediction_id not in predictions_store:
        return jsonify(error='Invalid prediction ID'), 400
    
    prediction = predictions_store[prediction_id]
    prediction['flagged'] = True
    prediction['flag_reason'] = flag_reason
    prediction['flag_timestamp'] = datetime.now().isoformat()
    
    # Record flagged prediction metric with version
    flagged_predictions = Counter(
        'flagged_predictions_total',
        'Total flagged predictions',
        ['reason', 'version']
    )
    flagged_predictions.labels(
        reason=flag_reason,
        version=app_version
    ).inc()
    
    return jsonify(success=True, message='Prediction flagged')

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
