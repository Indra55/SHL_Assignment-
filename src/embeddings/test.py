from src.embeddings.evaluation import  graded_recall_at_k, average_precision_at_k, mean_metrics_at_k   
import random

# Mock data generator
def generate_test_case(num_relevant=5, num_retrieved=10, k=5):
    """Generate a test case with random relevance and retrieval"""
    # Create random relevant items (ground truth)
    relevant = {f"url_{i}": random.uniform(0.5, 1.0) for i in range(num_relevant)}
    
    # Create retrieved list with some overlap
    retrieved = []
    # Add some truly relevant items
    for url in random.sample(list(relevant.keys()), min(3, num_relevant)):
        retrieved.append(url)
    # Add some irrelevant items
    retrieved.extend(f"bad_url_{i}" for i in range(num_retrieved - len(retrieved)))
    random.shuffle(retrieved)
    
    return relevant, retrieved

# Test cases
def test_metrics():
    print("Running quick sanity checks...\n")
    
    # Test 1: Perfect retrieval
    relevant = {"url1": 1.0, "url2": 0.8, "url3": 0.6}
    retrieved = ["url1", "url2", "url3", "url4", "url5"]
    print(f"Perfect case - Recall@3: {graded_recall_at_k(relevant, retrieved, 3):.1%} (should be 100%)")
    print(f"Perfect case - AP@3: {average_precision_at_k(relevant, retrieved, 3):.1%}\n")
    
    # Test 2: Partial retrieval
    relevant = {"url1": 1.0, "url2": 0.8, "url3": 0.6}
    retrieved = ["url1", "bad1", "url3", "bad2", "bad3"]
    print(f"Partial case - Recall@3: {graded_recall_at_k(relevant, retrieved, 3):.1%} (should be ~67%)")
    print(f"Partial case - AP@3: {average_precision_at_k(relevant, retrieved, 3):.1%}\n")
    
    # Test 3: Random case
    relevant, retrieved = generate_test_case()
    print(f"Random relevant: {relevant}")
    print(f"Random retrieved: {retrieved[:5]}...")
    print(f"Random case - Recall@5: {graded_recall_at_k(relevant, retrieved, 5):.1%}")
    print(f"Random case - AP@5: {average_precision_at_k(relevant, retrieved, 5):.1%}\n")
    
    # Test 4: Multiple queries
    test_cases = [generate_test_case() for _ in range(3)]
    relevance_mappings = [case[0] for case in test_cases]
    retrieved_lists = [case[1] for case in test_cases]
    metrics = mean_metrics_at_k(relevance_mappings, retrieved_lists, 5)
    print(f"Batch of 3 queries - Mean Recall@5: {metrics['mean_recall@k']:.1%}")
    print(f"Batch of 3 queries - MAP@5: {metrics['map@k']:.1%}")

if __name__ == "__main__":
    test_metrics()