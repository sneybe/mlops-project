from flask import Flask, request, jsonify
import mlflow.sklearn
import boto3
import os
import json

app = Flask(__name__)

# ── Charger le modèle depuis S3 ──────────────
BUCKET = "mlops-samba-artifacts"
PREFIX = "mlflow/models"
REGION = "ca-central-1"

def get_latest_model_path():
    """Trouve automatiquement le dernier modèle dans S3"""
    s3 = boto3.client('s3', region_name=REGION)
    response = s3.list_objects_v2(
        Bucket=BUCKET,
        Prefix=PREFIX
    )
    
    # Trouver tous les MLmodel files
    models = [
        obj['Key'] for obj in response.get('Contents', [])
        if obj['Key'].endswith('MLmodel')
    ]
    
    if not models:
        raise Exception("Aucun modèle trouvé dans S3 !")
    
    # Prendre le plus récent
    latest = sorted(models)[-1]
    # Retourner le chemin S3 du dossier
    model_path = f"s3://{BUCKET}/{latest.replace('/MLmodel', '')}"
    print(f"📦 Modèle chargé depuis : {model_path}")
    return model_path

# Charger le modèle au démarrage
model_path = get_latest_model_path()
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
    classes_pred = [classes[p] for p in predictions]
    return jsonify({
        "predictions": predictions,
        "classes": classes_pred
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
