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
# ⚠️ RAM 12G pour devops (Ollama + phi3:mini nécessite beaucoup de RAM)
multipass launch --name devops --cpus 4 --memory 12G --disk 60G 24.04
multipass launch --name k8s --cpus 4 --memory 4G --disk 40G 24.04
multipass launch --name monitoring --cpus 2 --memory 2G --disk 20G 24.04

# Vérifier
multipass list
```

---

## Étape 2 — Récupérer les IPs

```bash
# Sur Mac — après création des VMs
export IP_DEVOPS=$(multipass info devops | grep IPv4 | awk '{print $2}')
export IP_K8S=$(multipass info k8s | grep IPv4 | awk '{print $2}')
export IP_MONITORING=$(multipass info monitoring | grep IPv4 | awk '{print $2}')

echo "devops     → $IP_DEVOPS"
echo "k8s        → $IP_K8S"
echo "monitoring → $IP_MONITORING"
```

---

## Étape 3 — Configurer le DNS sur les 3 VMs

```bash
# Sur CHAQUE VM (devops, k8s, monitoring)
sudo rm /etc/resolv.conf
sudo bash -c 'cat > /etc/resolv.conf << DNSEOF
nameserver 8.8.8.8
nameserver 8.8.4.4
DNSEOF'
sudo chattr +i /etc/resolv.conf
```

---

## Étape 4 — Configurer les clés SSH depuis le Mac

```bash
# Sur Mac — copier la clé SSH vers les 3 VMs
multipass exec devops -- bash -c "mkdir -p ~/.ssh && echo '$(cat ~/.ssh/id_ed25519.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"

multipass exec k8s -- bash -c "mkdir -p ~/.ssh && echo '$(cat ~/.ssh/id_ed25519.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"

multipass exec monitoring -- bash -c "mkdir -p ~/.ssh && echo '$(cat ~/.ssh/id_ed25519.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
```

---

## Étape 5 — VM devops

```bash
multipass shell devops

# Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker

# Python + venv
sudo apt install python3 python3-pip python3-venv -y
mkdir -p ~/mlops-project && cd ~/mlops-project
python3 -m venv mlops-env
source mlops-env/bin/activate

# ⚠️ Cloner dans le dossier courant avec le point !
git clone https://github.com/sneybe/mlops-project.git .

# Installer les dépendances
pip install mlflow scikit-learn pandas fastapi uvicorn \
            prometheus-client httpx langchain-community \
            langchain-text-splitters chromadb \
            sentence-transformers langchain-core dvc

# Ollama
curl -fsSL https://ollama.com/install.sh | sh

# ⚠️ Configuration initiale uniquement (pas à répéter)
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo bash -c 'cat > /etc/systemd/system/ollama.service.d/override.conf << OLLAMAEOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
OLLAMAEOF'
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Télécharger phi3:mini (~2.2GB)
ollama pull phi3:mini

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

---

## Étape 6 — VM k8s

```bash
multipass shell k8s

# Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker

# K3s
curl -sfL https://get.k3s.io | sh -

# ⚠️ Configurer kubectl correctement
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown ubuntu:ubuntu ~/.kube/config

# ⚠️ Important : exporter KUBECONFIG
export KUBECONFIG=~/.kube/config
echo "export KUBECONFIG=~/.kube/config" >> ~/.bashrc
source ~/.bashrc

# Vérifier
kubectl get nodes

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Image pause (nécessaire pour K3s)
docker pull rancher/mirrored-pause:3.6
docker save rancher/mirrored-pause:3.6 -o pause.tar
sudo k3s ctr images import pause.tar
sudo systemctl restart k3s
```

---

## Étape 7 — VM monitoring

```bash
multipass shell monitoring

sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
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

# ⚠️ Remplacer IP_DEVOPS par la vraie IP de la VM devops
cat > prometheus.yml << 'PROMEOF'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'iris-model'
    static_configs:
      - targets: ['IP_DEVOPS:5001']
  - job_name: 'llm-api'
    static_configs:
      - targets: ['IP_DEVOPS:8000']
PROMEOF

docker-compose up -d
```

---

## Étape 8 — Configurer kubectl sur VM devops

```bash
# Sur Mac
multipass exec k8s -- sudo cat /etc/rancher/k3s/k3s.yaml > ~/k3s.yaml

# ⚠️ Sur Mac : sed -i nécessite '' (différent de Linux)
sed -i '' 's/127.0.0.1/IP_K8S/g' ~/k3s.yaml

# Créer le dossier .kube sur devops
multipass exec devops -- mkdir -p /home/ubuntu/.kube

# Transférer
multipass transfer ~/k3s.yaml devops:/home/ubuntu/.kube/config

# Vérifier
multipass exec devops -- kubectl get nodes
```

---

## Étape 9 — Entraîner le modèle et builder les images

```bash
# Sur VM devops
cd ~/mlops-project
source mlops-env/bin/activate

# ⚠️ Démarrer MLflow AVANT train.py
MLFLOW_ALLOW_FILE_STORE=true mlflow ui --host 0.0.0.0 --port 5000 &
sleep 5

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

## Étape 10 — Importer images dans K3s

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

## Étape 11 — Déployer avec Helm

```bash
# Sur VM devops
cd ~/mlops-project

# ⚠️ Mettre à jour l'IP Ollama dans values.yaml
nano mlops-chart/values.yaml
# Changer ollamaHost: "http://IP_DEVOPS:11434"

helm upgrade --install mlops-app ./mlops-chart
kubectl get pods
kubectl get svc
```

---

## Étape 12 — Services systemd

```bash
# Sur VM devops

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

# RAG API (optionnel - consomme beaucoup de RAM)
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
sudo systemctl enable mlflow iris-api llm-api ollama
sudo systemctl start mlflow iris-api llm-api

# ⚠️ RAG API optionnel - lancer seulement si assez de RAM disponible
# sudo systemctl enable rag-api
# sudo systemctl start rag-api
```

---

## Étape 13 — GitHub Actions Runner

```bash
# Sur VM devops
# ⚠️ Générer un nouveau token sur GitHub à chaque fois :
# https://github.com/sneybe/mlops-project/settings/actions/runners/new

mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-arm64-2.334.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.334.0/actions-runner-linux-arm64-2.334.0.tar.gz
tar xzf ./actions-runner-linux-arm64-2.334.0.tar.gz
./config.sh --url https://github.com/sneybe/mlops-project --token TON_TOKEN

# Installer comme service systemd
sudo ./svc.sh install
sudo ./svc.sh start
```

---

## Étape 14 — Tunnels SSH depuis le Mac

```bash
# Terminal 1 — VM devops
ssh -L 5000:localhost:5000 \
    -L 5001:localhost:5001 \
    -L 8000:localhost:8000 \
    -L 8001:localhost:8001 \
    ubuntu@IP_DEVOPS

# Terminal 2 — VM monitoring
ssh -L 3000:localhost:3000 \
    -L 9090:localhost:9090 \
    ubuntu@IP_MONITORING
```

---

## Vérification finale

```bash
# Iris API via K8s
curl -X POST http://IP_K8S:32653/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
# → {"predictions": [0]}

# LLM API via K8s
curl -X POST http://IP_K8S:30222/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Cest quoi MLOps en une phrase?"}'

# FastAPI Iris locale
curl -X POST http://IP_DEVOPS:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'

# RAG API (si démarrée)
curl -X POST http://localhost:8001/rag \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est lIP de la VM k8s?"}'
```

---

## Services accessibles

| Service | URL |
|---------|-----|
| MLflow | http://localhost:5000 |
| Iris API locale | http://localhost:5001 |
| LLM API locale | http://localhost:8000 |
| RAG API | http://localhost:8001 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| K8s Iris | http://IP_K8S:32653 |
| K8s LLM | http://IP_K8S:30222 |

---

## ⚠️ Notes importantes

Les IPs Multipass changent à chaque recréation des VMs
→ Toujours récupérer les IPs avec multipass list
RAM devops doit être 12G minimum pour Ollama + phi3:mini
MLflow doit tourner AVANT de lancer train.py
git clone doit se faire avec . à la fin pour cloner dans le dossier courant
Sur Mac, sed -i nécessite '' : sed -i '' 's/.../.../g'
KUBECONFIG doit être exporté sur la VM k8s
Le token GitHub Actions expire rapidement
→ Générer un nouveau token à chaque fois
Le chemin du modèle MLflow change à chaque entraînement
→ Le Dockerfile et app.py trouvent automatiquement le bon chemin
RAG API consomme beaucoup de RAM
→ Lancer seulement si nécessaire
Les IPs dans prometheus.yml doivent pointer vers IP_DEVOPS
→ Pas vers IP_K8S !

