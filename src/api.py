from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import sys
import os

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.embeddings.product_embeddings import ProductEmbeddings
from app import (
    get_graded_relevance,
    graded_recall_at_k,
    graded_average_precision,
    format_results,
    get_genai_response,
    init_genai
)

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embedder = ProductEmbeddings()
embedder.load_products(str(root_dir / "src" / "data" / "shl_products.json"))

index_path = root_dir / "src" / "embeddings" / "products.index"
if index_path.exists():
    embedder.load_index(str(index_path))
else:
    embedder.generate_embeddings()
    embedder.save_index(str(index_path))

genai_client = init_genai()


@app.get("/search")
async def search(query: str = None, k: int = 5):
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' parameter")

    try:
        results = embedder.search(query, k=k)
        relevance = get_graded_relevance(results)
        retrieved = [r["url"] for r in results if "url" in r]

        response = {
            "results": results,
            "graded_recall": graded_recall_at_k(relevance, retrieved, k),
            "average_precision": graded_average_precision(relevance, retrieved, k),
        }

        if genai_client:
            response["ai_analysis"] = get_genai_response(
                genai_client, format_results(results, query), query
            )

        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
