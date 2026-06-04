from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
import mlflow.sklearn
import os

app = FastAPI()

# Métriques Prometheus
PREDICTIONS = Counter(
    'iris_predictions_total',
    'Total predictions',
    ['classe']
)
LATENCY = Histogram(
    'iris_prediction_latency_seconds',
    'Prediction latency'
)

# Charger le modèle
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
model = mlflow.sklearn.load_model(
    "mlruns/1/models/m-99929f406d8e4ebca5617cdfcc676b69/artifacts"
)

classes = {0: 'Setosa', 1: 'Versicolor', 2: 'Virginica'}

@app.post("/predict")
def predict(data: dict):
    with LATENCY.time():
        inputs = data['inputs']
        prediction = model.predict(inputs)[0]
        classe = classes[prediction]
        PREDICTIONS.labels(classe=classe).inc()
        return {"prediction": int(prediction), "classe": classe}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok"}
