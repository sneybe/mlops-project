# MLOps Project — Sy Samba

Pipeline MLOps complet de bout en bout.

## Architecture
Code → GitHub → Actions → Train → Docker → K8s
↓
Docker Hub
sambasy/iris-model

## Stack technique

- **MLflow 3.13.0** — tracking et versioning des modèles
- **Docker** — conteneurisation
- **Kubernetes K3s** — orchestration
- **GitHub Actions** — CI/CD pipeline
- **Docker Hub** — registry d'images

## Infrastructure

| VM | IP | Rôle |
|----|----|------|
| devops | 192.168.65.37 | MLflow, Docker, Runner |
| k8s | 192.168.65.40 | Cluster K3s |

## Pipeline CI/CD

À chaque `git push` sur `main` :
1. Entraînement du modèle
2. Build Docker image
3. Push sur Docker Hub
4. Deploy sur Kubernetes

## Tester l'API

```bash
curl -X POST http://192.168.65.40:32653/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
# {"predictions": [0]}
```

## Prochaines étapes

- [ ] Azure ML / AWS SageMaker
- [ ] Monitoring avec Evidently AI + Grafana
- [ ] LLMOps — déployer un LLM
