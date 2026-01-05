# Setup Guide: Pinecone & LangSmith Integration

This guide will help you set up Pinecone and LangSmith for the Healthcare Agentic RAG API.

## Prerequisites

1. **Pinecone Account**: Sign up at https://www.pinecone.io/
2. **LangSmith Account**: Sign up at https://smith.langchain.com/
3. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
4. **Anthropic API Key** (optional): Get from https://console.anthropic.com/

## Step 1: Pinecone Setup

1. **Create a Pinecone Account**
   - Go to https://www.pinecone.io/ and sign up
   - Navigate to your API keys section

2. **Get Your API Key**
   - Copy your Pinecone API key
   - Note your environment/region (e.g., `us-east-1`, `us-west-2`)

3. **Configure in .env**
   ```bash
   PINECONE_API_KEY=your-pinecone-api-key-here
   PINECONE_ENVIRONMENT=us-east-1
   PINECONE_INDEX_NAME=healthcare-knowledge-base
   ```

## Step 2: Tavily Setup (Real-time Web Search)

1. **Create a Tavily Account**
   - Go to https://tavily.com/ and sign up
   - Navigate to your API keys section

2. **Get Your API Key**
   - Copy your Tavily API key
   - Free tier available with generous limits

3. **Configure in .env**
   ```bash
   TAVILY_API_KEY=your-tavily-api-key-here
   TAVILY_ENABLED=true
   TAVILY_MAX_RESULTS=5
   ```

**Why Tavily?**
- Fetches latest medical research and guidelines in real-time
- Searches trusted medical sources (PubMed, NEJM, WHO, CDC, etc.)
- Complements Pinecone's static knowledge base
- Ensures recommendations include most current information

## Step 3: LangSmith Setup

1. **Create a LangSmith Account**
   - Go to https://smith.langchain.com/ and sign up
   - Create a new project (or use default)

2. **Get Your API Key**
   - Go to Settings → API Keys
   - Create a new API key
   - Copy the key

3. **Configure in .env**
   ```bash
   LANGSMITH_API_KEY=your-langsmith-api-key-here
   LANGSMITH_PROJECT=healthcare-rag
   LANGSMITH_TRACING=true
   ```

## Step 4: LLM Provider Setup

### Option A: OpenAI (Default)

1. **Get OpenAI API Key**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key

2. **Configure in .env**
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   LLM_PROVIDER=openai
   ```

### Option B: Anthropic

1. **Get Anthropic API Key**
   - Go to https://console.anthropic.com/
   - Create a new API key

2. **Configure in .env**
   ```bash
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   LLM_PROVIDER=anthropic
   ```

**Note**: You can set both keys and switch providers by changing `LLM_PROVIDER`. OpenAI is required for embeddings regardless of LLM provider choice.

## Step 5: Seed Pinecone

After setting up your `.env` file, seed Pinecone with medical knowledge:

```bash
python scripts/seed_pinecone.py
```

This will:
- Create the Pinecone index if it doesn't exist
- Add medical guidelines, protocols, and safety information
- Organize documents into namespaces:
  - `medical_guidelines`: Clinical guidelines
  - `treatment_protocols`: Treatment protocols
  - `safety_guidelines`: Medication safety information

## Step 6: Verify Setup

1. **Check Pinecone Index**
   - Go to your Pinecone dashboard
   - Verify the index `healthcare-knowledge-base` exists
   - Check that it has documents (should show vector count)

2. **Test the API**
   ```bash
   # Make a clinical query
   curl -X POST "http://localhost:8000/api/v1/rag/clinical-query" \
     -H "X-API-Key: test-api-key-physician-12345" \
     -H "Content-Type: application/json" \
     -d '{
       "patient_id": 1,
       "query": "chest pain in diabetic patient",
       "include_history": true
     }'
   ```

3. **Check LangSmith**
   - Go to https://smith.langchain.com/
   - Navigate to your project
   - You should see traces of the query:
     - Vector search operations
     - LLM calls
     - Agent responses

## Troubleshooting

### Pinecone Issues

**Error: "Pinecone API key not set"**
- Verify `PINECONE_API_KEY` is set in `.env`
- Restart the application after adding the key

**Error: "Index not found"**
- The seed script will create the index automatically
- Or create it manually in Pinecone dashboard

**Error: "Dimension mismatch"**
- The index dimension should be 1536 (for OpenAI embeddings)
- Delete and recreate the index if needed

### Tavily Issues

**Error: "Tavily API key not set"**
- Verify `TAVILY_API_KEY` is set in `.env`
- Restart the application after adding the key

**No web search results**
- Check `TAVILY_ENABLED=true` in `.env`
- Verify your API key is valid
- Check Tavily dashboard for usage limits

**Slow search performance**
- Reduce `TAVILY_MAX_RESULTS` if needed
- Tavily searches are async and may take a few seconds

### LangSmith Issues

**No traces appearing**
- Verify `LANGSMITH_API_KEY` is set
- Check `LANGSMITH_TRACING=true`
- Ensure you're looking at the correct project name

**Traces incomplete**
- Some operations may not be traced if LangSmith isn't properly initialized
- Check application logs for LangSmith initialization messages

### LLM Issues

**Error: "OpenAI API key not set"**
- Required for embeddings even if using Anthropic for LLM
- Set `OPENAI_API_KEY` in `.env`

**Error: "Anthropic API key not set"**
- Only needed if `LLM_PROVIDER=anthropic`
- Set `ANTHROPIC_API_KEY` in `.env`

## Adding Your Own Medical Knowledge

To add custom medical knowledge to Pinecone:

1. **Create documents**:
   ```python
   from langchain.schema import Document
   
   documents = [
       Document(
           page_content="Your medical guideline text here...",
           metadata={
               "source": "Your Source",
               "type": "guideline",  # or "protocol", "safety"
               "category": "cardiac",  # or other category
           }
       )
   ]
   ```

2. **Add to Pinecone**:
   ```python
   from app.services.pinecone_service import PineconeService
   
   service = PineconeService()
   await service.add_documents(documents, namespace="medical_guidelines")
   ```

## Cost Considerations

- **Pinecone**: Free tier available, pay per query/storage
- **Tavily**: Free tier with 1,000 searches/month, then pay per search
- **OpenAI Embeddings**: ~$0.02 per 1M tokens (text-embedding-3-small)
- **OpenAI GPT-4**: ~$10-30 per 1M tokens
- **Anthropic Claude**: ~$3-15 per 1M tokens
- **LangSmith**: Free tier available, pay for additional usage

**Tip**: Tavily is very cost-effective for real-time search. The free tier is usually sufficient for development and moderate production use.

Monitor costs in:
- Pinecone dashboard
- OpenAI/Anthropic dashboards
- LangSmith project metrics

