import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict, Set
import os
from src.embeddings.evaluation import mean_metrics_at_k

class ProductEmbeddings:
    def __init__(self, model_name: str = 'multi-qa-mpnet-base-dot-v1', reranker_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = SentenceTransformer(model_name)
        self.reranker = CrossEncoder(reranker_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  
        self.products: List[Dict] = []
        self.embeddings = None

    def load_products(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.products = json.load(f)

    def create_product_text(self, product: Dict) -> str:
        fields = [
            product.get('title', ''),
            product.get('description', ''),
            product.get('job_level', ''),
            product.get('languages', ''),
            str(product.get('completion_time', '')),
            ' '.join(str(x) for x in product.get('test_types', [])),
            product.get('remote_testing', ''),
            ' '.join(pdf.get('name', '') for pdf in product.get('pdf_links', []))
        ]
        return ' '.join([str(field) for field in fields if field])

    def generate_embeddings(self):
        texts = [self.create_product_text(p) for p in self.products]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True)
        self.index.add(self.embeddings.astype('float32'))
        return self.embeddings

    def save_index(self, path: str):
        faiss.write_index(self.index, path)

    def load_index(self, path: str):
        self.index = faiss.read_index(path)

    def search(self, query: str, k: int = 5, rerank: bool = True) -> List[Dict]:
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding.astype('float32'), k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.products):
                result = self.products[idx].copy()
                result['similarity_score'] = float(score)  
                results.append(result)

        if rerank:
            pairs = [[query, self.create_product_text(r)] for r in results]
            rerank_scores = self.reranker.predict(pairs)
            for i, r in enumerate(results):
                r['rerank_score'] = float(rerank_scores[i])
            results.sort(key=lambda x: x['rerank_score'], reverse=True)

        return results

    def evaluate(self, queries: List[str], relevant_ids: List[Set[str]], k: int = 10) -> Dict[str, float]:
        all_retrieved = []
        relevance_mappings = [{url: 1.0 for url in relevant_set} for relevant_set in relevant_ids]
        for query in queries:
            results = self.search(query, k=k)
            retrieved_ids = [str(r.get('url', '')) for r in results]
            all_retrieved.append(retrieved_ids)
        return mean_metrics_at_k(relevance_mappings, all_retrieved, k)

    def evaluate_example(self):
        queries = [
            "entry level sales position",
            "technical programming job",
            "healthcare management role"
        ]
        relevant_ids = [
            {
                "https://www.shl.com/solutions/products/product-catalog/view/retail-sales-associate-solution/",
                "https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/"
            },
            {
                "https://www.shl.com/solutions/products/product-catalog/view/net-mvc-new/",
                "https://www.shl.com/solutions/products/product-catalog/view/net-framework-4-5/"
            },
            {
                "https://www.shl.com/solutions/products/product-catalog/view/healthcare-service-associate-solution/",
                "https://www.shl.com/solutions/products/product-catalog/view/nurse-leader-solution/"
            }
        ]
        metrics = self.evaluate(queries, relevant_ids, k=5)
        print("\nEvaluation Metrics:")
        print(f"Mean Recall@5: {metrics['mean_recall@k']:.3f}")
        print(f"MAP@5: {metrics['map@k']:.3f}")

        print("\nSearch results for:", queries[0])
        results = self.search(queries[0], k=3)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"Score: {result['similarity_score']:.3f} | Rerank Score: {result['rerank_score']:.3f}")
            print(f"Job Level: {result['job_level']}")
            print(f"Languages: {result['languages']}")
            print(f"Completion Time: {result['completion_time']} minutes")
            print(f"Test Types: {', '.join(result['test_types'])}")
            print(f"Remote Testing: {result['remote_testing']}")

def main():
    embedder = ProductEmbeddings()
    products_path = os.path.join('src', 'data', 'shl_products.json')
    embedder.load_products(products_path)
    embedder.generate_embeddings()

    index_path = os.path.join('src', 'embeddings', 'products.index')
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    embedder.save_index(index_path)

    query = "entry level sales position"
    results = embedder.search(query, k=3)

    print(f"\nSearch results for: {query}")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"Score: {result['similarity_score']:.3f} | Rerank Score: {result['rerank_score']:.3f}")
        print(f"Job Level: {result['job_level']}")

    embedder.evaluate_example()

if __name__ == "__main__":
    main()
