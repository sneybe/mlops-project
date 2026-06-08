# Runbook MLOps — Sy Samba
> Guide de déploiement complet from scratch

---

## Prérequis

- Mac Apple Silicon
- Multipass installé
- Compte GitHub (sneybe)
- Compte Docker Hub (sambasy)

---

## Étape 1 — Créer les VMs

```bash
multipass launch --name devops --cpus 4 --memory 8G --disk 60G ubuntu:24.04
multipass launch --name k8s --cpus 4 --memory 4G --disk 40G ubuntu:24.04
multipass launch --name monitoring --cpus 2 --memory 2G --disk 20G ubuntu:24.04
multipass list
```

---

## Étape 2 — Configurer le DNS sur les 3 VMs

```bash
# Sur chaque VM
sudo rm /etc/resolv.conf
sudo bash -c 'cat > /etc/resolv.conf << DNSEOF
nameserver 8.8.8.8
nameserver 8.8.4.4
DNSEOF'
sudo chattr +i /etc/resolv.conf
```

---

## Étape 3 — VM devops

```bash
# Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker

# Python + MLflow
sudo apt install python3 python3-pip python3-venv -y
mkdir -p ~/mlops-project && cd ~/mlops-project
python3 -m venv mlops-env
source mlops-env/bin/activate

# Cloner le repo
git clone https://github.com/sneybe/mlops-project.git .

# Installer les dépendances
pip install mlflow scikit-learn pandas fastapi uvicorn \
            prometheus-client httpx langchain-community \
            langchain-text-splitters chromadb \
            sentence-transformers langchain-core dvc

# Ollama
curl -fsSL https://ollama.com/install.sh | sh

# ⚠️ Configuration initiale uniquement
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo bash -c 'cat > /etc/systemd/system/ollama.service.d/override.conf << OLLAMAEOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
OLLAMAEOF'
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Télécharger phi3:mini (une seule fois)
ollama pull phi3:mini

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

---

## Étape 4 — VM k8s

```bash
# Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo usermod -aG docker ubuntu
newgrp docker

# K3s
curl -sfL https://get.k3s.io | sh -
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown ubuntu:ubuntu ~/.kube/config

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Image pause
docker pull rancher/mirrored-pause:3.6
docker save rancher/mirrored-pause:3.6 -o pause.tar
sudo k3s ctr images import pause.tar
sudo systemctl restart k3s
```

---

## Étape 5 — VM monitoring

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo usermod -aG docker ubuntu
newgrp docker

mkdir ~/monitoring && cd ~/monitoring

cat > docker-compose.yml << 'COMPOSEEOF'
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: always
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=smtp.mail.yahoo.com:587
      - GF_SMTP_USER=sneybe2002@yahoo.fr
      - GF_SMTP_PASSWORD=TON_MOT_DE_PASSE_APP
      - GF_SMTP_FROM_ADDRESS=sneybe2002@yahoo.fr
      - GF_SMTP_FROM_NAME=MLOps Grafana
    restart: always
COMPOSEEOF

cat > prometheus.yml << 'PROMEOF'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'iris-model'
    static_configs:
      - targets: ['192.168.65.37:5001']
  - job_name: 'llm-api'
    static_configs:
      - targets: ['192.168.65.37:8000']
PROMEOF

docker-compose up -d
```

---

## Étape 6 — Configurer kubectl sur VM devops

```bash
# Sur Mac
multipass exec k8s -- sudo cat /etc/rancher/k3s/k3s.yaml > ~/k3s.yaml

# ⚠️ Sur Mac : sed -i nécessite '' 
sed -i '' 's/127.0.0.1/TON_IP_K8S/g' ~/k3s.yaml

# Créer le dossier .kube sur devops
multipass exec devops -- mkdir -p /home/ubuntu/.kube

# Transférer
multipass transfer ~/k3s.yaml devops:/home/ubuntu/.kube/config

# Vérifier
multipass exec devops -- kubectl get nodes
# Vérifier
kubectl get nodes
```

---

## Étape 7 — Déployer les images Docker

```bash
cd ~/mlops-project
source mlops-env/bin/activate

# Entraîner le modèle
MLFLOW_ALLOW_FILE_STORE=true python train.py

# Builder les images
docker build -t sambasy/iris-model:latest .
docker build -f Dockerfile.llm -t sambasy/llm-api:latest .

# Pusher sur Docker Hub
docker login -u sambasy
docker push sambasy/iris-model:latest
docker push sambasy/llm-api:latest

# Exporter vers K3s
docker save sambasy/iris-model:latest -o /tmp/iris-model.tar
docker save sambasy/llm-api:latest -o /tmp/llm-api.tar
```

---

## Étape 8 — Importer images dans K3s

```bash
# Sur Mac
multipass transfer devops:/tmp/iris-model.tar ~/iris-model.tar
multipass transfer devops:/tmp/llm-api.tar ~/llm-api.tar
multipass transfer ~/iris-model.tar k8s:/home/ubuntu/iris-model.tar
multipass transfer ~/llm-api.tar k8s:/home/ubuntu/llm-api.tar

# Sur VM k8s
sudo k3s ctr images import iris-model.tar
sudo k3s ctr images import llm-api.tar
```

---

## Étape 9 — Déployer avec Helm

```bash
cd ~/mlops-project
helm upgrade --install mlops-app ./mlops-chart
kubectl get pods
kubectl get svc
```

---

## Étape 10 — Services systemd

```bash
# MLflow
sudo bash -c 'cat > /etc/systemd/system/mlflow.service << SVCEOF
[Unit]
Description=MLflow UI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/mlops-project
Environment="MLFLOW_ALLOW_FILE_STORE=true"
ExecStart=/home/ubuntu/mlops-project/mlops-env/bin/mlflow ui --host 0.0.0.0 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF'

# Iris API
sudo bash -c 'cat > /etc/systemd/system/iris-api.service << SVCEOF
[Unit]
Description=FastAPI Iris Model
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/mlops-project
Environment="MLFLOW_ALLOW_FILE_STORE=true"
ExecStart=/home/ubuntu/mlops-project/mlops-env/bin/uvicorn app:app --host 0.0.0.0 --port 5001
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF'

# LLM API
sudo bash -c 'cat > /etc/systemd/system/llm-api.service << SVCEOF
[Unit]
Description=FastAPI LLM API
After=network.target ollama.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/mlops-project
ExecStart=/home/ubuntu/mlops-project/mlops-env/bin/uvicorn llm_app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF'

# RAG API
sudo bash -c 'cat > /etc/systemd/system/rag-api.service << SVCEOF
[Unit]
Description=RAG API
After=network.target ollama.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/mlops-project
ExecStart=/home/ubuntu/mlops-project/mlops-env/bin/uvicorn rag_api:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF'

# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable mlflow iris-api llm-api rag-api ollama
sudo systemctl start mlflow iris-api llm-api rag-api
```

---

## Étape 11 — GitHub Actions Runner

```bash
mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-arm64-2.334.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.334.0/actions-runner-linux-arm64-2.334.0.tar.gz
tar xzf ./actions-runner-linux-arm64-2.334.0.tar.gz
./config.sh --url https://github.com/sneybe/mlops-project --token TON_TOKEN
sudo ./svc.sh install
sudo ./svc.sh start
```

---

## Étape 12 — Tunnels SSH depuis le Mac

```bash
# Terminal 1 — VM devops
ssh -L 5000:localhost:5000 \
    -L 5001:localhost:5001 \
    -L 8000:localhost:8000 \
    -L 8001:localhost:8001 \
    ubuntu@192.168.65.37

# Terminal 2 — VM monitoring
ssh -L 3000:localhost:3000 \
    -L 9090:localhost:9090 \
    ubuntu@192.168.65.38
```

---

## Vérification finale

```bash
# Iris API
curl -X POST http://192.168.65.40:32653/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
# → {"predictions": [0]}

# LLM API
curl -X POST http://192.168.65.40:30222/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Cest quoi MLOps?"}'

# RAG API
curl -X POST http://localhost:8001/rag \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est lIP de la VM k8s?"}'
# → {"response": "192.168.65.40"}
```

---

## Services accessibles

| Service | URL |
|---------|-----|
| MLflow | http://localhost:5000 |
| Iris API | http://localhost:5001 |
| LLM API | http://localhost:8000 |
| RAG API | http://localhost:8001 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| K8s Iris | http://192.168.65.40:32653 |
| K8s LLM | http://192.168.65.40:30222 |
