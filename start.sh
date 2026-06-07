#!/bin/bash
echo "🚀 Démarrage du stack MLOps..."

# Fonction pour vérifier si un port est utilisé
port_libre() {
    ! ss -tlnp | grep -q ":$1 "
}

# Ollama
sudo systemctl start ollama
echo "✅ Ollama démarré"

# Activer l'env virtuel
source ~/mlops-project/mlops-env/bin/activate
cd ~/mlops-project

# MLflow UI
if port_libre 5000; then
    MLFLOW_ALLOW_FILE_STORE=true mlflow ui --host 0.0.0.0 --port 5000 &
    echo "✅ MLflow UI démarré sur :5000"
else
    echo "⚠️  MLflow UI déjà sur :5000"
fi

# FastAPI Iris
if port_libre 5001; then
    MLFLOW_ALLOW_FILE_STORE=true uvicorn app:app --host 0.0.0.0 --port 5001 &
    echo "✅ FastAPI Iris démarré sur :5001"
else
    echo "⚠️  FastAPI Iris déjà sur :5001"
fi

# FastAPI LLM
if port_libre 8000; then
    uvicorn llm_app:app --host 0.0.0.0 --port 8000 &
    echo "✅ FastAPI LLM démarré sur :8000"
else
    echo "⚠️  FastAPI LLM déjà sur :8000"
fi

# RAG API
if port_libre 8001; then
    cd ~/mlops-project
    source mlops-env/bin/activate
    uvicorn rag_api:app --host 0.0.0.0 --port 8001 &
    echo "✅ RAG API démarré sur :8001"
else
    echo "⚠️  RAG API déjà sur :8001"
fi
echo ""
echo "🎉 Stack MLOps complet !"
echo "   MLflow  → http://192.168.65.37:5000"
echo "   Iris    → http://192.168.65.37:5001"
echo "   RAG     → http://192.168.65.37:8001"
echo "   LLM     → http://192.168.65.37:8000"
echo "   K8s     → http://192.168.65.40:32653"
echo "   Grafana → http://192.168.65.38:3000"
