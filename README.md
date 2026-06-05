# MLOps Project — Sy Samba

Pipeline MLOps + LLMOps complet de bout en bout.

## Stack technique

| Outil | Rôle | Version |
|-------|------|---------|
| MLflow | Tracking modèles | 3.13.0 |
| FastAPI | APIs REST | latest |
| Docker | Conteneurisation | 29.1.3 |
| Kubernetes K3s | Orchestration | v1.35.4 |
| GitHub Actions | CI/CD | - |
| Docker Hub | Registry | - |
| Prometheus | Métriques | latest |
| Grafana | Dashboard | latest |
| Ollama | Moteur LLM | 0.30.3 |
| phi3:mini | Modèle LLM | 3.8B |

## Infrastructure

| VM | IP | Rôle |
|----|----|------|
| devops | 192.168.65.37 | MLflow, Docker, APIs, Runner |
| k8s | 192.168.65.40 | Cluster K3s |
| monitoring | 192.168.65.38 | Prometheus, Grafana |

## Démarrage rapide

```bash
cd ~/mlops-project
./start.sh
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| MLflow UI | http://192.168.65.37:5000 | Tracking modèles |
| FastAPI Iris | http://192.168.65.37:5001 | API prédiction fleurs |
| FastAPI LLM | http://192.168.65.37:8000 | API questions/réponses |
| Ollama | http://192.168.65.37:11434 | Moteur LLM |
| iris-model K8s | http://192.168.65.40:32653 | Modèle en production |
| llm-api K8s | http://192.168.65.40:30222 | LLM en production |
| Grafana | http://192.168.65.38:3000 | Dashboard monitoring |
| Prometheus | http://192.168.65.38:9090 | Métriques |

## Pipeline CI/CD
git push
↓
iris-pipeline (32s)
├── Train modèle Iris
├── Docker build + push Docker Hub
└── Deploy K8s iris-model
↓
llm-pipeline (10s)
├── Docker build llm-api
├── Push Docker Hub
├── Import dans K3s
└── Deploy K8s llm-api

## APIs

### API Iris — Prédiction de fleurs

```bash
curl -X POST http://192.168.65.37:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
# {"prediction": 0, "classe": "Setosa"}
```

### API LLM — Questions/Réponses

```bash
curl -X POST http://192.168.65.37:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Cest quoi Docker?"}'
# {"response": "Docker est..."}
```

## Docker Hub

- sambasy/iris-model:latest
- sambasy/llm-api:latest

## Architecture
Code → GitHub → Actions → Train → Docker → K8s
↓
Docker Hub
sambasy/iris-model
sambasy/llm-api

## Prochaines étapes

- [ ] Terraform — infrastructure as code
- [ ] Azure ML / AWS SageMaker
- [ ] Alerting Grafana
- [ ] RAG avec LangChain
