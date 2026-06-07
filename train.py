import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import os
# Charger le dataset versionné
df = pd.read_csv("data/iris_v2.csv")
print(f"📊 Dataset : {len(df)} lignes")

# ── 1. Données ──────────────────────────────────────
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── 2. Entraînement + Tracking MLflow ───────────────
mlflow.set_experiment("mon-premier-modele")
# Pointer vers le MLflow de la VM
mlflow.set_tracking_uri(
    os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
)
with mlflow.start_run():

    # Paramètres du modèle
    n_estimators = 100
    max_depth = 3

    # Entraîner
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Évaluer
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    # ── 3. Logger dans MLflow ────────────────────────
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.sklearn.log_model(model, "model")

    print(f"✅ Accuracy : {accuracy:.2f}")
    print(f"✅ Modèle sauvegardé dans MLflow")
