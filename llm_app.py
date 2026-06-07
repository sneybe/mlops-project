from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
import httpx
import time
import os

app = FastAPI()

# Métriques Prometheus
REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests'
)
LATENCY = Histogram(
    'llm_response_latency_seconds',
    'LLM response latency'
)
ERRORS = Counter(
    'llm_errors_total',
    'Total LLM errors'
)

#OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/api/generate"

@app.post("/ask")
async def ask(data: dict):
    question = data.get("question", "")
    REQUESTS.inc()

    # Vérifier que la question n'est pas vide
    if not question:
        ERRORS.inc()
        return {"error": "Le champ 'question' est obligatoire"}

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": "phi3:mini",
                "prompt": question,
                "stream": False
            })
            result = response.json()
            latency = time.time() - start
            LATENCY.observe(latency)

            return {
                "question": question,
                "response": result.get("response", ""),
                "latency_seconds": round(latency, 2)
            }
    except Exception as e:
        ERRORS.inc()
        return {"error": str(e)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok", "model": "phi3:mini"}
