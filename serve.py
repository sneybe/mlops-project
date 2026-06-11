from flask import Flask, request, jsonify
import mlflow.sklearn
import glob
import os
import sys

app = Flask(__name__)

# Charger le modèle
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
models = glob.glob('/app/mlruns/1/models/*/artifacts')
model_path = sorted(models)[-1]
print(f"Loading model from: {model_path}")
model = mlflow.sklearn.load_model(model_path)

classes = {0: 'Setosa', 1: 'Versicolor', 2: 'Virginica'}

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "healthy"}), 200

@app.route('/invocations', methods=['POST'])
def predict():
    data = request.get_json()
    inputs = data.get('inputs', [])
    predictions = model.predict(inputs).tolist()
    return jsonify({"predictions": predictions})

# ⚠️ SageMaker passe 'serve' comme argument
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
