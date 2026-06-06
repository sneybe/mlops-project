from fastapi import FastAPI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import os

app = FastAPI()

# ── Métriques Prometheus ──────────────────────
REQUESTS = Counter('rag_requests_total', 'Total RAG requests')
LATENCY = Histogram('rag_latency_seconds', 'RAG response latency')
ERRORS = Counter('rag_errors_total', 'Total RAG errors')

# ── Initialiser le RAG au démarrage ──────────
print("🚀 Initialisation du RAG...")

loader = TextLoader("README.md")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)

embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = Ollama(model="phi3:mini")

prompt = PromptTemplate.from_template("""
Utilise le contexte suivant pour répondre à la question.
Si tu ne sais pas, dis-le simplement.

Contexte: {context}
Question: {question}
Réponse:
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("✅ RAG prêt !")

# ── Endpoints ────────────────────────────────
@app.post("/rag")
async def ask_rag(data: dict):
    question = data.get("question", "")
    if not question:
        ERRORS.inc()
        return {"error": "Le champ 'question' est obligatoire"}

    REQUESTS.inc()
    start = time.time()
    try:
        response = rag_chain.invoke(question)
        LATENCY.observe(time.time() - start)
        return {
            "question": question,
            "response": response,
            "latency_seconds": round(time.time() - start, 2)
        }
    except Exception as e:
        ERRORS.inc()
        return {"error": str(e)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok", "model": "phi3:mini", "docs": "README.md"}
