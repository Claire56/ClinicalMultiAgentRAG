# Healthcare Agentic RAG API

A production-ready FastAPI application for clinical decision support using agentic RAG (Retrieval-Augmented Generation) with LangGraph.

## Features

- **Agentic RAG System**: Multiple AI agents working together for clinical decision support
- **Pinecone Integration**: Vector database for semantic search of medical knowledge
- **Tavily Integration**: Real-time web search for latest medical research and guidelines
- **Hybrid Search**: Combines static knowledge (Pinecone) with real-time information (Tavily)
- **LangSmith Observability**: Full tracing and monitoring of LLM calls and agent workflows
- **Multi-LLM Support**: Choose between OpenAI (GPT-4) or Anthropic (Claude) models
- **FastAPI**: Modern, fast web framework
- **PostgreSQL**: Relational database for patient data
- **Redis**: Caching and rate limiting
- **Authentication**: JWT and API key authentication
- **Security**: Rate limiting, CORS, security headers
- **Structured Logging**: Comprehensive logging with structlog
- **Database Migrations**: Alembic for schema management
- **Docker**: Containerized setup for easy deployment

## Architecture

The application uses multiple specialized agents powered by LangGraph:
- **Clinical Research Agent**: Retrieves medical literature and guidelines from Pinecone vector database
- **Patient History Agent**: Analyzes patient medical history from PostgreSQL
- **Treatment Protocol Agent**: Validates treatments against protocols stored in Pinecone
- **Risk Assessment Agent**: Assesses patient risk factors using patient data and knowledge base

### Technology Stack

- **Vector Database**: Pinecone for storing and retrieving medical knowledge embeddings
- **Real-time Search**: Tavily for fetching latest medical research and guidelines from trusted sources
- **LLM Providers**: OpenAI (GPT-4) or Anthropic (Claude 3.5 Sonnet)
- **Observability**: LangSmith for tracing all LLM calls, agent decisions, and RAG retrievals
- **Embeddings**: OpenAI text-embedding-3-small for cost-effective vector embeddings

### Hybrid RAG Architecture

The system uses a **hybrid RAG approach**:
1. **Pinecone**: Searches established medical guidelines and protocols stored in vector database
2. **Tavily**: Searches real-time web for latest research, breaking news, and updated guidelines
3. **LLM Synthesis**: Combines both sources to generate evidence-based recommendations

This ensures clinicians get both:
- **Established knowledge**: Proven guidelines and protocols
- **Latest information**: Recent research, updated guidelines, and emerging treatments

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Installation

1. **Clone and navigate to the project**:
```bash
cd "AI Agents"
```

2. **Create environment file**:
```bash
cp .env.example .env
```

Edit `.env` and set your configuration values, especially:
- `SECRET_KEY`: Generate a secure random key (min 32 characters)
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings and optional LLM)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional, for Claude models)
- `LLM_PROVIDER`: Set to "openai" or "anthropic" (default: "openai")
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENVIRONMENT`: Your Pinecone environment/region (e.g., "us-east-1")
- `PINECONE_INDEX_NAME`: Name for your Pinecone index (default: "healthcare-knowledge-base")
- `TAVILY_API_KEY`: Your Tavily API key for real-time web search
- `TAVILY_ENABLED`: Set to "true" to enable Tavily (default: "true")
- `LANGSMITH_API_KEY`: Your LangSmith API key for observability
- `LANGSMITH_PROJECT`: Project name for LangSmith (default: "healthcare-rag")
- `DATABASE_URL` and `SYNC_DATABASE_URL`: Database connection strings

3. **Start Docker services**:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379

4. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

5. **Run database migrations**:
```bash
alembic upgrade head
```

6. **Seed the database with fake data**:
```bash
python scripts/seed_data.py
```

This will create:
- 3 test users (admin, doctor, nurse)
- 50 fake patients
- Medical records, medications, and treatments

7. **Seed Pinecone with medical knowledge base**:
```bash
python scripts/seed_pinecone.py
```

This will populate your Pinecone index with medical guidelines and protocols that the RAG agents will use.

7. **Start the application**:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs` (when DEBUG=True)
- **ReDoc**: `http://localhost:8000/api/redoc` (when DEBUG=True)
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

## Authentication

### JWT Authentication

1. **Login** to get a token:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

2. **Use the token** in subsequent requests:
```bash
curl -X GET "http://localhost:8000/api/v1/patients" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### API Key Authentication

Use the API key in the header:
```bash
curl -X GET "http://localhost:8000/api/v1/patients" \
  -H "X-API-Key: test-api-key-admin-12345"
```

## Example Usage

### Clinical Query (Agentic RAG)

Query the system for clinical decision support. The system will:
1. Retrieve patient context from PostgreSQL
2. Search Pinecone for established medical guidelines (static knowledge)
3. Search Tavily for latest medical research and updated guidelines (real-time)
4. Synthesize both sources using LLM (OpenAI or Anthropic) to generate recommendations
5. All operations are traced in LangSmith

```bash
curl -X POST "http://localhost:8000/api/v1/rag/clinical-query" \
  -H "X-API-Key: test-api-key-physician-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "query": "Patient presents with chest pain and has diabetes. What should I do?",
    "include_history": true,
    "urgency": "high"
  }'
```

**View traces in LangSmith**: After making queries, visit your LangSmith project to see:
- Vector search queries and results
- LLM prompts and responses
- Agent decision flows
- Token usage and costs
- Latency metrics

### Get Patient Information

```bash
curl -X GET "http://localhost:8000/api/v1/patients/1" \
  -H "X-API-Key: test-api-key-admin-12345"
```

### Create Medical Record

```bash
curl -X POST "http://localhost:8000/api/v1/medical-records" \
  -H "X-API-Key: test-api-key-physician-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "record_type": "consultation",
    "title": "Chest Pain Evaluation",
    "description": "Patient reports chest pain",
    "symptoms": "Chest pain, shortness of breath",
    "physician_name": "Dr. Smith",
    "date_of_visit": "2024-01-15T10:00:00Z"
  }'
```

## Test Credentials

After running the seed script:

- **Admin**: `username=admin`, `password=admin123`, `api_key=test-api-key-admin-12345`
- **Physician**: `username=dr.smith`, `password=doctor123`, `api_key=test-api-key-physician-12345`
- **Nurse**: `username=nurse.jones`, `password=nurse123`

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoints
│   │       └── router.py       # Route aggregation
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database setup
│   │   ├── security.py         # Authentication
│   │   └── logging.py          # Logging config
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   │   └── rag_service.py     # RAG service
│   ├── middleware/             # Custom middleware
│   └── main.py                # FastAPI app
├── alembic/                    # Database migrations
├── scripts/
│   └── seed_data.py           # Database seeding
├── docker-compose.yml          # Docker services
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Production Considerations

This application includes production-ready features:

- ✅ Rate limiting (per minute and per hour)
- ✅ Security headers
- ✅ Structured logging
- ✅ Error handling
- ✅ Input validation with Pydantic
- ✅ Database connection pooling
- ✅ Async/await for performance
- ✅ Health check endpoints
- ✅ CORS configuration
- ✅ API versioning

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

### Code Quality

The codebase follows best practices:
- Type hints throughout
- Pydantic for validation
- Structured logging
- Error handling
- Security middleware

## License

This is a demonstration project for learning purposes.

