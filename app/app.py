from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/version/appversion')
def get_lib_version():
    return jsonify({'message': 'Here should be App Version!'})

@app.route('/version/modelversion')
def get_model_version():
    return jsonify({'message': 'Here should be Model Version!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)