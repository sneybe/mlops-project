FROM python:3.12-slim

WORKDIR /app

RUN pip install mlflow scikit-learn pandas

COPY mlruns/ /app/mlruns/

ENV MLFLOW_ALLOW_FILE_STORE=true

EXPOSE 5001

CMD mlflow models serve \
    -m "/app/mlruns/1/models/m-99929f406d8e4ebca5617cdfcc676b69/artifacts" \
    --host 0.0.0.0 \
    --port 5001 \
    --no-conda
