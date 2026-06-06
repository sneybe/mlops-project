from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ── 1. Charger les documents ──────────────────
print("📄 Chargement des documents...")
loader = TextLoader("README.md")
documents = loader.load()

# ── 2. Découper en chunks ─────────────────────
print("✂️  Découpage en chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)
print(f"   → {len(chunks)} chunks créés")

# ── 3. Créer les embeddings + stocker ─────────
print("🧠 Création des embeddings...")
embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
print("   → ChromaDB créé !")

# ── 4. Créer le retriever ─────────────────────
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ── 5. Connecter au LLM Ollama ────────────────
print("🤖 Connexion à Ollama...")
llm = Ollama(model="phi3:mini")

# ── 6. Prompt template ───────────────────────
prompt = PromptTemplate.from_template("""
Utilise le contexte suivant pour répondre à la question.
Si tu ne sais pas, dis-le simplement.

Contexte: {context}
Question: {question}
Réponse:
""")

# ── 7. Chaîne RAG ────────────────────────────
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# ── 8. Poser des questions ───────────────────
print("\n🚀 RAG prêt ! Posons des questions...\n")

questions = [
    "Quels sont les services disponibles ?",
    "Quelle est l'IP de la VM devops ?",
    "Comment tester l'API Iris ?"
]

for question in questions:
    print(f"❓ Question : {question}")
    response = rag_chain.invoke(question)
    print(f"✅ Réponse  : {response}")
    print("─" * 50)
