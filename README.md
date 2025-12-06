# RAG Chatbot - Student Internship & Education Support

A Retrieval-Augmented Generation (RAG) chatbot system designed to help students with internship information, coding education, and interview preparation.

## Architecture

This chatbot uses a **strict sequential pipeline** architecture with two distinct paths:

### RAG Pipeline (Company Internship Queries)
1. **Intent Analysis** → Classify query intent
2. **Query Routing** → Route to RAG pipeline
3. **Document Retrieval** → Similarity search using ChromaDB + FAISS
4. **Context Validation** → Filter by confidence threshold
5. **Answer Generation** → LLaMA generates answer from retrieved context only
6. **Memory Update** → Store conversation history

### External Knowledge Pipeline (Education & Interview Queries)
1. **Intent Analysis** → Classify query intent
2. **Query Routing** → Route to external pipeline
3. **Knowledge Generation** → Gemini generates factual response
4. **Response Refinement** → LLaMA refines for clarity and tone
5. **Memory Update** → Store conversation history

## Technology Stack

- **Vector Store**: Qdrant (self-hosted)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Primary LLM**: Meta LLaMA 3.3 Turbo (via OpenRouter API)
- **External Knowledge**: Google Gemini API
- **Memory**: Redis (self-hosted) for conversation history
- **Web Server**: Nginx for SSE streaming support

## Project Structure

```
chatbot/
├── main.py                      # Entry point
├── config/
│   └── settings.py             # Configuration and API keys
├── ingestion/
│   ├── load_data.py            # Data loading
│   ├── clean_text.py           # Text preprocessing
│   ├── chunking.py             # Text segmentation
│   ├── embeddings.py           # Vector generation
│   └── chroma_index.py         # Vector storage
├── retrieval/
│   ├── retriever.py            # Similarity search
│   └── score_threshold.py      # Confidence validation
├── llm/
│   ├── llama_llm.py            # LLaMA integration
│   ├── gemini_llm.py           # Gemini integration
│   └── prompts.py              # Prompt templates
├── routing/
│   ├── intent_router.py        # Intent classification
│   └── route_rules.py          # Routing logic
├── graph/
│   ├── build_graph.py          # Pipeline orchestration
│   ├── nodes.py                # Processing nodes
│   └── memory.py               # Conversation state
├── data/
│   ├── companies/              # Company internship data
│   ├── faqs/                   # FAQ documents
│   └── college_docs/           # College policies
└── vectorstore/
    └── chroma/                 # ChromaDB persistence
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file or set environment variables:

```bash
```

### 3. Prepare Data

Add your documents to the `data/` directory:
- `data/companies/` - Company internship information (txt or json)
- `data/faqs/` - Frequently asked questions
- `data/college_docs/` - College policies and guidelines

### 4. Index Documents

Run the ingestion pipeline to create embeddings and index documents:

```python
from ingestion.load_data import DataLoader
from ingestion.clean_text import TextCleaner
from ingestion.chunking import TextChunker
from ingestion.embeddings import EmbeddingGenerator
from ingestion.chroma_index import ChromaIndexer
from config.settings import get_config

config = get_config()

# Load documents
loader = DataLoader()
documents = loader.load_all_documents()

# Clean documents
cleaner = TextCleaner()
cleaned_docs = [cleaner.clean_document(doc) for doc in documents]

# Chunk documents
chunker = TextChunker(
    chunk_size=config["chunk_size"],
    chunk_overlap=config["chunk_overlap"]
)
chunks = chunker.chunk_documents(cleaned_docs)

# Generate embeddings
embedder = EmbeddingGenerator(config["embedding_model"])
texts = [chunk["content"] for chunk in chunks]
embeddings = embedder.generate_embeddings(texts)

# Index in ChromaDB
indexer = ChromaIndexer(
    persist_directory=config["chroma_persist_dir"],
    collection_name=config["collection_name"]
)
indexer.add_documents(chunks, embeddings)
```

### 5. Run the Chatbot

#### Local Development

```bash
python chatbot_service_sse.py
```

#### Docker Deployment (Production)

For production deployment on EC2 with all services (Chatbot, Qdrant, Redis):

```bash
# 1. Create .env file from template
cp env_template.txt .env

# 2. Edit .env and add your API keys
# OPENROUTER_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here

# 3. Build and start all services
docker compose up -d

# 4. Check service health
docker compose ps
curl http://localhost/health

# 5. View logs
docker compose logs -f
```

**Services:**
- Chatbot Service: `http://localhost` (Port 80 via Nginx)
- Qdrant Dashboard: `http://localhost:6333/dashboard`
- Redis: `localhost:6379`

**Management Commands:**
```bash
# Stop services
docker compose down

# Restart services
docker compose restart

# View specific service logs
docker compose logs -f chatbot
docker compose logs -f qdrant
docker compose logs -f redis

# Debug container issues
bash debug-container.sh
```

**EC2 Deployment:**

Use the provided deployment script:

```bash
# On EC2 instance
bash deploy.sh
```

This will:
1. Pull latest code from GitHub
2. Build Docker images locally
3. Start all services with docker-compose
4. Run health checks

See the deployment script for configuration options.

## Usage

### Interactive Mode

```python
from main import RAGChatbot

chatbot = RAGChatbot()

# Query the chatbot
response = chatbot.query("What internships are available at Google?", session_id="user123")
print(response)

# Clear session history
chatbot.clear_session("user123")
```

### API Integration

```python
from main import RAGChatbot

chatbot = RAGChatbot()

def handle_user_query(user_id: str, query: str) -> str:
    """Handle a user query and return response."""
    return chatbot.query(query, session_id=user_id)
```

## Intent Categories

The system classifies queries into four categories:

1. **COMPANY_INTERNSHIP** - Uses RAG pipeline
   - Keywords: internship, company, stipend, eligibility, application
   
2. **EDUCATION_CODING** - Uses external knowledge
   - Keywords: programming, code, algorithm, data structure, Python, Java
   
3. **INTERVIEW_PREPARATION** - Uses external knowledge
   - Keywords: interview, HR, placement, resume, preparation
   
4. **GENERAL_EDUCATION** - Uses external knowledge
   - Keywords: learn, study, course, concept, theory

## Key Features

### No Hallucination
- RAG answers use **only retrieved context**
- External answers refined but not altered factually
- Fallback response when confidence is low

### Source Dominance
- Retrieved documents formatted with metadata
- Company name, document type, and source cited
- Confidence threshold filtering (default: 0.65)

### Session Isolation
- Per-user conversation memory
- Independent session histories
- Configurable history length

### Deterministic Routing
- Intent-based routing rules
- Consistent pipeline selection
- Internal classification (not exposed to user)

## Configuration

Edit `config/settings.py` to customize:

- **Models**: Change LLaMA or Gemini model versions
- **Temperature**: Adjust creativity (0.0 - 1.0)
- **Chunk Size**: Modify document segmentation
- **Top-K**: Number of retrieved documents
- **Similarity Threshold**: Minimum confidence score
- **Max History**: Conversation turns to remember

## Safety Guarantees

1. **No hallucination** - Strict source adherence
2. **Source dominance** - Retrieved context prioritized
3. **Session isolation** - User privacy maintained
4. **Deterministic routing** - Predictable behavior
5. **Fast execution** - Single primary LLM call per query

## License

This project is for educational purposes.

## Support

For issues or questions, please refer to the project documentation.
