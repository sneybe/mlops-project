FROM python:3.12-slim

WORKDIR /app

RUN pip install mlflow scikit-learn pandas

COPY mlruns/ /app/mlruns/

ENV MLFLOW_ALLOW_FILE_STORE=true

EXPOSE 5001

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
