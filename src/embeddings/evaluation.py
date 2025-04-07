from typing import List, Set, Dict

def graded_recall_at_k(relevant_scores: Dict[str, float], retrieved: List[str], k: int) -> float:
    """Calculate recall where items contribute proportionally to their relevance score"""
    top_k = retrieved[:k]
    total_relevance = sum(relevant_scores.values())
    if total_relevance == 0:
        return 0.0
    retrieved_relevance = sum(relevant_scores.get(url, 0) for url in top_k)
    return retrieved_relevance / total_relevance

def average_precision_at_k(relevant_scores: Dict[str, float], retrieved: List[str], k: int) -> float:
    """Calculate graded average precision"""
    hits = 0
    sum_precisions = 0.0
    total_relevant = sum(1 for score in relevant_scores.values() if score > 0)
    
    if total_relevant == 0:
        return 0.0
    
    for i, item in enumerate(retrieved[:k], 1):
        if item in relevant_scores and relevant_scores[item] > 0:
            hits += 1
            precision = hits / i
            sum_precisions += precision * relevant_scores[item] 
            
    return sum_precisions / min(total_relevant, k)

def mean_metrics_at_k(relevance_mappings: List[Dict[str, float]], retrieved_lists: List[List[str]], k: int) -> dict:
    """Calculate mean metrics across multiple queries"""
    recalls = []
    aps = []
    
    for relevant_scores, retrieved in zip(relevance_mappings, retrieved_lists):
        recalls.append(graded_recall_at_k(relevant_scores, retrieved, k))
        aps.append(average_precision_at_k(relevant_scores, retrieved, k))
    
    n_queries = len(relevance_mappings)
    return {
        'mean_recall@k': sum(recalls) / n_queries if n_queries > 0 else 0.0,
        'map@k': sum(aps) / n_queries if n_queries > 0 else 0.0
    }