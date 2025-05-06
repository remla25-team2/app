from flask import Flask, render_template, jsonify, request
from lib_version.version_util import VersionUtil
import requests
import os

app = Flask(__name__)
MODEL_URL = os.environ.get('MODEL_SERVICE_URL', 'http://model-service:5001')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
