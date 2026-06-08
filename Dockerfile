FROM python:3.12-slim

WORKDIR /app

RUN pip install mlflow scikit-learn pandas

COPY mlruns/ /app/mlruns/

ENV MLFLOW_ALLOW_FILE_STORE=true

EXPOSE 5001

# Script qui trouve automatiquement le bon chemin
CMD python -c "
import os
import glob
models = glob.glob('/app/mlruns/1/models/*/artifacts')
if models:
    model_path = models[-1]
    print(f'Using model: {model_path}')
    os.execlp('mlflow', 'mlflow', 'models', 'serve',
              '-m', model_path,
              '--host', '0.0.0.0',
              '--port', '5001',
              '--no-conda')
else:
    print('No model found!')
"
