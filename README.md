
# SHL Assessment Solutions Explorer

A semantic search engine and recommender system for SHL Assessment products using embeddings and GenAI-powered analysis.

## Overview

This project provides a search interface for exploring SHL's assessment solutions catalog using:
- Semantic search with sentence transformers
- FAISS vector similarity search
- GenAI-powered analysis of search results
- Both web UI (Streamlit) and API (FastAPI) interfaces

## Key Features

- **Semantic Search**: Uses sentence transformers to convert assessment descriptions into embeddings for similarity search
- **Reranking**: Cross-encoder model for improved result ranking
- **Vector Search**: FAISS indexing for fast similarity lookup
- **GenAI Analysis**: Gemini AI integration for interpreting search results
- **Evaluation Metrics**: Graded relevance metrics for search quality
- **Dual Interface**: Web UI with Streamlit and REST API with FastAPI

## Project Structure

```
shl/
├── src/
│   ├── data/
│   │   └── shl_products.json      # Assessment product catalog data
│   ├── embeddings/
│   │   ├── product_embeddings.py  # Core embedding and search logic  
│   │   ├── evaluation.py         # Search quality metrics
│   │   └── products.index        # FAISS vector index
│   ├── app.py                    # Streamlit web interface
│   └── api.py                    # FastAPI REST API
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

3. Run the web interface:
```bash
streamlit run src/app.py
```

4. Run the API server:
```bash
uvicorn src.api:app --reload
```

## Core Components

### Product Embeddings (`product_embeddings.py`)

- Generates embeddings using SentenceTransformer
- Builds FAISS index for similarity search
- Implements search with optional reranking
- Includes evaluation metrics

### Web Interface (`app.py`)

- Search interface built with Streamlit
- Displays raw search results and metrics
- GenAI-powered analysis of results
- Interactive result exploration

### REST API (`api.py`)

- FastAPI endpoints for search functionality
- Returns search results, metrics, and AI analysis
- CORS-enabled for web clients

## Search Features

- **Query Processing**: Converts natural language queries to embeddings
- **Similarity Search**: Uses FAISS for fast vector similarity
- **Reranking**: Optional cross-encoder reranking
- **Result Analysis**: 
  - Similarity scores
  - Job level matching
  - Test type analysis
  - Documentation links
  - AI-generated insights

## Metrics

- **Graded Relevance**: Relevance scores based on similarity
- **Recall@K**: Weighted by similarity scores
- **Average Precision**: Precision weighted by relevance

## API Endpoints

### GET /search
Query parameters:
- `query`: Search query string
- `k`: Number of results (default: 5)

Returns:
- Search results
- Graded recall
- Average precision
- AI analysis (if enabled)

## Dependencies

- sentence-transformers
- faiss-cpu
- streamlit
- fastapi
- google.generativeai
- python-dotenv

## License

MIT License
